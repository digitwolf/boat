from unittest import TestCase

from can import Message

from bms import BmsCellReportMessage


class TestBmsCellReportMessage(TestCase):
    def test_from_message_c1_to_c4(self):
        status: BmsCellReportMessage = BmsCellReportMessage.from_message(Message(
            arbitration_id=0x01df0902,
            data=[0xe9, 0x04, 0xe9, 0x04, 0xe9, 0x04, 0xe9, 0x04]
        ))

        self.assertEqual(0, status.bsc_id)
        self.assertEqual(2, status.ltc_id)
        self.assertEqual(125.7, status.volts[0])


    def test_from_message_c5_to_c8(self):
        status: BmsCellReportMessage = BmsCellReportMessage.from_message(Message(
            arbitration_id=0x01df0a02,
            data=[0xe9, 0x04, 0xe9, 0x04, 0xe9, 0x04, 0xe9, 0x04]
        ))

        self.assertEqual(0, status.bsc_id)
        self.assertEqual(2, status.ltc_id)
        self.assertEqual(125.7, status.volts[5])
