"""Read ds18b20 and VDD voltage, write to mqtt."""

import time

import ds18x20
import machine
import network
import onewire
from machine import ADC
from umqtt.simple import MQTTClient

ADC_NUM = 1
PIN_1W = 12
MIN_INTERVAL = 1
INTERVAL_SEC = 60
CONNECT_WAIT = 10
MQTT_SERVER = 'mqtt'


def rom_to_hex(rom):
    """Convert rom bytearray to hex string."""
    return ''.join('{:02x}'.format(x) for x in rom)


pong = None


def mqtt_send(values):
    """Send key/value pairs over mqtt."""
    device_name = rom_to_hex(bytearray(machine.unique_id()))

    mqtt = MQTTClient(device_name, MQTT_SERVER)
    mqtt.connect()

    # do mqtt ping/pong to ensure communication with broker is ok
    for x in range(CONNECT_WAIT):
        mqtt.ping()

        mqtt.sock.setblocking(False)
        res = mqtt.sock.read(1)

        if res == b"\xd0":
            sz = mqtt.sock.read(1)[0]
            if sz == 0:
                break
        time.sleep(1)
    else:
        return False

    for name, raw_value in values.items():
        if isinstance(raw_value, float):
            value = b"{:4.3f}".format(raw_value)
        elif isinstance(raw_value, int):
            value = b"{:d}".format(raw_value)
        elif isinstance(raw_value, str):
            value = bytes(raw_value, 'utf8')

        mqtt.publish(b"templog/{}/{}".format(device_name, name), value)
    mqtt.disconnect()


def read_voltage():
    """Read VDD voltage and LiPO battery level."""
    voltage = ADC(ADC_NUM).read() / 1000
    return {
        'voltage': voltage,
        'battery': 'low' if voltage < 3.5 else 'ok',
    }


def read_temps():
    """Read DS18B20's."""
    dat = machine.Pin(PIN_1W)
    ds = ds18x20.DS18X20(onewire.OneWire(dat))

    ds.convert_temp()
    time.sleep_ms(750)

    return {rom_to_hex(rom): ds.read_temp(rom) for rom in ds.scan()}


def wait_connect():
    """Wait for wifi to be connected before attempting mqtt."""
    for x in range(CONNECT_WAIT):
        wlan = network.WLAN(network.STA_IF)
        if wlan.isconnected():
            print(wlan.ifconfig())
            return True
        time.sleep(1)
    else:
        return False


def deepsleep(uptime=0, calibrate=False):
    """Put to sleep for 60 seconds minus uptime."""
    rtc = machine.RTC()
    rtc.irq(trigger=rtc.ALARM0, wake=machine.DEEPSLEEP)
    sleeptime = max(MIN_INTERVAL, (INTERVAL_SEC * 1000) - uptime)
    rtc.alarm(rtc.ALARM0, sleeptime)
    machine.deepsleep()


def templog(sleep=True):
    """Log voltage and temperature to MQTT."""
    start = time.ticks_ms()

    # get sensor values
    values = read_voltage()
    values.update(read_temps())
    print(values)

    # send values over MQTT if connected
    if wait_connect():
        if not mqtt_send(values):
            machine.reset()
    else:
        # failed to connect, reboot
        machine.reset()

    if sleep:
        delta = time.ticks_diff(start, time.ticks_ms())
        deepsleep(delta)
