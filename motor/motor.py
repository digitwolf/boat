# import pydevd_pycharm
# pydevd_pycharm.settrace('192.168.4.110', port=2345, stdoutToServer=True, stderrToServer=True)


import asyncio
import atexit
import logging
import sys
import can
import canopen
from influxdb import InfluxDBClient
from prometheus_client import Gauge, start_http_server

import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BOARD)		#set pin numbering system
GPIO.setup(32,GPIO.OUT)
rpm_pwm = GPIO.PWM(32, 1)
rpm_pwm.start(50)

BATTERY_VOLTAGE = Gauge('motor_battery_voltage', 'Motor Battery Voltage, V')
MOTOR_CURRENT = Gauge('motor_current_amps', 'Motor Battery Current, A', ['sensor'])
MOTOR_VOLTAGE = Gauge('motor_voltage', 'AC Motor Voltage, V')
CAPACITOR_VOLTAGE = Gauge('motor_capacitor_voltage', 'Motor Controller Capacitor Voltage, V')

THROTTLE = Gauge('throttle', 'Throttle input V, direction', ['sensor'])

MOTOR_TEMPERATURE = Gauge('motor_temperature', 'Motor temperatures', ['sensor'])
MOTOR_TEMPERATURE_OVERALL = Gauge('motor_temperature_overall',
                                  'Highest temperature from all sources (heatsink, motor, etc).. In 12.4 DegC')

MOTOR_TORQUE = Gauge('motor_torque', 'Torque in 12.4Nm', ['type'])

MOTOR_RPM = Gauge('motor_rpm', 'RPM')

db_client = InfluxDBClient('localhost', 8086, 'kisa', 'Ar@nji', 'boat')

def get_rpm_frequency(rpm):
    """
    2000 - 250
    rpm  - x
    x = rpm * 250 / 200
    """
    return abs(rpm) * 180 / 1000

def update_tach(rpm):
    rpm_pwm.ChangeFrequency(get_rpm_frequency(rpm))


def write_rpm(rpm):
    body = [
        {
            "measurement": "rpm",
            "fields": {
                "Int_value": rpm,
            }
        }
    ]
    db_client.write_points(body)


def record_rpm(pdo):
    rpm=-1*pdo[0].raw
    update_tach(rpm)
    MOTOR_RPM.set(rpm)
    write_rpm(rpm)


def read_device_status(node):
    device_status = node.sdo[0x5100]

    battery_voltage_volts = device_status[1].raw * 0.0625
    battery_current_amps = device_status[2].raw * 0.0625
    capacitor_voltage_volts = device_status[7].raw * 0.25

    logging.info('Battery Voltage: %f V,    Battery Current: %f A,    Capacitor Voltage, %f V ',
                 battery_voltage_volts, battery_current_amps, capacitor_voltage_volts)

    BATTERY_VOLTAGE.set(battery_voltage_volts)
    MOTOR_CURRENT.labels('battery').set(battery_current_amps)
    CAPACITOR_VOLTAGE.set(capacitor_voltage_volts)


def read_throttle(node):
    forward = node.sdo[0x2121].raw
    reverse = node.sdo[0x2122].raw

    direction = int(forward) - int(reverse)
    THROTTLE.labels(sensor='direction').set(direction)
    THROTTLE.labels(sensor='voltage').set(node.sdo[0x2220].raw * 0.00390625)


def read_motor_debug_info(node):
    #rpm_sdo = node.sdo[0x2020]
    #rpm = -1 * rpm_sdo[4].raw
    #MOTOR_RPM.set(rpm)
    #write_rpm(rpm)
    # update_tach(rpm)
    
    motor_info = node.sdo[0x4600]
    MOTOR_TEMPERATURE.labels(sensor='Motor1').set(motor_info[3].raw)
    MOTOR_TEMPERATURE.labels(sensor='MotorRemote').set(motor_info[0x10].raw)
    MOTOR_CURRENT.labels(sensor='AC').set(motor_info[0xC].raw * 0.0625)
    MOTOR_VOLTAGE.set(motor_info[0xD].raw * 0.0625)

    """Reads SDO 4602h"""
    motor_info = node.sdo[0x4602]

    # DSP Estimated MOSFET junction temperature in 16.0 DegC.
    MOTOR_TEMPERATURE.labels(sensor='Junction1').set(motor_info[2].raw)
    MOTOR_TEMPERATURE.labels(sensor='Junction2').set(motor_info[3].raw)
    MOTOR_TEMPERATURE.labels(sensor='Junction3').set(motor_info[4].raw)
    MOTOR_TEMPERATURE.labels(sensor='Junction4').set(motor_info[5].raw)
    MOTOR_TEMPERATURE.labels(sensor='Junction5').set(motor_info[6].raw)
    MOTOR_TEMPERATURE.labels(sensor='Junction6').set(motor_info[7].raw)

    # Estimated Motor Temperature. In 16.0 DegC
    MOTOR_TEMPERATURE.labels(sensor='MotorEstimate').set(motor_info[8].raw)

    # Heatsink temperature in 8.0 DegC.
    MOTOR_TEMPERATURE.labels(sensor='Heatsink').set(motor_info[9].raw)

    # Overall DSP Maximum Motor Temperature (Y.Temp_max)
    MOTOR_TEMPERATURE_OVERALL.set(motor_info[10].raw)

    # Torque in 12.4Nm
    MOTOR_TORQUE.labels(type='demand').set(motor_info[11].raw * 0.0625)
    MOTOR_TORQUE.labels(type='actual').set(motor_info[12].raw * 0.0625)

    # Maximum torque sent to DSP in 12.4Nm
    MOTOR_TORQUE.labels(type='max').set(motor_info[13].raw * 0.0625)
    MOTOR_TORQUE.labels(type='limit').set(motor_info[14].raw * 0.0625)

    # AC Current sensor autozero value in 12.4
    MOTOR_CURRENT.labels(sensor='M1').set(motor_info[22].raw * 0.0625)
    MOTOR_CURRENT.labels(sensor='M2').set(motor_info[23].raw * 0.0625)
    # M3 is missing MOTOR_CURRENT.labels(sensor='M3').set(motor_info[24].raw * 0.0625)

    BATTERY_VOLTAGE.set(motor_info[17].raw * 0.0625)
    CAPACITOR_VOLTAGE.set(motor_info[18].raw * 0.0625)

    # Value of the long term capacitor temperature estimate, this is regarded as the temperature rise over an hour
    # at the maximum current which would cause acceptable ripple current capacitor degradation
    MOTOR_TEMPERATURE.labels(sensor='CapacitorLong').set(motor_info[21].raw)
    MOTOR_TEMPERATURE.labels(sensor='PCBTrack').set(motor_info[20].raw)


def get_device_measurements(node):
    device_info = node.sdo[0x5100]

    MOTOR_CURRENT.labels(sensor='Battery').set(device_info[2] * 0.0625)


def print_speed(message):
    print('%s received' % message.name)
    for var in message:
        print('%s = %d' % (var.name, var.raw))


def heatsink_temperature_handler(message):
    temperature = message.raw * 0.0625


def velocity_handler(message):
    velocity = message.raw * 0.001


handlers = {
    '0x2020_5': velocity_handler,
    '0x5100_4': heatsink_temperature_handler
}

# def attach_listeners(node):
#     node.tpdo[3].add_callback(temperature_handler)
#     node.tpdo[5].add_callback(velocity_handler)

async def main():
    start_http_server(7002)
    network = canopen.Network()
    try:
        network.connect(channel='can1', bustype='socketcan', bitrate=500000)
    except Exception as error:
        logging.error(f'Couldn\'t connect to CanOpen network: ', error)
        sys.exit(-1)

    node = network.add_node(1, '/home/pi/AC24ls.dcf')

    atexit.register(lambda: network.disconnect())


    node.tpdo.read()
    node.tpdo[5].add_callback(record_rpm)
    
    while True:
        read_device_status(node)
        read_throttle(node)
        read_motor_debug_info(node)
        await asyncio.sleep(3)

    network.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
