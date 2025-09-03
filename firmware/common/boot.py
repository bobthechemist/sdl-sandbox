# type: ignore
import usb_cdc
import supervisor

# Remember changes to boot.py only go into effect upon power cycling the uC.
# (The reset button won't do it.)

supervisor.set_usb_identification(
    vid=808,
    pid=808,
    # These variables cannot be written, so they are here in case something changes in the future.
    product="something awesome",
    manufacturer="Brockport Original Builds")

usb_cdc.enable(console=True, data=True)