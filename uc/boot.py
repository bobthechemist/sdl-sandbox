import usb_cdc
import supervisor

# product and manufacturer cannot be written; however vid and pid can.
supervisor.set_usb_identification(
    vid=808,
    pid=808,
    product="something awesome",
    manufacturer="Brockport Original Builds")
# Will probably want console=False for actual device
usb_cdc.enable(console=True, data=True)