import threading
import queue
import time
from .device import Device
from host.core.discovery import find_data_comports
from host.firmware_db import get_device_name
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
        
    def connect_all(self):
        """
        Scans for and connects to all recognized CircuitPython devices.
        Returns a dictionary mapping device_key (slug) to port.
        """
        device_ports_map = {}
        all_ports = find_data_comports()
        
        if not all_ports:
            log.warning("No CircuitPython devices connected.")
            return device_ports_map
            
        for port_info in all_ports:
            port, vid, pid = port_info['port'], port_info['VID'], port_info['PID']
            friendly_name = get_device_name(vid, pid)

            if "Unknown" not in friendly_name:
                clean_name = friendly_name.split('(')[0].strip()
                device_key = clean_name.lower().replace(" ", "_")

                log.info(f"Connecting to {friendly_name} on {port}...")
                if self.connect_device(port, vid, pid):
                    device_ports_map[device_key] = port
                else:
                    log.error(f"Failed to connect to {port}")
        
        if not device_ports_map:
            log.warning("No recognized devices connected.")
        else:
            log.info(f"Connected to: {list(device_ports_map.keys())}")
            
        return device_ports_map

    def get_device_capabilities(self, ports: list, timeout: int = 5) -> dict:
        """
        Synchronously fetches the command capabilities ('help' command) for the given ports.
        Returns a dictionary mapping {port: raw_help_payload}.
        """
        if not ports:
            return {}

        log.info(f"Retrieving capabilities from {len(ports)} device(s)...")
        help_msg = Message.create_message("HOST", "INSTRUCTION", payload={"func": "help", "args": {}})
        
        for port in ports:
            self.send_message(port, help_msg)

        capabilities = {}
        start_time = time.time()
        
        while len(capabilities) < len(ports) and (time.time() - start_time) < timeout:
            try:
                msg_type, msg_port, msg_data = self.incoming_message_queue.get_nowait()
                
                if msg_type == 'RECV':
                    # Ensure the Device model stays updated with anything pulled from the queue
                    if msg_port in self.devices:
                        self.devices[msg_port].update_from_message(msg_data)

                    # Check if this is the expected help payload
                    if msg_data.status == "DATA_RESPONSE":
                        payload = msg_data.payload
                        data_content = payload.get('data', {})
                        
                        # Heuristic: verify this is the command description dictionary
                        if (isinstance(data_content, dict) and data_content and
                            isinstance(next(iter(data_content.values()), None), dict) and
                            'description' in next(iter(data_content.values()), {})):
                            
                            capabilities[msg_port] = payload
                            log.info(f"Successfully received capabilities from {msg_port}.")
            except queue.Empty:
                time.sleep(0.1)

        if len(capabilities) < len(ports):
            missing = [p for p in ports if p not in capabilities]
            log.warning(f"Timeout: Did not receive capabilities from ports: {missing}")

        return capabilities

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