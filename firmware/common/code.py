# type: ignore
# Basic setup for code.py. Replace SUBSYSTEM with the appropriate one

from firmware.SUBSYSTEM import machine
from time import sleep

machine.run()
while True:
    machine.update()
    sleep(0.005)
