import esp
import machine
from flashbdev import bdev

sector_size = bdev.SEC_SIZE
flash_size = esp.flash_size()  # device dependent
init_sector = int(flash_size / sector_size - 4)
data = bytearray(esp.flash_read(init_sector * sector_size, sector_size))
data[107] = 255
esp.flash_erase(init_sector)
esp.flash_write(init_sector * sector_size, data)
machine.reset()

# from machine import ADC
# ADC(1).read()
