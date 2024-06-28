# type: ignore
import adafruit_board_toolkit.circuitpython_serial
import mse1
import asyncio


# get all data ports
ports = adafruit_board_toolkit.circuitpython_serial.data_comports()
# Assume the first one is what we want

if len(ports) > 0:
    for port in ports:
        print(f"Found a device on {port.device}. (VID:{port.vid}, PID:{port.pid})")
else:
    print("no ports found")

async def group():
    s = []
    for p in ports:
        s.append(mse1.sdlCommunicator(port=p.device))

    task1 = asyncio.create_task(s[0].read_serial_data())
    task2 = asyncio.create_task(s[1].read_serial_data())
    await asyncio.gather(task1,task2)
    
asyncio.run(group())

# Connecting to port
#if not port is None:
#    s = mse1.sdlCommunicator(port=port.device)
#    asyncio.run(s.host_main())