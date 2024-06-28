# type: ignore **siliences pylance errors in development system**
import board
import digitalio
import json
import time
import usb_cdc
import random

################################################################
# init board's LEDs for visual output
################################################################

pix = None
if hasattr(board, "NEOPIXEL"):
    import neopixel
    pix = neopixel.NeoPixel(board.NEOPIXEL, 1)
    pix.fill((0,0,128))
else:
    print("This board is not equipped with a Neopixel.")

led = None
for ledname in ["LED", "L", "RED_LED", "BLUE_LED"]:
    if hasattr(board, ledname):
        led = digitalio.DigitalInOut(getattr(board, ledname))
        led.switch_to_output()
        led.value = False
        print(ledname)
        break


################################################################
# prepare values for the loop
################################################################

usb_cdc.data.timeout = 0.1

#
# Create a random message
#
def random_message(i):

    return {"success":True,"response":i}


################################################################
# loop-y-loop
################################################################
i = 0
while True:
    # add to that dictionary to send the data at the end of the loop
    data_out = {}
    data_out = random_message(i)

    # read the data serial line by line when there's data
    if usb_cdc.data.in_waiting > 0:
        data_in = usb_cdc.data.readline()

        # try to convert the data to a dict (with JSON)
        data = None
        if len(data_in) > 0:
            try:
                data = json.loads(data_in)
            except ValueError:
                data_out = {"raw": data_in.decode()}

        # interpret
        if isinstance(data, dict):

            # change the color of the neopixel
            if "color" in data:
                print(data["color"])
                if pix is not None:
                    pix.fill(data["color"])

            # blinking without sleep is left as an exercise
            if "blink" in data and led is not None:
                led.value = True
                time.sleep(0.25)
                led.value = False
                time.sleep(0.25)
                data_out["blink"] = [{"status": "DONE", "id": led.value}]


    # send the data out once everything to be sent is gathered
    if data_out and i < 5:
        print(json.dumps(data_out))
        usb_cdc.data.write(json.dumps(data_out).encode() + b"\r\n")
    i = (i + 1)%4
    time.sleep(1)
