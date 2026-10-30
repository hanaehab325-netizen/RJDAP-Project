import unittest
import struct

from protocol import (
    MessageType,
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
        self.assertEqual(HEADER_SIZE, 13)

    def test_maximum_payload_allowed(self):
        payload = b"A" * MAX_PAYLOAD_SIZE

        message = encode_message(
            MessageType.TASK_DISPATCH, 1, 1, 1, payload
        )

        _, _, _, _, received_payload = decode_message(message)

        self.assertEqual(received_payload, payload)

    def test_payload_too_large(self):
        payload = b"A" * (MAX_PAYLOAD_SIZE + 1)

        with self.assertRaises(ValueError):
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
        with self.assertRaises(ValueError):
            decode_message(b"\x01\x02")

    def test_invalid_message_type(self):
        invalid_header = struct.pack(
            HEADER_FORMAT, 99, 100, 5, 1, 0
        )

        with self.assertRaisesRegex(ValueError, "message type"):
            decode_message(invalid_header)


if __name__ == "__main__":
    unittest.main()