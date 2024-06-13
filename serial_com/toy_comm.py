"""
GOAL: Listen to two different USB devices for status information
"""

import adafruit_board_toolkit.circuitpython_serial
import serial
import asyncio
import time
import json

subsystems = []

# get all data ports and print info about them.
ports = adafruit_board_toolkit.circuitpython_serial.data_comports()

if len(ports) == 0:
    print("No devices found, bailing.")
else:
    print(f"Found {len(ports)} device(s).")
    for i, p in enumerate(ports):
        print(f'DEVICE {i}: PID={p.pid}, VID={p.vid} found on {p.device}.')

# connect to each of the subsystems
for p in ports:
    subsystems.append(serial.Serial(p.device))

async def read_serial():
        print("read serial")
        while True:
            for s in subsystems:
                 line = s.readline()[:-2]
                 if line !=b"":
                    print(line.decode())
            await asyncio.sleep(.1)

async def main():
     await asyncio.sleep(10)
     task.cancel()

loop = asyncio.get_event_loop()
try:
    task = loop.create_task(read_serial())
    loop.run_until_complete(main())
finally:
     loop.close()



