from unittest import TestCase

from can import Message

from bms import BmsTemperatureStatus


class TestBmsTemperatureStatus(TestCase):
    def test_from_message(self):
        status: BmsTemperatureStatus = BmsTemperatureStatus.from_message(Message(
            arbitration_id=0x01df0e00,
            data=[0x00, 0x1f, 0x1f, 0x01, 0x02, 0x03, 0x04, 0x05]
        ))

        self.assertEqual(status.ltc_idx, 0)
        self.assertEqual(len(status.temperatures), 5)

        self.assertEqual(status.temperatures[0], 1)
        self.assertEqual(status.temperatures[1], 2)
        self.assertEqual(status.temperatures[2], 3)
        self.assertEqual(status.temperatures[3], 4)
        self.assertEqual(status.temperatures[4], 5)

        self.assertTrue(status.thermistors_enabled[0])
        self.assertTrue(status.thermistors_enabled[1])
        self.assertTrue(status.thermistors_enabled[2])
        self.assertTrue(status.thermistors_enabled[3])
        self.assertTrue(status.thermistors_enabled[4])

        self.assertTrue(status.thermistors_present[0])
        self.assertTrue(status.thermistors_present[1])
        self.assertTrue(status.thermistors_present[2])
        self.assertTrue(status.thermistors_present[3])
        self.assertTrue(status.thermistors_present[4])
