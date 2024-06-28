# type: ignore
import adafruit_board_toolkit.circuitpython_serial
import mse1
import asyncio


# get all data ports
ports = adafruit_board_toolkit.circuitpython_serial.data_comports()
# Assume the first one is what we want
port = None
if len(ports) > 0:
    port = ports[0]
else:
    print("no ports found")

# Port ID
print(f"Found a device on {port.device}. (VID:{port.vid}, PID:{port.pid})")

# Connecting to port
if not port is None:
    s = mse1.sdlCommunicator(port=port.device)
    asyncio.run(s.host_main())