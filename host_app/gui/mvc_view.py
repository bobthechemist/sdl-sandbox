import tkinter as tk
from tkinter import ttk, scrolledtext
import json
import queue
from datetime import datetime
import re
import time

# Import from the new MVC architecture and shared libraries
from ..core.device_manager import DeviceManager
from ..firmware_db import get_device_name
from shared_lib.messages import Message

class LogLevel:
    """Helper class to define styles for log messages."""
    INFO = "INFO"
    ERROR = "ERROR"
    WARNING = "WARNING"
    SENT = "SENT"
    RECV = "RECV"
    RECV_SUCCESS = "RECV_SUCCESS"
    RECV_PROBLEM = "RECV_PROBLEM"
    RECV_TELEMETRY = "RECV_TELEMETRY"

class MvcGui:
    """
    The main 'View' of the MVC application.
    This class is responsible for the UI layout and event handling.
    """
    def __init__(self, root: tk.Tk, device_manager: DeviceManager):
        self.root = root
        self.device_manager = device_manager  # Injected dependency
        self.root.title("MVC Host Interface")
        self.root.geometry("850x750")

        self.available_devices = []
        self.selected_port = tk.StringVar()

        self._configure_styles()
        self._create_widgets()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.after(100, self.scan_ports)
        self.root.after(100, self.process_incoming_messages)

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

    def _create_widgets(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(3, weight=1) 
        self._create_connection_frame()
        self._create_command_info_frame()
        self._create_command_frame()
        self._create_log_frame()
        self._create_status_bar()

    def _create_connection_frame(self):
        # This UI creation code is correct and unchanged
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
        # This UI creation code is correct and unchanged
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

    def _create_command_frame(self):
        # This UI creation code is correct and unchanged
        cmd_frame = ttk.LabelFrame(self.root, text="Send Command")
        cmd_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        cmd_frame.columnconfigure(1, weight=1)
        ttk.Label(cmd_frame, text="Function:").grid(row=0, column=0, padx=(0,5), pady=5, sticky="w")
        self.func_entry = ttk.Entry(cmd_frame)
        self.func_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.func_entry.insert(0, 'help')
        ttk.Label(cmd_frame, text="Arguments:").grid(row=1, column=0, padx=(0,5), pady=5, sticky="w")
        self.args_entry = ttk.Entry(cmd_frame)
        self.args_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        self.send_btn = ttk.Button(cmd_frame, text="Send", command=self.send_command, state=tk.DISABLED)
        self.send_btn.grid(row=0, column=2, rowspan=2, padx=5, pady=5, sticky="ns")

    def _create_log_frame(self):
        # This UI creation code is correct and unchanged
        log_frame = ttk.LabelFrame(self.root, text="Message Log")
        log_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=5)
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state=tk.DISABLED)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        for tag_name, config in self.log_text_tags.items():
            self.log_text.tag_config(tag_name, **config)
        clear_btn = ttk.Button(log_frame, text="Clear Log", command=self.clear_log)
        clear_btn.grid(row=1, column=0, sticky="e", pady=5)

    def _create_status_bar(self):
        # This UI creation code is correct and unchanged
        self.status_bar = ttk.Label(self.root, text="Status: Disconnected", relief=tk.SUNKEN, anchor=tk.W, padding=5)
        self.status_bar.grid(row=4, column=0, sticky="ew")

    def process_incoming_messages(self):
        """Periodically checks the DeviceManager's queue and updates the UI."""
        try:
            while not self.device_manager.incoming_message_queue.empty():
                msg_type, port, data = self.device_manager.incoming_message_queue.get_nowait()
                
                if msg_type == 'SENT':
                    self.log_message(f"[{port}] Sent: {data.to_dict()}", LogLevel.SENT)
                elif msg_type == 'RECV':
                    self.handle_received_message(port, data)
                elif msg_type == 'RAW':
                    self.log_message(f"[{port}] Recv Raw: {data}", LogLevel.RECV)
                elif msg_type == 'ERROR':
                    self.log_message(f"[{port}] Listener Error: {data}", LogLevel.ERROR)
        finally:
            self.root.after(100, self.process_incoming_messages)

    # --- REVISED METHOD ---
    def handle_received_message(self, port, msg: Message):
        """Processes a parsed Message object and updates the UI accordingly."""
        msg_dict = msg.to_dict()
        status = msg_dict.get('status', '').upper()
        payload = msg_dict.get('payload', {})
        
        # Check if this is a response to the 'help' command.
        if status == 'DATA_RESPONSE':
            data_content = payload.get('data', {})
            # Heuristic to identify if this is a command list
            if (isinstance(data_content, dict) and data_content and
                isinstance(next(iter(data_content.values()), None), dict) and
                'description' in next(iter(data_content.values()), {})):
                
                # This is our command list. Populate the UI.
                self._populate_command_info(data_content)

        # Log the message with appropriate styling
        log_level = LogLevel.RECV
        if status in ("SUCCESS", "DATA_RESPONSE"):
            log_level = LogLevel.RECV_SUCCESS
        elif status == "PROBLEM":
            log_level = LogLevel.RECV_PROBLEM
        elif status == "TELEMETRY":
            log_level = LogLevel.RECV_TELEMETRY
            
        self.log_message(f"[{port}] Recv: {msg_dict}", log_level)

    def scan_ports(self):
        self.log_message("Scanning for devices...")
        self.available_devices = self.device_manager.scan_for_devices()
        display_strings = [
            f"{get_device_name(p['VID'], p['PID'])} - {p['port']}"
            for p in self.available_devices
        ]
        self._update_device_list(display_strings)
        self.log_message(f"Scan complete. Found {len(display_strings)} device(s).")

    def connect_device(self):
        selected_index = self.device_combo.current()
        if selected_index == -1:
            self.log_message("No device selected.", LogLevel.ERROR)
            return
        
        port = self.available_devices[selected_index]['port']
        self.selected_port.set(port)
        
        if self.device_manager.connect_device(port):
            self.log_message(f"Connection to {port} successful.")
            self.connect_btn.config(state=tk.DISABLED)
            self.disconnect_btn.config(state=tk.NORMAL)
            self.send_btn.config(state=tk.NORMAL)
            self.status_bar.config(text=f"Status: Connected to {port}")
            # Automatically query the device for its info after a short delay
            self.root.after(200, lambda: self._send_command_to_device(port, "get_info"))
            self.root.after(400, lambda: self._send_command_to_device(port, "help"))
            self.root.after(600, lambda: self._send_command_to_device(port, "set_time", {"epoch_seconds": int(time.time())}))

    def disconnect_device(self):
        port = self.selected_port.get()
        if not port: return
        
        self.device_manager.disconnect_device(port)
        self.log_message(f"Disconnected from {port}.")
        self.connect_btn.config(state=tk.NORMAL)
        self.disconnect_btn.config(state=tk.DISABLED)
        self.send_btn.config(state=tk.DISABLED)
        self.status_bar.config(text="Status: Disconnected")
        self.selected_port.set("")
        self._clear_command_info()

    def send_command(self):
        port = self.selected_port.get()
        if not port:
            self.log_message("No device selected.", LogLevel.ERROR)
            return

        func_name = self.func_entry.get().strip()
        if not func_name:
            self.log_message("Function name cannot be empty.", LogLevel.ERROR)
            return

        args_str = self.args_entry.get().strip()
        args_dict = {}
        if args_str:
            try:
                # Add quotes around unquoted keys to make the string valid JSON
                json_compatible_args = re.sub(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'"\1":', args_str)
                full_json_str = f"{{{json_compatible_args}}}"
                args_dict = json.loads(full_json_str)
            except json.JSONDecodeError as e:
                self.log_message(f"Invalid arguments format. Use 'key:value'. Error: {e}", LogLevel.ERROR)
                return
        
        self._send_command_to_device(port, func_name, args_dict)

    def _send_command_to_device(self, port, func, args=None):
        """Helper to construct and send a message via the manager."""
        payload = {"func": func, "args": args if args is not None else {}}
        message = Message.create_message(
            subsystem_name="HOST_MVC",
            status="INSTRUCTION",
            payload=payload
        )
        self.device_manager.send_message(port, message)

    def on_closing(self):
        self.device_manager.disconnect_all()
        self.root.destroy()

    def _update_device_list(self, display_strings):
        self.device_combo['values'] = display_strings
        if display_strings:
            self.device_combo.current(0)
        else:
            self.device_combo.set("")

    def log_message(self, text, level=LogLevel.INFO):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        full_message = f"[{timestamp}] {text}\n"
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, full_message, level)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def clear_log(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete('1.0', tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.log_message("Log cleared.")

    def _populate_command_info(self, commands_dict):
        self._clear_command_info()
        try:
            for name, details in commands_dict.items():
                desc = details.get('description', 'N/A')
                args = details.get('args', [])
                args_str = ", ".join(map(str, args)) if args else "None"
                self.command_tree.insert("", tk.END, values=(name, desc, args_str))
        except Exception as e:
            self.log_message(f"Could not parse command info: {e}", LogLevel.ERROR)

    def _clear_command_info(self):
        for item in self.command_tree.get_children():
            self.command_tree.delete(item)