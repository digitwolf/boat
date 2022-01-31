#!/usr/bin/python3
import pydevd_pycharm
#pydevd_pycharm.settrace('192.168.4.110', port=2345, stdoutToServer=True, stderrToServer=True)


import can
import atexit
import asyncio
import logging, sys
import bms

from prometheus_client import start_http_server
from prometheus_client import Gauge

logging.basicConfig(format='[%(levelname)s] %(asctime)s:%(message)s', level=logging.INFO)

handlers = [
    bms.BmsCellReportMessage.from_message,
    bms.BmsStatusMessage.from_message,
    bms.BmsTemperatureStatus.from_message,
    bms.ChargeControlMessage.from_message,
    bms.ChargeStatusMessage.from_message
]
            
            
cell_voltage = Gauge('battery_cell_volts', 'Cell Voltage, V', ['cell_id'])
cell_temperature = Gauge('battery_temp', 'Battery Temperature, C', ['therm_id'])


def invert_cell_index(idx, ltc_id):
    if ltc_id == 1:
        return 12 + idx
    else:
        return idx


def log_cell_report(report):
    for k, v in report.volts.items():
        idx = invert_cell_index(k, report.ltc_id)
        if k <= 23:
            cell_voltage.labels(cell_id=idx).set(v/1000)


def log_cell_temperature(report):
    for i in range(len(report.thermistors_enabled)):
        if report.thermistors_enabled[i]:
            temp = report.temperatures[i]
            id = report.ltc_idx * 5 + i
            cell_temperature.labels(therm_id=id).set(temp)



def parse_data(can):
    for handler in handlers:
        msg = handler(can)
        if msg is not None:

            if isinstance(msg, bms.BmsCellReportMessage):
                logging.debug("BmsCellReportMessage: %s", msg)
                log_cell_report(msg)

            if isinstance(msg, bms.BmsTemperatureStatus):
                logging.debug("BmsTemperatureStatus: %s", msg)
                log_cell_temperature(msg)

            break


async def main():
    start_http_server(7001)
    bus = can.interface.Bus(bustype='socketcan', channel='can0', bitrate=250000, receive_own_messages=False)

    reader = can.AsyncBufferedReader()
    loop = asyncio.get_event_loop()
    listeners = [
        parse_data,  # Callback function
        reader,
    ]
    notifier = can.Notifier(bus, [parse_data], loop=loop)
    
    bus.send(bms.BmsCellReportMessage.create_request(0, 0))
    bus.send(bms.BmsCellReportMessage.create_request(0, 1))
    atexit.register(lambda: bus.shutdown())

    logging.info("Started!")
    while True:
        # Wait for next message from AsyncBufferedReader
        await asyncio.sleep(10)
        bus.send(bms.BmsCellReportMessage.create_request(0, 0))
        bus.send(bms.BmsCellReportMessage.create_request(0, 1))

    #print("Done!")
    # Clean-up
    notifier.stop()
    bus.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
