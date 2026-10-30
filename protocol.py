from enum import IntEnum
import struct 
import zlib

class MessageType(IntEnum):
    WORKER_JOIN = 1
    HEARTBEAT = 2
    TASK_DISPATCH =3
    TASK_RESULT = 4
    ACK_RESULT = 5

HEADER_FORMAT = "!BIHHI"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
MAX_PAYLOAD_SIZE = 512 


def calculate_checksum(payload) :

    return zlib.crc32(payload) & 0xFFFFFFFF


def encode_header (message_type, task_id,worker_id,attempt_num,checksum):

    data = struct.pack(HEADER_FORMAT, message_type,task_id,worker_id,attempt_num, checksum)
    return data

def decode_header (data):
    if len(data) != HEADER_SIZE :
        raise ValueError("Invalid header size")
    message_type, task_id, worker_id, attempt_num, checksum = struct.unpack(HEADER_FORMAT, data)
    try:
        message_type = MessageType(message_type)
    except:
        raise ValueError("Invalid message type")
    return message_type,task_id,worker_id,attempt_num, checksum

def encode_message(message_type, task_id, worker_id, attempt_num, payload):
    if len(payload) > MAX_PAYLOAD_SIZE :
        raise ValueError ("Payload exceeds 512 bytes")
    checksum = calculate_checksum(payload)
    header = encode_header(message_type,task_id,worker_id,attempt_num,checksum)
    message = header + payload;
    return message;

def decode_message(data):
    if len(data) < HEADER_SIZE:
        raise ValueError("Message is shorter than header")
    header = data[:HEADER_SIZE]
    payload = data [HEADER_SIZE:]
    if len (payload) > MAX_PAYLOAD_SIZE :
        raise ValueError("Payload exceeds 512 bytes")
    message_type, task_id, worker_id, attempt_num, received_checksum =decode_header(header)
    calculated_checksum = calculate_checksum(payload)
    if (received_checksum != calculated_checksum):
        raise ValueError (" Payload checksum mismatch")
    return message_type, task_id, worker_id,attempt_num, payload

