# host/calibration/view_transects.py
import argparse
import json
import sys
import tkinter as tk
from tkinter import ttk
from pathlib import Path

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    from matplotlib.figure import Figure
except ImportError:
    print("Error: 'matplotlib' is required. Please run 'pip install matplotlib'")
    sys.exit(1)

class TransectViewer:
    def __init__(self, root, json_data, filename):
        self.root = root
        self.data = json_data
        self.filename = filename
        
        self.root.title(f"Transect Viewer - {filename}")
        self.root.geometry("1000x700")

        # Extract available channels from the first data point found
        self.channels = self._extract_channels()
        if not self.channels:
            print("Error: No spectral data found in the JSON file.")
            sys.exit(1)

        # Set default channel (prefer 'clear', else first available)
        self.current_channel = tk.StringVar()
        if 'clear' in self.channels:
            self.current_channel.set('clear')
        else:
            self.current_channel.set(self.channels[0])

        self._init_ui()
        self._plot_data()

    def _extract_channels(self):
        """Finds all available color channels in the dataset."""
        # Check M1 transect first
        m1_data = self.data.get('m1_transect', [])
        if m1_data and 'spectral_data' in m1_data[0]:
            return list(m1_data[0]['spectral_data'].keys())
        
        # Check M2 transect if M1 was empty
        m2_data = self.data.get('m2_transect', [])
        if m2_data and 'spectral_data' in m2_data[0]:
            return list(m2_data[0]['spectral_data'].keys())
            
        return []

    def _init_ui(self):
        # --- Control Frame (Top) ---
        control_frame = ttk.Frame(self.root, padding=10)
        control_frame.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(control_frame, text="Select Channel:").pack(side=tk.LEFT, padx=5)
        
        self.combo = ttk.Combobox(control_frame, textvariable=self.current_channel, values=self.channels, state="readonly")
        self.combo.pack(side=tk.LEFT, padx=5)
        self.combo.bind("<<ComboboxSelected>>", self._on_channel_change)

        # Display File Info
        target_well = self.data.get("target_well", "Unknown")
        center = self.data.get("center_steps", {})
        info_text = f"Target: {target_well} | Center: ({center.get('m1')}, {center.get('m2')})"
        ttk.Label(control_frame, text=info_text, font=("Arial", 10, "bold")).pack(side=tk.RIGHT, padx=10)

        # --- Plot Frame (Center) ---
        plot_frame = ttk.Frame(self.root)
        plot_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.ax = self.figure.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(self.figure, master=plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Matplotlib Toolbar
        toolbar = NavigationToolbar2Tk(self.canvas, plot_frame)
        toolbar.update()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def _on_channel_change(self, event):
        self._plot_data()

    def _plot_data(self):
        self.ax.clear()
        channel = self.current_channel.get()
        center = self.data.get("center_steps", {})
        center_m1 = center.get("m1", "N/A")
        center_m2 = center.get("m2", "N/A")

        # --- Process M1 Transect ---
        m1_offsets = []
        m1_values = []
        for point in self.data.get('m1_transect', []):
            m1_offsets.append(point['offset'])
            # Safely get intensity, default to 0 if missing
            val = point.get('spectral_data', {}).get(channel, 0)
            m1_values.append(val)

        if m1_offsets:
            label = f"M1 Scan (M2 fixed at {center_m2})"
            self.ax.plot(m1_offsets, m1_values, marker='o', linestyle='-', color='blue', label=label)

        # --- Process M2 Transect ---
        m2_offsets = []
        m2_values = []
        for point in self.data.get('m2_transect', []):
            m2_offsets.append(point['offset'])
            val = point.get('spectral_data', {}).get(channel, 0)
            m2_values.append(val)

        if m2_offsets:
            label = f"M2 Scan (M1 fixed at {center_m1})"
            self.ax.plot(m2_offsets, m2_values, marker='s', linestyle='--', color='red', label=label)

        # --- Formatting ---
        self.ax.set_title(f"Spectral Intensity Transect: Channel '{channel}'")
        self.ax.set_xlabel("Motor Steps Offset (from center)")
        self.ax.set_ylabel("Intensity")
        self.ax.grid(True, linestyle=':', alpha=0.6)
        self.ax.legend()
        
        # Add a vertical line at offset 0
        self.ax.axvline(x=0, color='black', linestyle='-', alpha=0.3)

        self.canvas.draw()

def main():
    parser = argparse.ArgumentParser(description="Visualize transect JSON data.")
    parser.add_argument("file", type=str, help="Path to the JSON data file.")
    args = parser.parse_args()

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: File '{args.file}' not found.")
        sys.exit(1)

    try:
        with open(file_path, 'r') as f:
            json_data = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON from '{args.file}'.")
        sys.exit(1)

    root = tk.Tk()
    app = TransectViewer(root, json_data, file_path.name)
    root.mainloop()

if __name__ == "__main__":
    main()