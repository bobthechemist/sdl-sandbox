import threading
import queue
import time
from .device import Device # <-- IMPORT THE NEW CLASS
from host.core.discovery import find_data_comports
from shared_lib.messages import Message
import json
import logging

log = logging.getLogger(__name__)

class DeviceManager:
    """
    Manages the lifecycle of Device objects and routes messages to them.
    This is the 'Controller' in our MVC architecture.
    """
    def __init__(self):
        self.devices = {}  # {port: Device object}
        self.listener_threads = {}
        self.stop_events = {}
        self.incoming_message_queue = queue.Queue()
        

    def start(self):
        """Starts the message processing thread."""

        log.info("DeviceManager started")

    def stop(self):
        """Stops all threads and disconnects all devices."""
        log.info("DeviceManager stopping...")
        self.disconnect_all()
        log.info("DeviceManager stopped.")

    def scan_for_devices(self):
        log.info("Scanning for devices...")
        return find_data_comports()

    def connect_device(self, port: str, vid: int, pid: int):
        if port in self.devices:
            log.warning(f"Already managing a device on {port}.")
            return

        log.info(f"Creating device model for {port}...")
        device = Device(port, vid, pid)
        
        if device.connect():
            self.devices[port] = device
            stop_event = threading.Event()
            thread = threading.Thread(
                target=self._listen_for_messages, 
                args=(device, stop_event), 
                daemon=True
            )
            self.stop_events[port] = stop_event
            self.listener_threads[port] = thread
            thread.start()
            return True
        else:
            return False

    def disconnect_device(self, port: str):
        if port not in self.devices:
            return

        log.info(f"Disconnecting from {port}...")
        self.stop_events[port].set()
        self.listener_threads[port].join(timeout=2)
        self.devices[port].disconnect()
        
        del self.devices[port]
        del self.listener_threads[port]
        del self.stop_events[port]
        log.info(f"Disconnected and cleaned up resources for {port}.")

    def disconnect_all(self):
        for port in list(self.devices.keys()):
            self.disconnect_device(port)

    def send_message(self, port: str, message: Message):
        if port not in self.devices:
            log.error(f"Cannot send message. No device at {port}.")
            return
            
        try:
            device = self.devices[port]
            device.send_message(message)
            self.incoming_message_queue.put(('SENT', port, message))
        except Exception as e:
            log.error(f"Failed to send message to {port}: {e}")

    def _listen_for_messages(self, device: Device, stop_event: threading.Event):
        """Worker that listens on one device's Postman and puts messages on the central queue."""
        port = device.port
        while not stop_event.is_set():
            try:
                raw_data = device.postman.receive()
                if raw_data:
                    try:
                        message = Message.from_json(raw_data)
                        self.incoming_message_queue.put(('RECV', port, message))
                    except (json.JSONDecodeError, ValueError):
                        self.incoming_message_queue.put(('RAW', port, raw_data))
                time.sleep(0.05)
            except Exception as e:
                log.error(f"Critical error in listener for {port}: {e}")
                self.incoming_message_queue.put(('ERROR', port, str(e)))
                break
    
