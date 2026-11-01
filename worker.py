
import socket
import sys
from datetime import datetime
from protocol import MessageType, encode_message, decode_message

SERVER_IP = "127.0.0.1"
SERVER_PORT = 5000

if len(sys.argv) != 2:
    print("Usage: py worker.py <worker_id>")
    sys.exit()

try:
    WORKER_ID = int(sys.argv[1])
    if WORKER_ID <= 0 or WORKER_ID > 65535:
        raise ValueError
except ValueError:
    print("Worker ID must be between 1 and 65535")
    sys.exit()

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] [Worker {WORKER_ID}] {message}")


worker_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

log("Worker is ready!")

try:
    join_message = encode_message(
        MessageType.WORKER_JOIN,
        0,
        WORKER_ID,
        0,
        b""
    )

    worker_socket.sendto(join_message, (SERVER_IP, SERVER_PORT))
    log("WORKER_JOIN sent to server")

    while True:
        data, server_address = worker_socket.recvfrom(2048)

        if data == b"STOP":
            log("Worker stopped")
            break

        try:
            message_type, task_id, worker_id, attempt_num, payload = decode_message(data)
        except ValueError as e:
            log(f"Invalid message: {e}")
            continue

    
        if message_type == MessageType.TASK_DISPATCH:

            if worker_id != WORKER_ID:
                log("Task belongs to another worker")
                continue

            try:
                numbers = payload.decode().split(":")

                if len(numbers) != 2:
                    raise ValueError

                num1 = int(numbers[0])
                num2 = int(numbers[1])

                result = num1 + num2

                log(f"Task {task_id}: {num1} + {num2} = {result}")

                result_message = encode_message(
                    MessageType.TASK_RESULT,
                    task_id,
                    WORKER_ID,
                    attempt_num,
                    str(result).encode()
                )

                worker_socket.sendto(result_message, server_address)

                log(f"Sent TASK_RESULT for Task {task_id}: {result}")

            except (ValueError, UnicodeDecodeError):
                log("Invalid task payload")
        elif message_type == MessageType.ACK_RESULT:
            log(f"ACK_RESULT received for Task {task_id}")

        else:
            log(f"Unexpected message type: {message_type.name}")

except KeyboardInterrupt:
    log("Worker interrupted")

finally:
    worker_socket.close()
    log("Worker socket closed")
