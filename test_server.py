
import socket
from datetime import datetime
from protocol import MessageType, encode_message, decode_message

SERVER_IP = "127.0.0.1"
SERVER_PORT = 5000
NUM_WORKERS = 4


def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] [Server] {message}")


server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((SERVER_IP, SERVER_PORT))
server_socket.settimeout(30)

workers = {}

log("Server started")
log("Waiting for 4 workers...")

try:
    # Register workers
    while len(workers) < NUM_WORKERS:
        data, address = server_socket.recvfrom(2048)

        try:
            message_type, task_id, worker_id, attempt_num, payload = decode_message(data)
        except ValueError as e:
            log(f"Invalid message: {e}")
            continue

        if message_type == MessageType.WORKER_JOIN:
            if worker_id <= 0:
                log("Invalid worker ID")
                continue

            workers[worker_id] = address
            log(f"Worker {worker_id} registered: {address}")

    log("All 4 workers registered!")

    tasks = [
        (101, 5, 3),
        (102, 10, 20),
        (103, 7, 4),
        (104, 15, 5)
    ]

    worker_ids = sorted(workers.keys())

    # Dispatch tasks
    for i in range(NUM_WORKERS):
        worker_id = worker_ids[i]
        task_id, num1, num2 = tasks[i]

        payload = f"{num1}:{num2}".encode()

        task_message = encode_message(
            MessageType.TASK_DISPATCH,
            task_id,
            worker_id,
            1,
            payload
        )

        server_socket.sendto(task_message, workers[worker_id])
        log(f"Sent Task {task_id} to Worker {worker_id}")

    # Receive results
    received_results = {}
    expected_tasks = {
        task_id: worker_ids[i]
        for i, (task_id, _, _) in enumerate(tasks)
    }

    while len(received_results) < NUM_WORKERS:
        data, address = server_socket.recvfrom(2048)

        try:
            message_type, task_id, worker_id, attempt_num, payload = decode_message(data)
        except ValueError as e:
            log(f"Invalid message: {e}")
            continue

        if message_type == MessageType.TASK_RESULT:
            if task_id not in expected_tasks:
                log(f"Unknown Task ID: {task_id}")
                continue

            if expected_tasks[task_id] != worker_id:
                log(f"Unexpected Worker ID for Task {task_id}")
                continue

            if workers.get(worker_id) != address:
                log(f"Unexpected address for Worker {worker_id}")
                continue

            if task_id in received_results:
                log(f"Duplicate result for Task {task_id}")
                continue

            try:
                result = int(payload.decode())
            except (ValueError, UnicodeDecodeError):
                log("Invalid result payload")
                continue

            received_results[task_id] = result
            log(f"Received Task {task_id} result: {result}")

    log("All task results received!")

except socket.timeout:
    log("Timeout: Not all workers or results arrived")

except KeyboardInterrupt:
    log("Server interrupted")

finally:
    # Temporary STOP message
    for worker_id, address in workers.items():
        server_socket.sendto(b"STOP", address)

    server_socket.close()
    log("Server stopped")
