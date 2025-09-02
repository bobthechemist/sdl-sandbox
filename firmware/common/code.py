# type: ignore
# Basic setup for code.py. Replace SUBSYSTEM with the appropriate one

from firmware.SUBSYSTEM import machine
from time import sleep

# Use numerical value to avoid having to do an import
#  DEBUG:10, INFO: 20, ...
machine.log.setLevel(10)
machine.run()
while True:
    machine.update()
    sleep(0.005)
