Low-power Micropython MQTT temperature logger for DS18B20 and ESP8266 (Banggood ESP12E) running on 18650 Lipo.

![Overview](templogger.png)

Features:

- Temperature sensor
- 1/60 Hz update interval
- Low-power (deepsleep)
- Battery level indicator
- Battery voltage level
- Logging to MQTT
- Multiple sensor support
- Webrepl alternative boot

# Functionality
This firmware is configured to run the following steps at boot:

- Read battery voltage
- Read all connected one-wire temperature sensors
- Wait for Wifi connection to be established (timeout 10s)
- Publish values to MQTT host named `mqtt` on default MQTT port.
- Shutdown and enter deep-sleep to conserve power
- Wakeup (boot) after 60 seconds (minus runtime)

This cycle repeats until the battery is dead or alternative boot is selected (see below).

# Example output
Logging to MQTT will look like this:

    templog/9b80e600/battery ok
    templog/9b80e600/280d7427050000e5 22.37
    templog/9b80e600/voltage 4.11

The first topic level is always `templog`, the next level is the unique device ID.

The `battery` topic show status of the battery `ok` for anything above 3.5v, `low` for everything below.

The `voltage` topic shows the actual battery voltage in volts.

For every onewire temperature sensor a topic is added with the unique ID of that sensor. Multiple sensors are supported and adding/removing sensors is possible without powercycle.

When using webrepl in testing mode (see below) sensor information is also printed as python dictionary like this:

    >>> import templog; templog.templog(sleep=False)
    {'battery': 'ok', 'voltage': 4.111, '280d7427050000e5': 22.37}

# Hardware

Requirements:

- ESP12E (or other ESP8266 device, but tested on ESP12E)
- DS18B20 one-wire temperature sensor(s)
- 18650 battery (or alternative power source)
- onewire pullup resistor (4k7 or similar)

The following connections need to be made:

- Battery + to VDD, CH_PD and GPIO02
- Battery - to GND and GPIO15
- VDD to onewire VDD
- GND to onewire GND
- VDD to pull-up resistor
- Pull-up resistor to GPIO12
- GPIO12 to onewire data
- GPIO16 (WAKE) to RST

![ESP12E pinout](http://simba-os.readthedocs.io/en/latest/_images/esp12e-pinout.png)

![Circuit overview](circuit.png)

Not shown on picture a wire between `VDD` and `CH_PD`!

# Setup
Clone this repository using `--recursive` or update submodules `git submodule update --init`.

Ensure ESP12E device has:

- Micropython installed (tested with 1.8.6) https://docs.micropython.org/en/latest/esp8266/esp8266/tutorial/intro.html#intro
- Is configured for Wifi https://docs.micropython.org/en/latest/esp8266/esp8266/tutorial/network_basics.html#configuration-of-the-wifi
- Has Webrepl enabled https://docs.micropython.org/en/latest/esp8266/esp8266/tutorial/repl.html#webrepl-a-prompt-over-wifi
- Has ADC switched to battery input (see below)

Next copy all these files using webrepl_cli:

    webrepl/webrepl_cli.py templog.py <ip of device>:
    webrepl/webrepl_cli.py micropython-lib/umqtt.simple/umqtt/simple <ip of device>:umqtt/

Log into [webrepl](http://micropython.org/webrepl/), connect to the device and run:

    import templog; templog.templog(sleep=False)

This will read battery and temperature values, print them and publish to MQTT but not go into deep sleep.

Enable templogger on boot:

    webrepl/webrepl_cli.py boot.py <ip of device>:

# Alternative boot to webrepl
To run Webrepl (upload new firmware/debug) instead of the temperature logger at boot pull down the 1w datapin (GPIO12) to ground. During bootup this will select webrepl. Since the software boots every 60 seconds after deepsleep just connecting the 1w pin to ground should have it end up in webrepl within a minute without cycling power.

To return to normal templogging mode powercycle the device or run: `import machine; machine.reset()`.

# Battery voltage level
To allow measurement of battery voltage instead of ADC input pin run `adc_vdd.py` once. This will configure the ADC to allow reading the voltage accross `gnd` and `vdd`.
