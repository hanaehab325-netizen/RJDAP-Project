import socket
from datetime import datetime
from protocol import MessageType, encode_message, decode_message

IP, PORT = "127.0.0.1", 5000
TOTAL_TASKS = 1000
TOTAL_WORKERS = 4

logfile = open("server.log", "w")


def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    line = f"[{timestamp}] [Server] {message}"
    print(line)
    logfile.write(line + "\n")
    logfile.flush()


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((IP, PORT))
sock.settimeout(30)

workers = {}      
results = {}     
next_task = 1


def send(message_type, task_id, worker_id, payload=b""):
    message = encode_message(message_type, task_id, worker_id, 1, payload)
    sock.sendto(message, workers[worker_id])
    log(f"SEND {message_type.name} task={task_id} worker={worker_id}")


def give_task(worker_id):
    global next_task
    if next_task <= TOTAL_TASKS:
        payload = f"{next_task}:{next_task * 2}".encode()   
        send(MessageType.TASK_DISPATCH, next_task, worker_id, payload)
        next_task += 1


log(f"Server started, waiting for {TOTAL_WORKERS} workers...")
start_time = datetime.now()

try:
    while len(results) < TOTAL_TASKS:
        try:
            data, address = sock.recvfrom(2048)
        except ConnectionResetError:     
            continue

        try:
            message_type, task_id, worker_id, attempt_num, payload = decode_message(data)
        except ValueError as e:
            log(f"Invalid message: {e}")
            continue

        log(f"RECV {message_type.name} task={task_id} worker={worker_id}")

        if message_type == MessageType.WORKER_JOIN:
            if worker_id <= 0 or worker_id in workers or len(workers) >= TOTAL_WORKERS:
                log("Join rejected (invalid ID, duplicate, or server full)")
                continue

            workers[worker_id] = address
            log(f"Worker {worker_id} registered: {address}")

            if len(workers) == TOTAL_WORKERS:          
                log("All workers registered, starting tasks")
                start_time = datetime.now()
                for wid in workers:
                    give_task(wid)

        elif message_type == MessageType.TASK_RESULT:
            if worker_id not in workers:
                log("Result from unknown worker")
                continue

            if task_id not in results:
                try:
                    results[task_id] = int(payload.decode())
                except (ValueError, UnicodeDecodeError):
                    log("Invalid result payload")
                    continue
                log(f"Task {task_id} done ({len(results)}/{TOTAL_TASKS})")
                send(MessageType.ACK_RESULT, task_id, worker_id)
                give_task(worker_id)
            else:
                log(f"Duplicate result for Task {task_id}")
                send(MessageType.ACK_RESULT, task_id, worker_id)

    seconds = (datetime.now() - start_time).total_seconds()
    log(f"All {TOTAL_TASKS} tasks completed in {seconds:.2f}s")

except socket.timeout:
    log("Timeout: no packets received")

except KeyboardInterrupt:
    log("Server interrupted")

finally:
    for address in workers.values():
        sock.sendto(b"STOP", address)         
    sock.close()
    log("Server stopped")
