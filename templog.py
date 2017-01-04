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
INTERVAL_SEC = 60
CONNECT_WAIT = 10
MQTT_SERVER = 'mqtt'


def rom_to_hex(rom):
    """Convert rom bytearray to hex string."""
    return ''.join('{:02x}'.format(x) for x in rom)


def mqtt_send(values):
    """Send key/value pairs over mqtt."""
    device_name = rom_to_hex(bytearray(machine.unique_id()))

    mqtt = MQTTClient(device_name, MQTT_SERVER)
    mqtt.connect()
    for name, raw_value in values.items():
        if isinstance(raw_value, float):
            value = b"{:4.2f}".format(raw_value)
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
            break
        time.sleep(1)


def deepsleep(uptime=0):
    """Put to sleep for 60 seconds minus uptime."""
    rtc = machine.RTC()
    rtc.irq(trigger=rtc.ALARM0, wake=machine.DEEPSLEEP)
    rtc.alarm(rtc.ALARM0, (INTERVAL_SEC * 1000) - uptime)
    machine.deepsleep()


def templog(sleep=True):
    """Log voltage and temperature to MQTT."""
    start = time.ticks_ms()

    # get sensor values
    values = read_voltage()
    values.update(read_temps())
    print(values)

    wait_connect()

    mqtt_send(values)

    if sleep:
        delta = time.ticks_diff(start, time.ticks_ms())
        deepsleep(delta)
