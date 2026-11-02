# RJDAP Mini-RFC

## 1. Introduction

### 1.1 Protocol Overview

RJDAP (Reliable Job Dispatch & Aggregation Protocol) is a custom application-layer protocol designed to distribute computational tasks from a central server to multiple workers using UDP sockets.

The server registers workers, assigns tasks, and collects their results. Each worker joins the system, receives a task, performs the required computation, and sends the result back to the server.

### 1.2 Purpose and Motivation

UDP provides lightweight communication but does not guarantee packet delivery, ordering, or duplicate prevention.

RJDAP aims to address these limitations through application-layer mechanisms such as acknowledgments, task tracking, timeout-based reassignment, and duplicate result suppression.

The main purpose of the protocol is to support reliable task distribution while keeping communication efficient.

### 1.3 Use Case

A central server distributes independent computational tasks among four workers.

For example, the server sends an addition task containing two numbers to a worker. The worker calculates their sum and returns the result using a `TASK_RESULT` message.

The server then collects the results from all workers.

### 1.4 Assumptions and Constraints

- The protocol uses UDP for communication.
- The system supports at least four workers.
- Tasks are independent and can be executed separately.
- Messages use a custom binary header containing Version, Message Type, Task ID, Worker ID, Attempt Number, and Payload Checksum.
- The current protocol version is 1.
- Task packets must comply with the project's 512-byte application payload limit.
- Advanced reliability mechanisms will be developed and tested in Phase 2.

## 2. Protocol Architecture

### 2.1 Entities

**Server (Command Hub).** A single UDP socket bound to `127.0.0.1:5000`. It registers exactly four workers, owns a queue of 1,000 tasks, dispatches tasks, acknowledges results, and logs every sent and received packet with a timestamp to the console and to `server.log`.

**Worker (compute node).** Four worker processes. Each worker is started with its own Worker ID (1 to 4), joins the server, executes the assigned computation (adding two integers), and returns the result.

### 2.2 Task and Result Encoding (Phase 1)

- `TASK_DISPATCH` payload: ASCII text `"a:b"` (two integers separated by a colon).
- `TASK_RESULT` payload: ASCII text containing the sum `a + b`.
- Task N asks the worker to add N and 2N, so every run is identical and reproducible.

### 2.3 Sequence Flow

```
Worker                                      Server (127.0.0.1:5000)
  |                                               |
  |------ WORKER_JOIN (Worker_ID) --------------->| Register worker (no reply)
  |        ... all 4 workers join ...             |
  |<----- TASK_DISPATCH (Task_ID, "a:b") ---------| Sent once 4 workers are registered
  | [compute a + b]                               |
  |------ TASK_RESULT (sum) --------------------->| Validate and store result
  |<----- ACK_RESULT -----------------------------|
  |<----- TASK_DISPATCH (next task) --------------| Repeat until all 1,000 are done
  |<----- STOP -----------------------------------| All results received; worker exits
```

The server does not start dispatching until all four workers have joined. After that, it sends one task at a time to each worker and sends the next task only after it has received and acknowledged the previous result, so faster workers handle more tasks.

`HEARTBEAT` is defined in the protocol but is not used in Phase 1; it will be used for crash detection in Phase 2. `STOP` is a temporary raw message and will be replaced by a protocol message in Phase 2.

### 2.4 Server Finite-State Machine

| State | Event | Action | Next State |
|---|---|---|---|
| `WAITING_FOR_WORKERS` | `WORKER_JOIN` (valid, new ID) | Register worker | `WAITING_FOR_WORKERS` |
| `WAITING_FOR_WORKERS` | `WORKER_JOIN` (4th worker) | Register worker, dispatch one task to each worker, start timer | `RUNNING` |
| `WAITING_FOR_WORKERS` / `RUNNING` | `WORKER_JOIN` (invalid ID, duplicate ID, or already 4 workers) | Log and reject | Unchanged |
| `RUNNING` | `TASK_RESULT` (valid, new task) | Store result, send `ACK_RESULT`, dispatch next task to that worker | `RUNNING` |
| `RUNNING` | `TASK_RESULT` (task already stored) | Log as duplicate, re-send `ACK_RESULT` | `RUNNING` |
| `RUNNING` | `TASK_RESULT` (unknown worker or invalid payload) | Log and drop | `RUNNING` |
| Any | Malformed packet (bad checksum, size, version, or message type) | Log and drop | Unchanged |
| `RUNNING` | All 1,000 results stored | Log total time, send `STOP` to workers | `STOPPED` |
| Any | No packet received for 30 s | Log timeout, send `STOP` to workers | `STOPPED` |

### 2.5 Worker Finite-State Machine

`JOINING` (send `WORKER_JOIN`) → `WAITING` (for a task) → `COMPUTING` → `WAITING` (after sending `TASK_RESULT`) → `STOPPED` (when `STOP` is received).

A worker ignores any task whose Worker ID is not its own.

### 2.6 Server State

The server keeps a worker registry (Worker ID to address), a map of received results keyed by Task ID, and a counter for the next task in the queue. Every packet is logged with a millisecond timestamp.

### 2.7 Phase 1 Assumptions and Phase 2 Extensions

Loopback is assumed lossless in Phase 1, so no retransmission timers are used yet, and the server waits for all four workers before starting.

The result map and duplicate-result check are the foundation for Phase 2: timeout-based task reassignment, worker crash detection, starting without every worker, and exactly-once result handling.

## 3. Binary Header Format

The RJDAP header uses the Python `struct` format `!BBIHHI`.

The `!` specifies network byte order (big-endian), with standard field sizes and no padding. The Version field identifies the protocol version; the current supported version is `1`.

| Field | Format | Size | Start Offset | End Offset | Description |
|---|---|---:|---:|---:|---|
| Version | `B` | 1 byte | 0 | 0 | Identifies the protocol version |
| Message Type | `B` | 1 byte | 1 | 1 | Identifies the message |
| Task ID | `I` | 4 bytes | 2 | 5 | Identifies the task |
| Worker ID | `H` | 2 bytes | 6 | 7 | Identifies the worker |
| Attempt Number | `H` | 2 bytes | 8 | 9 | Identifies the task attempt |
| Payload Checksum | `I` | 4 bytes | 10 | 13 | CRC-32 checksum of the payload |
| **Total** | | **14 bytes** | **0** | **13** | |

The sender sets Version to `1`. The receiver rejects messages containing unsupported versions.

The payload immediately follows the header, beginning at byte offset 14.

### 3.1 Message Types

| Message Type | Value | Description |
|---|---|---|
| `WORKER_JOIN` | 1 | Worker registers with the server |
| `HEARTBEAT` | 2 | Reserved for Phase 2 worker monitoring |
| `TASK_DISPATCH` | 3 | Server sends a task to a worker |
| `TASK_RESULT` | 4 | Worker sends the computed result |
| `ACK_RESULT` | 5 | Server acknowledges the result |

### 3.2 Sample Message

Example of a `TASK_DISPATCH` message sent to Worker 1:

| Field | Value |
|---|---|
| Version | 1 |
| Message Type | 3 (`TASK_DISPATCH`) |
| Task ID | 1 |
| Worker ID | 1 |
| Attempt Number | 1 |
| Payload | `b"1:2"` |
| Payload Checksum | CRC-32 of `b"1:2"` |

Encoding example:

```python
message = encode_message(
    MessageType.TASK_DISPATCH, 1, 1, 1, b"1:2"
)
```

The message contains a 14-byte binary header followed by the 3-byte payload, giving a total size of 17 bytes.

## 4. Payload and Checksum

The payload contains the message's application data and follows the header.

The maximum payload size is 512 bytes in the current prototype.

The sender calculates a CRC-32 checksum over the payload and places the checksum in the header. The receiver recalculates the checksum and compares it with the received value. If the values differ, the message is rejected.

The checksum detects accidental payload corruption but does not guarantee packet delivery or authenticate the sender.

## 5. Encoding and Decoding

The sender serializes the header fields using Python's `struct.pack()`.

The receiver extracts the header and payload, then uses `struct.unpack()` to decode the header fields.

The receiver validates the header size, protocol version, message type, payload size, and checksum before accepting the message.

## 6. Implementation Status

This document describes the current prototype. The header layout, field sizes, checksum algorithm, and message formats have been implemented and integrated with the server and workers. The Phase 1 baseline test successfully completed 1,000 tasks in each of five runs.

The current protocol implementation uses `!BBIHHI`, giving a 14-byte header that includes the required Version field. Phase 2 reliability mechanisms remain subject to implementation and testing.
