# RJDAP Mini-RFC

## 1. Protocol Overview

RJDAP (Reliable Job Dispatch & Aggregation Protocol) is an application-layer protocol designed to dispatch tasks from a server to workers over UDP and receive their results.

The protocol defines message types, a binary message header, and a payload checksum for detecting accidental data corruption.

## 2. Message Types

| Message Type | Value | Purpose |
|---|---:|---|
| WORKER_JOIN | 1 | Worker announces that it has joined |
| HEARTBEAT | 2 | Worker indicates that it is still active |
| TASK_DISPATCH | 3 | Server sends a task to a worker |
| TASK_RESULT | 4 | Worker returns a task result |
| ACK_RESULT | 5 | Server acknowledges a task result |

## 3. Binary Header Format

The current proposed header uses the Python `struct` format `!BIHHI`.

The `!` specifies network byte order (big-endian).

| Field | Format | Size | Description |
|---|---|---:|---|
| Message Type | B | 1 byte | Identifies the message |
| Task ID | I | 4 bytes | Identifies the task |
| Worker ID | H | 2 bytes | Identifies the worker |
| Attempt Number | H | 2 bytes | Identifies the task attempt |
| Payload Checksum | I | 4 bytes | CRC-32 checksum of the payload |
| **Total** | | **13 bytes** | |

## 4. Payload and Checksum

The payload contains the message's application data and follows the header.

The maximum payload size is 512 bytes.

The sender calculates a CRC-32 checksum over the payload and places the checksum in the header. The receiver recalculates the checksum and compares it with the received value. If the values differ, the message is rejected.

## 5. Encoding and Decoding

The sender serializes the header fields using Python's `struct.pack()`.

The receiver extracts the header and payload, then uses `struct.unpack()` to decode the header fields.

The receiver validates the header size, message type, payload size, and checksum before accepting the message.

## 6. Implementation Status

This document describes the current prototype. The header layout, field sizes, checksum algorithm, and message definitions must be confirmed with the project team before final integration.