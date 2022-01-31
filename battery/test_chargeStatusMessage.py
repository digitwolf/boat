from unittest import TestCase

from can import Message

from bms import ChargeStatusMessage


class TestChargeStatusMessage(TestCase):
    def test_from_message(self):
        status: ChargeStatusMessage = ChargeStatusMessage.from_message(Message(
            arbitration_id=0x18eb2440,
            data=[0x00, 0x00, 0xe9, 0x04, 0x33, 0x0C, 0x4A]
        ))

        self.assertTrue(status.status_flags == 0)
        self.assertTrue(status.charge_flags == 0)

        self.assertEqual(status.charger_temperature, 34)
        self.assertEqual(status.output_voltage, 125.7)
        self.assertEqual(status.output_current, 7.7)

