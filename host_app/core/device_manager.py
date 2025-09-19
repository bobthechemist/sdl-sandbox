import threading
import queue
import time
from communicate.serial_postman import SerialPostman
from communicate.host_utilities import find_data_comports
from shared_lib.messages import Message
import json
import logging

# Configure logging for this module
log = logging.getLogger(__name__)

class DeviceManager:
    """
    Handles all backend logic for device communication and lifecycle management.
    This class is UI-agnostic.
    """
    def __init__(self):
        self.connections = {}  # {port: SerialPostman}
        self.listener_threads = {}  # {port: threading.Thread}
        self.stop_events = {}  # {port: threading.Event}
        self.incoming_message_queue = queue.Queue()  # Thread-safe queue for all messages

    def scan_for_devices(self):
        """Scans for available CircuitPython devices."""
        log.info("Scanning for devices...")
        return find_data_comports()

    def connect_device(self, port: str):
        """Establishes a connection to a device on a given port."""
        if port in self.connections:
            log.warning(f"Already connected to {port}.")
            return

        try:
            log.info(f"Attempting to connect to {port}...")
            params = {"protocol": "serial", "port": port, "baudrate": 115200, "timeout": 0.1}
            postman = SerialPostman(params)
            postman.open_channel()
            time.sleep(1) # Allow time for serial connection to establish
            postman.channel.reset_input_buffer()
            
            stop_event = threading.Event()
            thread = threading.Thread(target=self._listen_for_messages, args=(port, postman, stop_event), daemon=True)
            
            self.connections[port] = postman
            self.stop_events[port] = stop_event
            self.listener_threads[port] = thread
            
            thread.start()
            log.info(f"Successfully connected to {port}. Listener started.")
            return True
        except Exception as e:
            log.error(f"Failed to connect to {port}: {e}")
            return False

    def disconnect_device(self, port: str):
        """Terminates the connection to a device."""
        if port not in self.connections:
            log.warning(f"Not connected to {port}.")
            return

        log.info(f"Disconnecting from {port}...")
        self.stop_events[port].set()  # Signal the thread to stop
        self.listener_threads[port].join(timeout=2)  # Wait for the thread to exit
        self.connections[port].close_channel()
        
        # Clean up resources
        del self.connections[port]
        del self.listener_threads[port]
        del self.stop_events[port]
        log.info(f"Disconnected from {port}.")

    def disconnect_all(self):
        """Disconnects from all currently connected devices."""
        ports = list(self.connections.keys())
        for port in ports:
            self.disconnect_device(port)

    def send_message(self, port: str, message: Message):
        """Sends a Message object to a specific device."""
        if port not in self.connections:
            log.error(f"Cannot send message. Not connected to {port}.")
            return
            
        try:
            postman = self.connections[port]
            postman.send(message.serialize())
            # Put the sent message on the queue so the UI can log it
            self.incoming_message_queue.put(('SENT', port, message))
        except Exception as e:
            log.error(f"Failed to send message to {port}: {e}")

    def _listen_for_messages(self, port: str, postman: SerialPostman, stop_event: threading.Event):
        """The worker method that runs in a thread, listening for data."""
        while not stop_event.is_set():
            try:
                raw_data = postman.receive()
                if raw_data:
                    try:
                        message = Message.from_json(raw_data)
                        self.incoming_message_queue.put(('RECV', port, message))
                    except (json.JSONDecodeError, ValueError):
                        # Put raw data on the queue for display
                        self.incoming_message_queue.put(('RAW', port, raw_data))
                time.sleep(0.05)  # Prevent CPU spinning
            except Exception as e:
                log.error(f"Error in listener for {port}: {e}")
                self.incoming_message_queue.put(('ERROR', port, str(e)))
                break # Exit thread on critical error