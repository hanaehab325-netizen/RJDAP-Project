import unittest
import struct

from protocol import (
    MessageType,
    PROTOCOL_VERSION,
    HEADER_FORMAT,
    HEADER_SIZE,
    MAX_PAYLOAD_SIZE,
    encode_message,
    decode_message,
)


class TestProtocol(unittest.TestCase):

    def test_message_round_trip(self):
        payload = b"Calculate 10 + 20"

        message = encode_message(
            MessageType.TASK_DISPATCH, 100, 5, 1, payload
        )

        message_type, task_id, worker_id, attempt_num, received_payload = (
            decode_message(message)
        )

        self.assertEqual(message_type, MessageType.TASK_DISPATCH)
        self.assertEqual(task_id, 100)
        self.assertEqual(worker_id, 5)
        self.assertEqual(attempt_num, 1)
        self.assertEqual(received_payload, payload)

    def test_header_size(self):
        self.assertEqual(HEADER_SIZE, 14)

    def test_protocol_version(self):
        message = encode_message(
            MessageType.TASK_DISPATCH, 1, 1, 1, b"test"
        )

        version = struct.unpack(HEADER_FORMAT, message[:HEADER_SIZE])[0]

        self.assertEqual(version, PROTOCOL_VERSION)

    def test_unsupported_protocol_version(self):
        invalid_header = struct.pack(
            HEADER_FORMAT,
            99,  # Unsupported version
            int(MessageType.TASK_DISPATCH),
            1,
            1,
            1,
            0,  # Checksum; version validation happens first
        )

        with self.assertRaisesRegex(ValueError, "version"):
            decode_message(invalid_header)

    def test_maximum_payload_allowed(self):
        payload = b"A" * MAX_PAYLOAD_SIZE

        message = encode_message(
            MessageType.TASK_DISPATCH, 1, 1, 1, payload
        )

        _, _, _, _, received_payload = decode_message(message)

        self.assertEqual(received_payload, payload)

    def test_payload_too_large(self):
        payload = b"A" * (MAX_PAYLOAD_SIZE + 1)

        with self.assertRaisesRegex(ValueError, "512"):
            encode_message(
                MessageType.TASK_DISPATCH, 1, 1, 1, payload
            )

    def test_corrupted_payload(self):
        message = encode_message(
            MessageType.TASK_DISPATCH, 100, 5, 1, b"Original payload"
        )

        corrupted = bytearray(message)
        corrupted[-1] ^= 1

        with self.assertRaisesRegex(ValueError, "checksum"):
            decode_message(bytes(corrupted))

    def test_message_shorter_than_header(self):
        with self.assertRaisesRegex(ValueError, "shorter than header"):
            decode_message(b"\x01\x02")

    def test_invalid_message_type(self):
        invalid_header = struct.pack(
            HEADER_FORMAT,
            PROTOCOL_VERSION,
            99,  # Invalid message type
            100,
            5,
            1,
            0,
        )

        with self.assertRaisesRegex(ValueError, "message type"):
            decode_message(invalid_header)


if __name__ == "__main__":
    unittest.main()