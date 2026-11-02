# RJDAP — Reliable Job Dispatch & Aggregation Protocol

Computer Networks Project – Phase 1

## Project Overview

RJDAP is a custom application-layer protocol designed to distribute computational tasks from a central server to multiple workers using UDP communication.

In Phase 1, the server registers four workers, distributes 1,000 addition tasks, collects results, and sends acknowledgments.

Advanced reliability features, including worker crash recovery and timeout-based task reassignment, will be implemented in Phase 2.

## Technologies Used

- Python 3
- UDP sockets
- Binary message encoding and decoding
- CRC-32 checksums
- Python `unittest` framework
- VS Code

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
├── server.log
├── README.md
└── .gitignore
```

## Protocol Implementation

The `protocol.py` module defines the message types and provides functions for encoding and decoding RJDAP messages.

### Supported Message Types

| Message Type | Value | Description |
|---|---|---|
| `WORKER_JOIN` | 1 | Registers a worker with the server |
| `HEARTBEAT` | 2 | Reserved for worker monitoring in Phase 2 |
| `TASK_DISPATCH` | 3 | Sends a task to a worker |
| `TASK_RESULT` | 4 | Sends the computed result to the server |
| `ACK_RESULT` | 5 | Acknowledges receipt of a result |

### Binary Message Header

The protocol uses the header format `!BBIHHI`, with a total size of 14 bytes.

| Field | Size |
|---|---|
| Version | 1 byte |
| Message Type | 1 byte |
| Task ID | 4 bytes |
| Worker ID | 2 bytes |
| Attempt Number | 2 bytes |
| Payload Checksum | 4 bytes |
| **Total** | **14 bytes** |

The `!` prefix specifies network byte order (big-endian). The current protocol version is 1.

### Payload and Checksum

- The maximum application payload size is 512 bytes.
- A CRC-32 checksum is calculated over the payload.
- The receiver verifies the checksum when decoding messages.
- Invalid message types, unsupported versions, oversized payloads, and checksum mismatches are rejected.

### Main Functions

- `encode_message(message_type, task_id, worker_id, attempt_num, payload)` — Creates a binary message.
- `decode_message(data)` — Validates and decodes a received message.

## Server and Worker Implementation

### Server (`server.py`)

The server uses UDP socket `127.0.0.1:5000`.

It registers four workers, distributes 1,000 tasks, receives results, sends acknowledgments, and records communication logs with timestamps.

### Worker (`worker.py`)

Each worker registers with the server using a unique Worker ID from 1 to 4.

The worker receives two numbers, calculates their sum, and returns the result.

For example:

- Task ID: `1`
- Payload: `"1:2"`
- Result: `3`

## How to Run the Project

### Requirements

- Python 3 installed.
- VS Code or another code editor.
- All project files in the correct folders.

No external Python packages are required for the Phase 1 prototype.

### Manual Execution

Open five terminals in the project folder.

Start the server in the first terminal:

```bash
python server.py
```

Start the four workers in separate terminals:

```bash
python worker.py 1
```

```bash
python worker.py 2
```

```bash
python worker.py 3
```

```bash
python worker.py 4
```

The server starts dispatching tasks after all four workers have registered.

### Automated Baseline Test

The `run_baseline.py` script automatically starts the server and four workers.

To run the test:

```bash
python run_baseline.py
```

The script performs five baseline runs and checks:

- Registration of four workers.
- Completion of all 1,000 tasks.
- Correct calculation results.
- Task IDs and duplicate task detection.
- Result acknowledgments.

The script saves server and worker logs for each run in the `logs/` folder.

It also creates `logs/baseline_results.csv` containing the status and completion time of each run.

## Testing

### Protocol Unit Tests

The protocol module is tested using Python's built-in `unittest` framework.

Run:

```bash
python -m unittest discover -s tests -v
```

The test suite contains nine tests covering:

- Message encoding and decoding.
- Header size.
- Protocol version.
- Unsupported protocol version rejection.
- Maximum payload size.
- Oversized payload rejection.
- Corrupted payload detection.
- Short message rejection.
- Invalid message type rejection.

### Protocol Unit Test Results

The protocol unit tests were executed to verify message encoding, decoding, and validation.

| Test | Status |
|---|---|
| `test_corrupted_payload` | PASS |
| `test_header_size` | PASS |
| `test_invalid_message_type` | PASS |
| `test_maximum_payload_allowed` | PASS |
| `test_message_round_trip` | PASS |
| `test_message_shorter_than_header` | PASS |
| `test_payload_too_large` | PASS |
| `test_protocol_version` | PASS |
| `test_unsupported_protocol_version` | PASS |

All nine protocol unit tests passed successfully.

### Automated Baseline Test

The `run_baseline.py` script automatically starts the server and four workers.

To run the test:

```bash
python run_baseline.py
```

The script performs five baseline runs and checks:

- Registration of four workers.
- Completion of all 1,000 tasks.
- Correct calculation results.
- Task IDs and duplicate task detection.
- Result acknowledgments.

The script saves server and worker logs for each run in the `logs/` folder.

It also creates `logs/baseline_results.csv` containing the status and completion time of each run.

### Baseline Test Results

The automated baseline test was executed five times on localhost.

| Run | Completed Tasks | Status |
|---|---|---|
| 1 | 1,000/1,000 | PASS |
| 2 | 1,000/1,000 | PASS |
| 3 | 1,000/1,000 | PASS |
| 4 | 1,000/1,000 | PASS |
| 5 | 1,000/1,000 | PASS |

All five runs passed the baseline validation checks.

The individual completion times are recorded in `logs/baseline_results.csv`.

## Logging

The server and workers log communication events with timestamps.

The automated baseline script stores separate log files for each run, including:

- `server_1.log` through `server_5.log`
- `w1_1.log` through `w4_5.log`

The `server.log` file is also generated by the server during execution.

## Documentation

The Mini-RFC is available at:

`docs/mini_rfc.md`
Just right click the file and click "Open Preview"to view it.

It describes the protocol introduction, architecture, communication flow, finite-state machines, and message formats.

## Phase 1 Demo Video

Demo video link: **[Add video link here]**

## GitHub Link that has all the files except for the logs/

https://github.com/hanaehab325-netizen/RJDAP-Project
