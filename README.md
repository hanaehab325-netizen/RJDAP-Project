# RJDAP-Project
Networks Project
# RJDAP — Reliable Job Dispatch & Aggregation Protocol

## Project Overview

RJDAP is a reliable job dispatch and aggregation protocol designed to distribute tasks from a server to multiple workers using UDP communication. The project aims to handle task dispatching, result collection, worker monitoring, and task reassignment.

## Technologies Used

- Python 3
- UDP sockets
- Binary message encoding and decoding
- CRC-32 checksums
- Python `unittest` framework

## Project Structure

```text
RJDAP-Project/
├── server.py
├── worker.py
├── protocol.py
├── run_baseline.py
├── tests/
│   └── test_protocol.py
├── docs/
│   └── mini_rfc.md
├── logs/
├── README.md
└── .gitignore
```

## Protocol Implementation

The `protocol.py` module defines the message types and provides functions for encoding and decoding RJDAP messages.

### Supported Message Types

| Message Type | Value | Description |
|---|---:|---|
| `WORKER_JOIN` | 1 | Indicates that a worker has joined the system. |
| `HEARTBEAT` | 2 | Indicates that a worker is still active. |
| `TASK_DISPATCH` | 3 | Sends a task from the server to a worker. |
| `TASK_RESULT` | 4 | Sends a task result from a worker to the server. |
| `ACK_RESULT` | 5 | Acknowledges the receipt of a task result. |

### Binary Message Header

The current proposed header format is `!BIHHI`, with a total size of 13 bytes.

| Field | Size |
|---|---:|
| Message Type | 1 byte |
| Task ID | 4 bytes |
| Worker ID | 2 bytes |
| Attempt Number | 2 bytes |
| Payload Checksum | 4 bytes |

The `!` prefix specifies network byte order (big-endian).

### Payload and Checksum

- The maximum application payload size is 512 bytes.
- A CRC-32 checksum is calculated over the payload.
- The receiver verifies the checksum when decoding a message.
- Messages with invalid headers, unsupported message types, oversized payloads, or checksum mismatches are rejected.

### Main Functions

- `encode_message(message_type, task_id, worker_id, attempt_num, payload)`: Encodes the header and payload into a binary message.
- `decode_message(data)`: Validates and decodes a binary message, returning the message type, task ID, worker ID, attempt number, and payload.

**Note:** The header format and payload conventions should be confirmed with the team before integration with the server and worker modules.

## Testing

The protocol module is tested using Python's built-in `unittest` framework.

Run the tests from the project root:

```bash
python -m unittest discover -s tests -v
```

The current protocol test suite contains seven tests covering message encoding and decoding, header size, maximum payload size, oversized payload rejection, corrupted payload detection, short messages, and invalid message types.

## Project Status

- Protocol message types and binary encoding/decoding implemented.
- Payload checksum validation implemented.
- Maximum payload size enforced.
- Seven protocol unit tests passing.
- Server and worker integration, baseline performance evaluation, and reliability testing are tracked separately.