import tkinter as tk
from tkinter import ttk, scrolledtext
import json
import threading
import time
from datetime import datetime
# Assuming these imports are correct for your project structure
from ..firmware_db import get_device_name
from communicate.host_utilities import find_data_comports
from communicate.serial_postman import SerialPostman
from shared_lib.messages import Message
import re

class LogLevel:
    INFO = "INFO"
    ERROR = "ERROR"
    WARNING = "WARNING"
    SENT = "SENT"
    RECV = "RECV"
    RECV_SUCCESS = "RECV_SUCCESS"
    RECV_PROBLEM = "RECV_PROBLEM"
    RECV_TELEMETRY = "RECV_TELEMETRY"


class SimpleHostGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Self-Driving Lab: Host Interface")
        self.root.geometry("850x750")

        # --- State Variables ---
        self.postman = None
        self.is_connected = False
        self.worker_thread = None
        self.stop_thread = threading.Event()
        self.available_devices = []

        # --- UI Setup ---
        self._configure_styles()
        self._create_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.after(100, self.scan_ports)

    def _configure_styles(self):
        style = ttk.Style()
        style.configure("TLabelFrame", padding=10)
        style.configure("TButton", padding=5)
        style.configure("TEntry", padding=5)
        
        self.log_text_tags = {
            LogLevel.INFO: {"foreground": "black"},
            LogLevel.ERROR: {"foreground": "red", "font": "Helvetica 9 bold"},
            LogLevel.WARNING: {"foreground": "orange"},
            LogLevel.SENT: {"foreground": "blue"},
            LogLevel.RECV: {"foreground": "dark slate gray"}, 
            LogLevel.RECV_SUCCESS: {"foreground": "green"},
            LogLevel.RECV_PROBLEM: {"foreground": "red"},
            LogLevel.RECV_TELEMETRY: {"foreground": "grey"},
        }

    # --- MODIFIED: Reordered frames and adjusted row expansion ---
    def _create_widgets(self):
        self.root.columnconfigure(0, weight=1)
        # The log frame is now at row 3
        self.root.rowconfigure(3, weight=1) 

        self._create_connection_frame()
        self._create_command_info_frame()
        self._create_command_frame() # Moved up
        self._create_log_frame()
        self._create_status_bar()

    def _create_connection_frame(self):
        conn_frame = ttk.LabelFrame(self.root, text="Connection")
        conn_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        conn_frame.columnconfigure(1, weight=1)

        ttk.Label(conn_frame, text="Available Devices:").grid(row=0, column=0, padx=5, pady=5)
        self.device_combo = ttk.Combobox(conn_frame, state="readonly")
        self.device_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        self.scan_btn = ttk.Button(conn_frame, text="Scan", command=self.scan_ports)
        self.scan_btn.grid(row=0, column=2, padx=5, pady=5)
        
        self.connect_btn = ttk.Button(conn_frame, text="Connect", command=self.connect_device)
        self.connect_btn.grid(row=0, column=3, padx=5, pady=5)
        
        self.disconnect_btn = ttk.Button(conn_frame, text="Disconnect", command=self.disconnect_device, state=tk.DISABLED)
        self.disconnect_btn.grid(row=0, column=4, padx=5, pady=5)

    def _create_command_info_frame(self):
        info_frame = ttk.LabelFrame(self.root, text="Available Device Commands")
        info_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        info_frame.columnconfigure(0, weight=1)
        info_frame.rowconfigure(0, weight=1)

        cols = ("Command", "Description", "Arguments")
        self.command_tree = ttk.Treeview(info_frame, columns=cols, show='headings', height=5)
        
        for col in cols: self.command_tree.heading(col, text=col)
        self.command_tree.column("Command", width=120)
        self.command_tree.column("Description", width=300)
        self.command_tree.column("Arguments", width=200)

        scrollbar = ttk.Scrollbar(info_frame, orient=tk.VERTICAL, command=self.command_tree.yview)
        self.command_tree.configure(yscroll=scrollbar.set)

        self.command_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

    # --- MODIFIED: This entire method is redesigned ---
    def _create_command_frame(self):
        cmd_frame = ttk.LabelFrame(self.root, text="Send Command")
        cmd_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        cmd_frame.columnconfigure(1, weight=1) # Arg entry should expand

        # Function Entry
        ttk.Label(cmd_frame, text="Function:").grid(row=0, column=0, padx=(0,5), pady=5, sticky="w")
        self.func_entry = ttk.Entry(cmd_frame)
        self.func_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.func_entry.insert(0, 'blink')

        # Arguments Entry
        ttk.Label(cmd_frame, text="Arguments:").grid(row=1, column=0, padx=(0,5), pady=5, sticky="w")
        self.args_entry = ttk.Entry(cmd_frame)
        self.args_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        # Updated placeholder to show the new key:value format
        self.args_entry.insert(0, 'count:3, delay:250')
        
        # Send Button
        self.send_btn = ttk.Button(cmd_frame, text="Send", command=self.send_command, state=tk.DISABLED)
        self.send_btn.grid(row=0, column=2, rowspan=2, padx=5, pady=5, sticky="ns")

    # --- MODIFIED: Grid row updated ---
    def _create_log_frame(self):
        log_frame = ttk.LabelFrame(self.root, text="Incoming Messages")
        log_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=5)
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)

        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state=tk.DISABLED)
        self.log_text.grid(row=0, column=0, sticky="nsew")

        clear_btn = ttk.Button(log_frame, text="Clear Log", command=self.clear_log)
        clear_btn.grid(row=1, column=0, sticky="e", pady=5)
        
        for tag_name, config in self.log_text_tags.items(): self.log_text.tag_config(tag_name, **config)

    # --- MODIFIED: Grid row updated ---
    def _create_status_bar(self):
        self.status_bar = ttk.Label(self.root, text="Status: Disconnected", relief=tk.SUNKEN, anchor=tk.W, padding=5)
        self.status_bar.grid(row=4, column=0, sticky="ew")

    # ... log_message, clear_log, and scanning methods are unchanged ...
    def log_message(self, text, level=LogLevel.INFO):
        def _do_log():
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            prefix_map = { LogLevel.INFO: "[INFO] ", LogLevel.ERROR: "[ERROR] ", LogLevel.WARNING: "[WARNING] ",}
            prefix = prefix_map.get(level, "")
            full_message = f"[{timestamp}] {prefix}{text}\n"
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, full_message, level)
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        self.root.after(0, _do_log)

    def clear_log(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete('1.0', tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.log_message("Log cleared.")

    def scan_ports(self):
        self.log_message("Scanning for CircuitPython devices...")
        self.scan_btn.config(state=tk.DISABLED)
        self.device_combo.set("Scanning...")
        scan_thread = threading.Thread(target=self._perform_scan, daemon=True)
        scan_thread.start()

    def _perform_scan(self):
        try:
            self.available_devices = find_data_comports()
            display_strings = []
            for p in self.available_devices:
                friendly_name = get_device_name(p['VID'], p['PID'])
                display_str = f"{friendly_name} - {p['port']} (VID:{p['VID']}, PID:{p['PID']})"
                display_strings.append(display_str)
            self.root.after(0, self._update_device_list, display_strings)
        except Exception as e:
            self.log_message(f"Error scanning for ports: {e}", level=LogLevel.ERROR)
            self.root.after(0, self._update_device_list, [])

    def _update_device_list(self, display_strings):
        self.device_combo['values'] = display_strings
        if display_strings:
            self.device_combo.current(0)
            self.log_message(f"Scan complete. Found {len(display_strings)} device(s).")
        else:
            self.device_combo.set("")
            self.log_message("Scan complete. No devices found.")
        self.scan_btn.config(state=tk.NORMAL)

    def connect_device(self):
        selected_index = self.device_combo.current()
        if selected_index == -1:
            self.log_message("No device selected.", level=LogLevel.ERROR)
            return
        device_info = self.available_devices[selected_index]
        port = device_info['port']
        if self.is_connected:
            self.log_message("Already connected.", level=LogLevel.WARNING)
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
            self.status_bar.config(text=f"Status: Connected to {self.device_combo.get()}")
            self.log_message(f"Successfully connected to {port}.")
            self._send_help_command()
            self._set_remote_time()
        except Exception as e:
            self.log_message(f"Failed to connect: {e}", level=LogLevel.ERROR)
            if self.postman:
                self.postman.close_channel()
            self.postman = None
    
    # ... message receiver loop is unchanged ...
    def _message_receiver_loop(self):
        while not self.stop_thread.is_set():
            if self.postman and self.postman.is_open:
                try:
                    raw_data = self.postman.receive()
                    if raw_data:
                        try:
                            msg = Message.from_json(raw_data)
                            msg_dict = msg.to_dict()
                            status = msg_dict.get('status', '').upper()
                            payload = msg_dict.get('payload', {})
                            is_command_list = False
                            if status == "SUCCESS" and isinstance(payload, dict) and payload:
                                first_value = next(iter(payload.values()))
                                if isinstance(first_value, dict) and 'description' in first_value:
                                    is_command_list = True
                            if is_command_list:
                                self.root.after(0, self._populate_command_info, payload)
                            log_level = LogLevel.RECV
                            if status == "SUCCESS": log_level = LogLevel.RECV_SUCCESS
                            elif status == "PROBLEM": log_level = LogLevel.RECV_PROBLEM
                            elif status == "TELEMETRY": log_level = LogLevel.RECV_TELEMETRY
                            self.log_message(f"Received: {msg_dict}", level=log_level)
                        except (json.JSONDecodeError, ValueError):
                            self.log_message(f"Received raw data: {raw_data}", level=LogLevel.RECV)
                except Exception as e:
                    self.log_message(f"Error in receive loop: {e}", level=LogLevel.ERROR)
                    self.stop_thread.set()
            time.sleep(0.05)
        self.log_message("Message receiver thread stopped.")

    # --- MODIFIED: The main command sending logic is now here ---
    def send_command(self):
        if not self.is_connected:
            self.log_message("Not connected. Cannot send command.", level=LogLevel.ERROR)
            return

        func_name = self.func_entry.get().strip()
        if not func_name:
            self.log_message("Function name cannot be empty.", level=LogLevel.ERROR)
            return

        args_str = self.args_entry.get().strip()
        args_dict = {}

        # Parse arguments string into a dictionary
        if args_str:
            try:
                # Add quotes around unquoted keys to make the string valid JSON.
                # This regex finds identifiers followed by a colon.
                json_compatible_args = re.sub(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'"\1":', args_str)
                full_json_str = f"{{{json_compatible_args}}}"
                args_dict = json.loads(full_json_str)
            except json.JSONDecodeError as e:
                self.log_message(
                    f"Invalid arguments format. Use comma-separated 'key:value' pairs. "
                    f"Values must be valid JSON (e.g., count:5, message:\"hello\"). Error: {e}",
                    level=LogLevel.ERROR
                )
                return
        
        # Construct the payload with the arguments dictionary and send
        payload_dict = {"func": func_name, "args": args_dict}
        self._send_message(payload_dict)
        


    def _send_help_command(self):
        self.log_message("Requesting command list from device...")
        help_payload = {"func": "help", "args": []}
        self._send_message(help_payload)

    def _set_remote_time(self):
        self.log_message("Setting the microcontrollers time...")
        time_payload = {"func": "set_time", "args":{"epoch_seconds":time.time()}}
        self._send_message(time_payload)

    def _send_message(self, payload_dict):
        try:
            message = Message.create_message(
                subsystem_name="HOST",
                status="INSTRUCTION",
                payload=payload_dict
            )
            serialized_msg = message.serialize()
            self.postman.send(serialized_msg)
            self.log_message(f"Sent: {message.to_dict()}", level=LogLevel.SENT)
        except Exception as e:
            self.log_message(f"Failed to send command: {e}", level=LogLevel.ERROR)

    # ... disconnect and other helper methods are unchanged ...
    def disconnect_device(self):
        if not self.is_connected:
            return
        self.log_message("Disconnecting...")
        self.stop_thread.set()
        if self.worker_thread: self.worker_thread.join(timeout=2)
        if self.postman: self.postman.close_channel()
        self._clear_command_info()
        self.is_connected = False
        self.postman = None
        self.connect_btn.config(state=tk.NORMAL)
        self.disconnect_btn.config(state=tk.DISABLED)
        self.send_btn.config(state=tk.DISABLED)
        self.device_combo.config(state="readonly")
        self.scan_btn.config(state=tk.NORMAL)
        self.status_bar.config(text="Status: Disconnected")
        self.log_message("Disconnected successfully.")

    def _populate_command_info(self, commands_dict):
        self._clear_command_info()
        try:
            for name, details in commands_dict.items():
                desc = details.get('description', 'N/A')
                args = details.get('args', [])
                args_str = ", ".join(map(str, args)) if args else "None"
                self.command_tree.insert("", tk.END, values=(name, desc, args_str))
        except Exception as e:
            self.log_message(f"Could not parse command info: {e}", level=LogLevel.ERROR)

    def _clear_command_info(self):
        for item in self.command_tree.get_children():
            self.command_tree.delete(item)

    def on_closing(self):
        if self.is_connected: self.disconnect_device()
        self.root.destroy()

if __name__ == "__main__":
    app_root = tk.Tk()
    gui = SimpleHostGUI(app_root)
    app_root.mainloop()