import tkinter as tk
import logging
from host_app.core.device_manager import DeviceManager
from host_app.gui.mvc_view import MvcGui

def main():
    # Configure root logger for the application
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(name)-18s] %(levelname)-8s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    log = logging.getLogger(__name__)
    log.info("Starting MVC Host Application...")

    # 1. Create the backend DeviceManager instance
    manager = DeviceManager()

    # 2. Create the Tkinter root window
    root = tk.Tk()

    # 3. Create the GUI View, injecting the manager into it
    app = MvcGui(root, manager)

    # 4. Start the Tkinter event loop
    root.mainloop()
    
    log.info("Application has been closed.")

if __name__ == "__main__":
    main()