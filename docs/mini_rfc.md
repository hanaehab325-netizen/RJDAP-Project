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

For example, the server sends an addition task containing two numbers to a worker. The worker calculates their sum and returns the result using a TASK_RESULT message.

The server then collects the results from all workers.

### 1.4 Assumptions and Constraints

- The protocol uses UDP for communication.
- The system supports at least four workers.
- Tasks are independent and can be executed separately.
- Messages use a custom binary header containing Message Type, Task ID, Worker ID, Attempt Number, and Payload Checksum.
- Task packets must comply with the project's 512-byte application payload limit.
- Advanced reliability mechanisms will be developed and tested in Phase 2.
## 2. Protocol Architecture

### 2.1 Entities

**Server (Command Hub).** A single UDP socket bound to 127.0.0.1:5000. It registers
workers, owns a queue of 1,000 tasks, dispatches tasks, validates and acknowledges
results, and logs every sent and received packet with a timestamp.

**Worker (compute node).** At least four worker processes. Each worker is started
with its own Worker ID, joins the server, executes the assigned computation (adding
two integers), and returns the result.

### 2.2 Task and Result Encoding (Phase 1)

- TASK_DISPATCH payload: ASCII text "a:b" (two integers separated by a colon).
- TASK_RESULT payload: ASCII text containing the sum a + b.
- Tasks are generated from a fixed random seed, so every run is reproducible.

### 2.3 Sequence Flow

    Worker                                   Server (127.0.0.1:5000)
      |------- WORKER_JOIN (Worker_ID) ------->|  register worker
      |<------ TASK_DISPATCH (Task_ID, "a:b") -|
      |   [compute a + b]                      |
      |------- TASK_RESULT (sum) ------------->|  validate and store result
      |<------ ACK_RESULT ---------------------|
      |<------ TASK_DISPATCH (next task) ------|  repeat until all 1,000 are done
      |<------ STOP ---------------------------|  all results received, worker exits

The server sends one task at a time to each worker and sends the next task only after
it has received and acknowledged the previous result. HEARTBEAT is defined in the
protocol but is not used in Phase 1; it will be used for crash detection in Phase 2.
STOP is a temporary raw message and will be replaced by a protocol message in Phase 2.

### 2.4 Server Finite-State Machine

| State | Event | Action | Next state |
|---|---|---|---|
| LISTENING | WORKER_JOIN (new valid ID) | Register worker, dispatch first task | LISTENING |
| LISTENING | WORKER_JOIN (ID already registered) | Log and ignore | LISTENING |
| LISTENING | TASK_RESULT (valid) | Store result, check it, send ACK_RESULT, dispatch next task | LISTENING |
| LISTENING | TASK_RESULT (task already stored) | Log as duplicate, re-send ACK_RESULT | LISTENING |
| LISTENING | TASK_RESULT (wrong worker, wrong address or invalid payload) | Log and drop | LISTENING |
| LISTENING | Malformed packet (bad checksum, size or type) | Log and drop | LISTENING |
| LISTENING | All 1,000 results stored, or 30 s idle timeout | Log summary, send STOP to workers | STOPPED |

### 2.5 Worker Finite-State Machine

JOINING (WORKER_JOIN sent) -> WAITING (for a task) -> COMPUTING -> WAITING (after
TASK_RESULT is sent) -> STOPPED (when STOP is received).

### 2.6 Server State

The server keeps a worker registry (Worker ID to address), a map of which task was
assigned to which worker, a map of received results, and a counter for the next task
in the queue. Every packet is logged to logs/server.log.

### 2.7 Phase 1 Assumptions and Phase 2 Extensions

Loopback is assumed lossless in Phase 1, so no retransmission timers are used yet.
The assignment map and the duplicate-result check are the foundation for Phase 2:
timeout-based task reassignment, worker crash detection and exactly-once result
handling.
## 2. Message Types

| Message Type | Value | Purpose |
|---|---|---|
| WORKER_JOIN | 1 | Worker announces that it has joined |
| HEARTBEAT | 2 | Worker indicates that it is still active |
| TASK_DISPATCH | 3 | Server sends a task to a worker |
| TASK_RESULT | 4 | Worker returns a task result |
| ACK_RESULT | 5 | Server acknowledges a task result |

## 3. Binary Header Format

The current proposed header uses the Python `struct` format `!BIHHI`.

The `!` specifies network byte order (big-endian).

| Field | Format | Size | Description |
|---|---|---|---|
| Message Type | B | 1 byte | Identifies the message |
| Task ID | I | 4 bytes | Identifies the task |
| Worker ID | H | 2 bytes | Identifies the worker |
| Attempt Number | H | 2 bytes | Identifies the task attempt |
| Payload Checksum | I | 4 bytes | CRC-32 checksum of the payload |
| **Total** | | **13 bytes** | |

## 4. Payload and Checksum

The payload contains the message's application data and follows the header.

The maximum payload size is 512 bytes in the current prototype.

The sender calculates a CRC-32 checksum over the payload and places the checksum in the header. The receiver recalculates the checksum and compares it with the received value. If the values differ, the message is rejected.

## 5. Encoding and Decoding

The sender serializes the header fields using Python's `struct.pack()`.

The receiver extracts the header and payload, then uses `struct.unpack()` to decode the header fields.

The receiver validates the header size, message type, payload size, and checksum before accepting the message.

## 6. Implementation Status

This document describes the current prototype. The header layout, field sizes, checksum algorithm, and message definitions must be confirmed with the project team before final integration.
