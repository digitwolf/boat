from unittest import TestCase

from can import Message

from bms import BmsStatusMessage


class TestBmsStatusMessage(TestCase):
    def test_from_message(self):
        status: BmsStatusMessage = BmsStatusMessage.from_message(Message(
            arbitration_id = 0x01dd0001,
            data = [0, 0, 0, 0, 2]
        ))

        self.assertFalse(status.fault_not_census)
        self.assertFalse(status.fault_not_locked)
        self.assertFalse(status.fault_not_overtemp)
        self.assertFalse(status.fault_not_therm_census)

        self.assertEqual(status.ltc_count, 2)
