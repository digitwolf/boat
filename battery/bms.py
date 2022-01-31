from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Optional

from can import Message


def is_bit(byte, bit) -> bool:
    return byte >> bit & 1 == 1


def get_voltage(byte1, byte2) -> float:
    return int.from_bytes([byte1, byte2], byteorder='little') / 10


@dataclass
class BmsMessage:
    can_message: Message


@dataclass
class BmsStatusMessage(BmsMessage):
    """This message is sent once a second by the BMS to indicate BMS health."""

    # BMS status flag definitions
    cell_hvc: bool  # at least one cell v is >HVC
    cell_lvc: bool  # at least one cell v is <LVC
    cell_bvc: bool  # at least one cell v is >BVC

    # BMS flag definitions
    fault_not_locked: bool  # configuration not locked
    fault_not_census: bool  # not all cells present
    fault_not_overtemp: bool  # thermistor overtemp
    fault_not_therm_census: bool  # not all thermistors present

    bmsc_id: int  # bmsc id (0..3)
    ltc_fault: bool
    ltc_count: int

    def __init__(self, msg: Message) -> None:
        super().__init__(msg)

        data = msg.data

        self.cell_hvc = is_bit(data[0], 0)
        self.cell_lvc = is_bit(data[0], 1)
        self.cell_bvc = is_bit(data[0], 3)

        self.bmsc_id = data[1]

        self.fault_not_locked = is_bit(data[2], 0)
        self.fault_not_census = is_bit(data[2], 1)
        self.fault_not_overtemp = is_bit(data[2], 3)
        self.fault_not_therm_census = is_bit(data[2], 7)

        self.ltc_fault = data[3] & 1 == 1  # Not sure if this is correct: bit mask; 1 indicates error
        self.ltc_count = data[4]

    @staticmethod
    def from_message(msg: Message) -> Optional[BmsMessage]:
        if msg.arbitration_id != 0x01dd0001:
            return None

        return BmsStatusMessage(msg)


@dataclass
class BmsTemperatureStatus(BmsMessage):
    """
    This message is sent once a second sent by the BMS to report the
    thermistor temperatures. Each report is for one LTC, and so it takes
    8 seconds to report the temperatures of all thermistors
    LTCs are numbered from 0 to 7; `bLtcIdx` indicates the LTC
    """
    ltc_idx: int
    thermistors_enabled: [bool]  # indicates which thermistors are enabled
    thermistors_present: [bool]  # indicates which thermistors are detected
    temperatures: bytearray  # an array of 5 entries that contains the temperature, in C, for each thermistor

    def __init__(self, msg: Message) -> None:
        super().__init__(msg)
        self.ltc_idx = msg.data[0]
        self.thermistors_enabled = []
        self.thermistors_present = []
        for bit in range(5):
            self.thermistors_enabled.append(is_bit(msg.data[1], bit))
            self.thermistors_present.append(is_bit(msg.data[2], bit))

        self.temperatures = msg.data[3:]

    @staticmethod
    def from_message(msg: Message):
        if msg.arbitration_id != 0x01df0e00:
            return None

        return BmsTemperatureStatus(msg)


@dataclass
class BmsCellReportMessage(BmsMessage):
    """
    Report voltages for 4 cells.
    Index of cells depends on the id of the message.

    For example:
    #define DD_BMS_CVCUR_C1_TO_C4_RSP 0x01df0900
    #define DD_BMS_CVCUR_C5_TO_C8_RSP 0x01df0a00
    #define DD_BMS_CVCUR_C9_TO_C12_RSP 0x01df0b00
    """

    bsc_id: int
    ltc_id: int
    volts: [int, float]

    def __init__(self, msg: Message) -> None:
        super().__init__(msg)

        self.bsc_id = msg.arbitration_id & 0x0030
        self.ltc_id = msg.arbitration_id & 0x0007

        idx = (msg.arbitration_id.to_bytes(4, "little")[1] - 9) * 4

        self.volts = {
            idx: get_voltage(msg.data[0], msg.data[1]),
            idx + 1: get_voltage(msg.data[2], msg.data[3]),
            idx + 2: get_voltage(msg.data[4], msg.data[5]),
            idx + 3: get_voltage(msg.data[6], msg.data[7]),
        }

    @staticmethod
    def from_message(msg: Message):
        if msg.arbitration_id >> 8 in (0x01df09, 0x01df0a, 0x01df0b):
            return BmsCellReportMessage(msg)
        else:
            return None


    @staticmethod
    def create_request(bsc_id=0, ltc_id=0) -> Message:
        msg = Message(
            arbitration_id=0x01de0800 | bsc_id << 4 | ltc_id,
            is_extended_id=True
        )

        return msg


@dataclass
class ChargeStatusMessage(BmsMessage):
    """Charge status message sent by tsm2500"""

    status_flags: int
    charge_flags: int

    output_voltage: float  # charge voltage in volts
    output_current: float  # charge current in amps

    charger_temperature: int

    def __init__(self, msg: Message) -> None:
        super().__init__(msg)

        self.status_flags = msg.data[0]
        self.charge_flags = msg.data[1]

        self.output_voltage = get_voltage(msg.data[2], msg.data[3])
        self.output_current = (3200 - int.from_bytes([msg.data[4], msg.data[5]], byteorder='little')) / 10

        self.charger_temperature = msg.data[6] - 40

    @staticmethod
    def from_message(msg: Message):
        if msg.arbitration_id != 0x18eb2440:
            return None

        return ChargeStatusMessage(msg)


@dataclass
class ChargeControlMessage(BmsMessage):
    """Charge status message sent by tsm2500"""

    enable: bool

    charge_voltage: float  # charge voltage in volts
    charge_current: float  # charge current in amps

    blink_pattern: int

    def __init__(self, msg: Message) -> None:
        super().__init__(msg)

        self.enable = msg.data[0]

        self.charge_voltage = get_voltage(msg.data[1], msg.data[2])
        self.charge_current = (3200 - int.from_bytes([msg.data[3], msg.data[4]], byteorder='little')) / 10

        self.blink_pattern = msg.data[5]

    @staticmethod
    def from_message(msg: Message):
        if msg.arbitration_id != 0x18e54024:
            return None

        return ChargeControlMessage(msg)


message_handler = Callable[[Message], BmsMessage]
