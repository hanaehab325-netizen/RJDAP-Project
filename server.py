import socket
from datetime import datetime
from protocol import MessageType, encode_message, decode_message

SERVER_IP = "127.0.0.1"
SERVER_PORT = 5000
TOTAL_TASKS = 1000

logfile = open("server.log", "w")


def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    line = f"[{timestamp}] [Server] {message}"
    print(line)
    logfile.write(line + "\n")
    logfile.flush()


server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((SERVER_IP, SERVER_PORT))
server_socket.settimeout(30)

workers = {}           
results = {}           
next_task = 1


def send(message_type, task_id, worker_id, payload=b""):
    message = encode_message(message_type, task_id, worker_id, 1, payload)
    server_socket.sendto(message, workers[worker_id])
    log(f"SEND {message_type.name} task={task_id} worker={worker_id}")


def give_task(worker_id):
    global next_task
    if next_task <= TOTAL_TASKS:
        
        payload = f"{next_task}:{next_task * 2}".encode()
        send(MessageType.TASK_DISPATCH, next_task, worker_id, payload)
        next_task += 1


log("Server started")
start_time = datetime.now()

try:
    while len(results) < TOTAL_TASKS:
        try:
            data, address = server_socket.recvfrom(2048)
        except ConnectionResetError:     
            continue

        try:
            message_type, task_id, worker_id, attempt_num, payload = decode_message(data)
        except ValueError as e:
            log(f"Invalid message: {e}")
            continue

        log(f"RECV {message_type.name} task={task_id} worker={worker_id}")

        if message_type == MessageType.WORKER_JOIN:
            if worker_id <= 0 or worker_id in workers:
                log("Invalid or duplicate worker ID")
                continue
            workers[worker_id] = address
            log(f"Worker {worker_id} registered: {address}")
            give_task(worker_id)

        elif message_type == MessageType.TASK_RESULT:
            if worker_id not in workers:
                log("Result from unknown worker")
                continue

            if task_id in results:
                log(f"Duplicate result for Task {task_id}")
                send(MessageType.ACK_RESULT, task_id, worker_id)
                continue

            try:
                results[task_id] = int(payload.decode())
            except (ValueError, UnicodeDecodeError):
                log("Invalid result payload")
                continue

            log(f"Received Task {task_id} result: {results[task_id]} ({len(results)}/{TOTAL_TASKS})")
            send(MessageType.ACK_RESULT, task_id, worker_id)
            give_task(worker_id)

    seconds = (datetime.now() - start_time).total_seconds()
    log(f"All {TOTAL_TASKS} tasks completed in {seconds:.2f}s")

except socket.timeout:
    log("Timeout: no packets received")

except KeyboardInterrupt:
    log("Server interrupted")

finally:
    
    for worker_id, address in workers.items():
        server_socket.sendto(b"STOP", address)

    server_socket.close()
    log("Server stopped")
