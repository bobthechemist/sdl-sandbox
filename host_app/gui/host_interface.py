import tkinter as tk
from tkinter import ttk, scrolledtext
import json
import threading
import time
from datetime import datetime
from ..firmware_db import get_device_name
from communicate.host_utilities import find_data_comports
from communicate.serial_postman import SerialPostman
from shared_lib.messages import Message

class SimpleHostGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Self-Driving Lab: Host Interface")
        self.root.geometry("800x600")

        # --- State Variables ---
        self.postman = None
        self.is_connected = False
        self.worker_thread = None
        self.stop_thread = threading.Event()
        self.available_devices = []  # --- MODIFIED ---: Will store the list of full device dicts

        # --- UI Setup ---
        self._create_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _create_widgets(self):
        # --- Connection Frame ---
        conn_frame = ttk.LabelFrame(self.root, text="Connection", padding=10)
        conn_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(conn_frame, text="Available Devices:").pack(side=tk.LEFT, padx=5)
        self.device_combo = ttk.Combobox(conn_frame, state="readonly")
        self.device_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.scan_btn = ttk.Button(conn_frame, text="Scan for Devices", command=self.scan_ports)
        self.scan_btn.pack(side=tk.LEFT, padx=5)
        
        self.connect_btn = ttk.Button(conn_frame, text="Connect", command=self.connect_device)
        self.connect_btn.pack(side=tk.LEFT, padx=5)
        
        self.disconnect_btn = ttk.Button(conn_frame, text="Disconnect", command=self.disconnect_device, state=tk.DISABLED)
        self.disconnect_btn.pack(side=tk.LEFT, padx=5)

        # ... (rest of the widget creation is the same) ...
        # --- Log Frame ---
        log_frame = ttk.LabelFrame(self.root, text="Incoming Messages", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # --- Command Frame ---
        cmd_frame = ttk.LabelFrame(self.root, text="Send Command", padding=10)
        cmd_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(cmd_frame, text="Payload (JSON):").pack(side=tk.LEFT, padx=5)
        self.payload_entry = ttk.Entry(cmd_frame)
        self.payload_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.payload_entry.insert(0, '{"func": "blink", "args": [3]}')
        
        self.send_btn = ttk.Button(cmd_frame, text="Send Instruction", command=self.send_command, state=tk.DISABLED)
        self.send_btn.pack(side=tk.LEFT, padx=5)

        # --- Status Bar ---
        self.status_bar = ttk.Label(self.root, text="Status: Disconnected", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)


    def log_message(self, text, prefix=""):
        # ... (this method is unchanged) ...
        def _do_log():
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            full_message = f"[{timestamp}] {prefix}{text}\n"
            
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, full_message)
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        
        self.root.after(0, _do_log)

    def scan_ports(self):
        # --- MODIFIED ---: This whole method is updated to use the database.
        self.log_message("Scanning for CircuitPython devices...")
        try:
            self.available_devices = find_data_comports()
            
            # Use get_device_name to create rich, descriptive names for the UI
            display_strings = []
            for p in self.available_devices:
                friendly_name = get_device_name(p['VID'], p['PID'])
                display_str = f"{friendly_name} - {p['port']} (VID:{p['VID']}, PID:{p['PID']})"
                display_strings.append(display_str)

            self.device_combo['values'] = display_strings
            if display_strings:
                self.device_combo.current(0)
                self.log_message(f"Found {len(display_strings)} device(s).")
            else:
                self.log_message("No devices found.")
                self.available_devices = []
        except Exception as e:
            self.log_message(f"Error scanning for ports: {e}", prefix="ERROR: ")
            self.available_devices = []

    def connect_device(self):
        # --- MODIFIED ---: Logic to get the port name is updated.
        selected_index = self.device_combo.current()

        if selected_index == -1:  # -1 means no item is selected
            self.log_message("No device selected.", prefix="ERROR: ")
            return

        # Retrieve the full device info using the index
        device_info = self.available_devices[selected_index]
        port = device_info['port']  # Extract just the port name for the connection
        
        if self.is_connected:
            self.log_message("Already connected.", prefix="WARNING: ")
            return

        try:
            self.log_message(f"Attempting to connect to {port}...")
            params = {"protocol": "serial", "port": port, "baudrate": 115200, "timeout": 0.1}
            self.postman = SerialPostman(params)
            self.postman.open_channel()
            
            time.sleep(1)
            self.postman.channel.reset_input_buffer()
            
            self.is_connected = True
            self.stop_thread.clear()
            
            self.worker_thread = threading.Thread(target=self._message_receiver_loop, daemon=True)
            self.worker_thread.start()
            
            self.connect_btn.config(state=tk.DISABLED)
            self.disconnect_btn.config(state=tk.NORMAL)
            self.send_btn.config(state=tk.NORMAL)
            self.device_combo.config(state=tk.DISABLED)
            self.scan_btn.config(state=tk.DISABLED)
            # Use the friendly name from the combobox for the status bar
            self.status_bar.config(text=f"Status: Connected to {self.device_combo.get()}")
            self.log_message(f"Successfully connected to {port}.")
        except Exception as e:
            self.log_message(f"Failed to connect: {e}", prefix="ERROR: ")
            if self.postman:
                self.postman.close_channel()
            self.postman = None
    
    # --- NO OTHER CHANGES ARE NEEDED BELOW THIS LINE ---
    
    def _message_receiver_loop(self):
        while not self.stop_thread.is_set():
            if self.postman and self.postman.is_open:
                try:
                    raw_data = self.postman.receive()
                    if raw_data:
                        try:
                            msg = Message.from_json(raw_data)
                            self.log_message(f"Received: {msg.to_dict()}", prefix="RECV: ")
                        except (json.JSONDecodeError, ValueError):
                            self.log_message(f"Received raw data: {raw_data}", prefix="RECV: ")
                except Exception as e:
                    self.log_message(f"Error in receive loop: {e}", prefix="ERROR: ")
                    self.stop_thread.set()
            
            time.sleep(0.05)
        
        self.log_message("Message receiver thread stopped.")

    def disconnect_device(self):
        if not self.is_connected:
            return

        self.log_message("Disconnecting...")
        self.stop_thread.set()
        if self.worker_thread:
            self.worker_thread.join(timeout=2)
        
        if self.postman:
            self.postman.close_channel()

        self.is_connected = False
        self.postman = None
        
        self.connect_btn.config(state=tk.NORMAL)
        self.disconnect_btn.config(state=tk.DISABLED)
        self.send_btn.config(state=tk.DISABLED)
        self.device_combo.config(state="readonly")
        self.scan_btn.config(state=tk.NORMAL)
        self.status_bar.config(text="Status: Disconnected")
        self.log_message("Disconnected successfully.")

    def send_command(self):
        if not self.is_connected:
            self.log_message("Not connected. Cannot send command.", prefix="ERROR: ")
            return

        payload_str = self.payload_entry.get()
        try:
            payload_dict = json.loads(payload_str)
            message = Message.create_message(
                subsystem_name="HOST",
                status="INSTRUCTION",
                payload=payload_dict
            )
            serialized_msg = message.serialize()
            self.postman.send(serialized_msg)
            self.log_message(f"Sent: {message.to_dict()}", prefix="SENT: ")
        except json.JSONDecodeError:
            self.log_message(f"Invalid JSON in payload: {payload_str}", prefix="ERROR: ")
        except Exception as e:
            self.log_message(f"Failed to send command: {e}", prefix="ERROR: ")

    def on_closing(self):
        if self.is_connected:
            self.disconnect_device()
        self.root.destroy()

if __name__ == "__main__":
    app_root = tk.Tk()
    gui = SimpleHostGUI(app_root)
    app_root.mainloop()