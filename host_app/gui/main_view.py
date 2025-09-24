import tkinter as tk
from tkinter import ttk, scrolledtext
import queue
from datetime import datetime
import re
import time
import json

from ..core.device_manager import DeviceManager
from ..core.device import Device
from shared_lib.messages import Message

class LogLevel:
    """Helper class to define styles and tags for log messages."""
    INFO = "INFO"
    ERROR = "ERROR"
    WARNING = "WARNING"
    SENT = "SENT"
    RECV = "RECV"
    RECV_SUCCESS = "RECV_SUCCESS"
    RECV_PROBLEM = "RECV_PROBLEM"
    RECV_TELEMETRY = "RECV_TELEMETRY"

class MainView:
    """The main 'View' of the MVC application. This class is only responsible for the UI."""
    # --- THIS IS THE FIX ---
    # The __init__ method was missing from the class definition.
    def __init__(self, root: tk.Tk, manager: DeviceManager):
        self.root = root
        self.manager = manager
        self.root.title("SDL Host - MVC")
        self.root.geometry("900x800")

        # --- UI State ---
        self.selected_device_port = None
        self.connected_device_ports = []

        # --- Tkinter Display Variables ---
        self.dv_firmware_name = tk.StringVar(value="N/A")
        self.dv_version = tk.StringVar(value="N/A")
        self.dv_state = tk.StringVar(value="Disconnected")
        self.dv_is_homed = tk.StringVar(value="N/A")
        self.command_details = {}
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
        self._configure_styles()
        self._create_widgets()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.after(250, self._periodic_update) # Start the main UI update loop

    def _configure_styles(self):
        style = ttk.Style()
        style.configure("TLabelFrame", padding=10)
        style.configure("TButton", padding=5)
        style.configure("TEntry", padding=5)

    def _create_widgets(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(4, weight=1)

        self._create_connection_frame()
        self._create_status_panel()
        self._create_command_info_frame()
        self._create_command_frame()
        self._create_log_frame()
        self._create_status_bar()

    def _create_connection_frame(self):
        frame = ttk.LabelFrame(self.root, text="Device Connections")
        frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Select Device:").grid(row=0, column=0, padx=5, pady=5)
        self.device_combo = ttk.Combobox(frame, state="readonly")
        self.device_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.device_combo.bind("<<ComboboxSelected>>", self._on_device_selected)
        
        self.scan_btn = ttk.Button(frame, text="Scan & Connect All", command=self._scan_and_connect)
        self.scan_btn.grid(row=0, column=2, padx=5, pady=5)

    def _create_status_panel(self):
        frame = ttk.LabelFrame(self.root, text="Device Status")
        frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        
        ttk.Label(frame, text="Firmware:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(frame, textvariable=self.dv_firmware_name).grid(row=0, column=1, sticky="w", padx=5, pady=2)
        
        ttk.Label(frame, text="Version:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(frame, textvariable=self.dv_version).grid(row=1, column=1, sticky="w", padx=5, pady=2)

        ttk.Label(frame, text="State:").grid(row=0, column=2, sticky="w", padx=20, pady=2)
        ttk.Label(frame, textvariable=self.dv_state).grid(row=0, column=3, sticky="w", padx=5, pady=2)

        ttk.Label(frame, text="Homed:").grid(row=1, column=2, sticky="w", padx=20, pady=2)
        ttk.Label(frame, textvariable=self.dv_is_homed).grid(row=1, column=3, sticky="w", padx=5, pady=2)

    def _create_command_info_frame(self):
        frame = ttk.LabelFrame(self.root, text="Available Commands")
        frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        frame.columnconfigure(0, weight=1); frame.rowconfigure(0, weight=1)
        cols = ("Command", "Description", "Arguments")
        self.command_tree = ttk.Treeview(frame, columns=cols, show='headings', height=5)
        for col in cols: self.command_tree.heading(col, text=col)
        self.command_tree.column("Command", width=120)
        self.command_tree.column("Description", width=350)
        self.command_tree.column("Arguments", width=300)
        self.command_tree.grid(row=0, column=0, sticky="nsew")
        self.command_tree.bind("<Double-1>", self._on_command_double_click)

    def _create_command_frame(self):
        frame = ttk.LabelFrame(self.root, text="Send Command")
        frame.grid(row=3, column=0, sticky="ew", padx=10, pady=5)
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text="Function:").grid(row=0, column=0, sticky="w", padx=5)
        self.func_entry = ttk.Entry(frame)
        self.func_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        ttk.Label(frame, text="Arguments:").grid(row=1, column=0, sticky="w", padx=5)
        self.args_entry = ttk.Entry(frame)
        self.args_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        self.send_btn = ttk.Button(frame, text="Send", command=self.send_command, state=tk.DISABLED)
        self.send_btn.grid(row=0, column=2, rowspan=2, padx=5, pady=5, sticky="ns")

    def _create_log_frame(self):
        frame = ttk.LabelFrame(self.root, text="Raw Message Log")
        frame.grid(row=4, column=0, sticky="nsew", padx=10, pady=5)
        frame.columnconfigure(0, weight=1); frame.rowconfigure(0, weight=1)
        self.log_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, state=tk.DISABLED)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        # Configure all the tag styles you defined earlier
        for tag, config in self.log_text_tags.items():
            self.log_text.tag_config(tag, **config)

    def _create_status_bar(self):
        self.status_bar = ttk.Label(self.root, text="Status: No devices connected.", relief=tk.SUNKEN)
        self.status_bar.grid(row=5, column=0, sticky="ew")

    def _periodic_update(self):
        self._update_device_list()
        
        if self.selected_device_port:
            device = self.manager.devices.get(self.selected_device_port)
            if device:
                self._update_status_panel(device)

        self._process_log_queue()
        self.root.after(250, self._periodic_update)

    def _update_device_list(self):
        manager_ports = list(self.manager.devices.keys())
        if manager_ports != self.connected_device_ports:
            self.connected_device_ports = manager_ports
            self.device_combo['values'] = self.connected_device_ports
            if self.selected_device_port not in self.connected_device_ports:
                self.device_combo.set("")
                self._on_device_selected(None)
            if self.connected_device_ports and not self.selected_device_port:
                self.device_combo.current(0)
                self._on_device_selected(None)
            self.status_bar.config(text=f"Connected Devices: {len(self.connected_device_ports)}")

    def _on_device_selected(self, event):
        port = self.device_combo.get()
        if not port:
            self.selected_device_port = None
            self._clear_command_info()
            self.send_btn.config(state=tk.DISABLED)
            return

        self.selected_device_port = port
        device = self.manager.devices.get(port)
        if device:
            self._populate_command_info(device.supported_commands)
            self.send_btn.config(state=tk.NORMAL)
            self.root.after(100, lambda: self._send_command_to_device(port, "get_info"))
            self.root.after(200, lambda: self._send_command_to_device(port, "help"))

    def _on_command_double_click(self, event):
        """
        Handles the double-click event on the command Treeview.
        Populates the function entry box with the selected command.
        """
        # Identify the unique ID of the row that was clicked on
        item_id = self.command_tree.identify_row(event.y)
        
        # If the click was not on an actual item, do nothing
        if not item_id:
            return

        # Get the dictionary of data for the clicked row
        item_data = self.command_tree.item(item_id)
        
        # The 'values' key holds a list of the cell contents for that row.
        # The first item in that list (index 0) is the command name.
        command_name = item_data['values'][0]

        # Clear the function entry box and insert the new command name
        self.func_entry.delete(0, tk.END)
        self.func_entry.insert(0, command_name)
        details = self.command_details.get(command_name)
        if not details:
            return

        args_list = details.get('args', [])
        template_parts = []
        for arg in args_list:
            arg_name = arg['name']
            
            # Use the default value if it exists, otherwise use a placeholder
            value = arg.get('default')
            if value is None:
                # Use a descriptive placeholder
                value_placeholder = f"<{arg.get('type', 'value')}>"
            else:
                value_placeholder = value

            # IMPORTANT: Wrap string types in the required double quotes for the user
            if arg.get('type') == 'str' and not (isinstance(value_placeholder, str) and value_placeholder.startswith('"')):
                value_str = f'"{value_placeholder}"'
            else:
                value_str = str(value_placeholder)

            template_parts.append(f"{arg_name}:{value_str}")
        
        final_template = ", ".join(template_parts)

        # Populate the arguments entry
        self.args_entry.delete(0, tk.END)
        self.args_entry.insert(0, final_template)

    def _update_status_panel(self, device: Device):
        self.dv_firmware_name.set(f"{device.friendly_name} ({device.firmware_name})")
        self.dv_version.set(device.version)
        self.dv_state.set(device.current_state)
        is_homed = device.status_info.get('homed', 'N/A')
        self.dv_is_homed.set(str(is_homed))



    def _scan_and_connect(self):
        self.log_message("Scanning for all available devices...")
        available = self.manager.scan_for_devices()
        if not available:
            self.log_message("No new devices found.")
            return

        newly_connected_ports = []
        for dev_info in available:
            port, vid, pid = dev_info['port'], dev_info['VID'], dev_info['PID']
            
            # Only attempt to connect if we are not already managing this port
            if port not in self.manager.devices:
                self.log_message(f"Found new device on {port}. Attempting to connect...")
                
                if self.manager.connect_device(port, vid, pid):
                    # If connection is successful, add to our list for post-processing
                    newly_connected_ports.append(port)
                else:
                    self.log_message(f"Failed to connect to {port}.", level=LogLevel.ERROR)

        if not newly_connected_ports:
            self.log_message("Scan complete. No new connections were established.")
            return

        # After connecting, send initial setup commands to each new device
        self.log_message(f"Sending setup commands to {len(newly_connected_ports)} new device(s)...")
        for port in newly_connected_ports:
            # Use root.after to schedule these commands. This gives the device
            # time to initialize and prevents the UI from freezing.
            # We use a robust lambda to capture the port variable correctly.
            self.root.after(200, lambda p=port: self._send_command_to_device(p, "get_info"))
            self.root.after(400, lambda p=port: self._send_command_to_device(p, "help"))

    def send_command(self):
        port = self.selected_device_port
        if not port:
            self.log_message("No device selected. Cannot send command.", level=LogLevel.ERROR)
            return

        func = self.func_entry.get().strip()
        if not func:
            self.log_message("Function name cannot be empty.", level=LogLevel.ERROR)
            return
            
        args_str = self.args_entry.get().strip()
        args_dict = {}

        if args_str:
            # --- START: MODIFIED PARSING LOGIC ---
            full_json_str = "" # Define here to be available in the except block
            try:
                # The user MUST use double quotes for string values.
                # Example: pump:"p1", vol:10
                json_compatible_args = re.sub(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'"\1":', args_str)
                full_json_str = f"{{{json_compatible_args}}}"
                args_dict = json.loads(full_json_str)
            except json.JSONDecodeError as e:
                # --- FIX: Log the generated string that failed to parse ---
                error_msg = (
                    f"Invalid arguments format. Use comma-separated key:value pairs. "
                    f"IMPORTANT: String values MUST be in double quotes (e.g., pump:\"p1\").\n"
                    f"    - Attempted to parse: {full_json_str}\n"
                    f"    - Parser error: {e}"
                )
                self.log_message(error_msg, level=LogLevel.ERROR)
                return
            # --- END: MODIFIED PARSING LOGIC ---

        self._send_command_to_device(port, func, args_dict)

    def _send_command_to_device(self, port, func, args=None):
        payload = {"func": func, "args": args if args is not None else {}}
        message = Message(subsystem_name="HOST_MVC", status="INSTRUCTION", payload=payload)
        self.manager.send_message(port, message)

    def _process_log_queue(self):
        while not self.manager.incoming_message_queue.empty():
            try:
                msg_type, port, data = self.manager.incoming_message_queue.get_nowait()

                # --- START: MODIFIED LOGIC ---
                if msg_type == 'SENT':
                    self.log_message(f"[{port}] Sent: {data.to_dict()}", level=LogLevel.SENT)
                
                elif msg_type == 'RECV':
                    # For received messages, we choose a color based on the message status
                    msg_dict = data.to_dict()
                    status = msg_dict.get('status', '').upper()
                    
                    log_level = LogLevel.RECV # Default for INFO, DEBUG, etc.
                    if status in ("SUCCESS", "DATA_RESPONSE"):
                        log_level = LogLevel.RECV_SUCCESS
                    elif status == "PROBLEM":
                        log_level = LogLevel.RECV_PROBLEM
                    elif status == "TELEMETRY":
                        log_level = LogLevel.RECV_TELEMETRY
                    elif status == "WARNING":
                        log_level = LogLevel.WARNING

                    self.log_message(f"[{port}] Recv: {msg_dict}", level=log_level)
                    
                    # Also update the model
                    device = self.manager.devices.get(port)
                    if device:
                        device.update_from_message(data)

                elif msg_type == 'RAW':
                    self.log_message(f"[{port}] Recv Raw: {data}", level=LogLevel.WARNING)
                
                elif msg_type == 'ERROR':
                    self.log_message(f"[{port}] Listener Error: {data}", level=LogLevel.ERROR)
                # --- END: MODIFIED LOGIC ---

            except queue.Empty:
                pass

    def log_message(self, text, level=LogLevel.INFO):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{timestamp}] {text}\n", level)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _populate_command_info(self, commands_dict):
        self._clear_command_info()
        self.command_details = commands_dict
        
        for name, details in commands_dict.items():
            desc = details.get('description', 'N/A')
            
            args_list = details.get('args', [])
            if not args_list:
                args_str = "None"
            else:
                parts = []
                # --- START: ROBUST PARSING LOGIC ---
                for arg in args_list:
                    # Check if the argument is the NEW dictionary format
                    if isinstance(arg, dict):
                        part = f"{arg.get('name', '?')} ({arg.get('type', 'any')}"
                        if 'default' in arg:
                            part += f", default={arg['default']}"
                        part += ")"
                        parts.append(part)
                    # Check if the argument is the OLD string format
                    elif isinstance(arg, str):
                        parts.append(arg)
                # --- END: ROBUST PARSING LOGIC ---
                args_str = ", ".join(parts)
            
            self.command_tree.insert("", tk.END, values=(name, desc, args_str))

    def _clear_command_info(self):
        for item in self.command_tree.get_children():
            self.command_tree.delete(item)

    def on_closing(self):
        self.manager.stop()
        self.root.destroy()