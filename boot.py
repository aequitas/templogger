# This file is executed on every boot (including wake-boot from deepsleep)
# import esp
# esp.osdebug(None)
import machine

# switch between normal and repl mode depending on pin12 pulldown
pin = machine.Pin(12, machine.Pin.IN)
if pin.value():
    import templog
    templog.templog()
else:
    import gc
    import webrepl
    webrepl.start()
    gc.collect()
