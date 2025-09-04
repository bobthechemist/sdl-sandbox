# firmware/sidekick/states.py
# type: ignore
import time
import digitalio
from shared_lib.statemachine import State
from shared_lib.messages import Message
from firmware.common.common_states import listen_for_instructions

class Initialize(State):
    @property
    def name(self): return 'Initialize'
    def enter(self, machine):
        super().enter(machine)
        try:
            # Create a dictionary of all hardware objects for easy access
            machine.hardware = {}
            pin_config = machine.config['pins']
            
            # Setup Motors and Endstops
            for i in [1, 2]:
                machine.hardware[f'motor{i}_step'] = digitalio.DigitalInOut(pin_config[f'motor{i}_step'])
                machine.hardware[f'motor{i}_step'].direction = digitalio.Direction.OUTPUT
                machine.hardware[f'motor{i}_dir'] = digitalio.DigitalInOut(pin_config[f'motor{i}_dir'])
                machine.hardware[f'motor{i}_dir'].direction = digitalio.Direction.OUTPUT
                machine.hardware[f'motor{i}_enable'] = digitalio.DigitalInOut(pin_config[f'motor{i}_enable'])
                machine.hardware[f'motor{i}_enable'].direction = digitalio.Direction.OUTPUT
                machine.hardware[f'motor{i}_enable'].value = True # Start with motors disabled (HIGH = off for some drivers)

                machine.hardware[f'endstop_m{i}'] = digitalio.DigitalInOut(pin_config[f'endstop_m{i}'])
                machine.hardware[f'endstop_m{i}'].direction = digitalio.Direction.INPUT
                machine.hardware[f'endstop_m{i}'].pull = digitalio.Pull.UP
            
            # Setup Pumps
            machine.hardware['pumps'] = {}
            for i in [1, 2, 3, 4]:
                machine.hardware['pumps'][f'p{i}'] = digitalio.DigitalInOut(pin_config[f'pump{i}'])
                machine.hardware['pumps'][f'p{i}'].direction = digitalio.Direction.OUTPUT

            machine.log.info("Sidekick hardware initialized successfully.")
            machine.go_to_state('Homing') # The first action after init must be to home.
        except Exception as e:
            machine.flags['error_message'] = f"Hardware Initialization failed: {e}"
            machine.go_to_state('Error')

class Idle(State):
    @property
    def name(self): return 'Idle'
    def __init__(self, telemetry_callback=None):
        super().__init__()
        self._telemetry_callback = telemetry_callback
    def enter(self, machine):
        super().enter(machine)
        self._telemetry_interval = machine.flags.get('telemetry_interval', 5.0)
        self._next_telemetry_time = time.monotonic() + self._telemetry_interval
        machine.hardware['motor1_enable'].value = True # Disable motors to save power
        machine.hardware['motor2_enable'].value = True
    def update(self, machine):
        super().update(machine)
        listen_for_instructions(machine)
        if time.monotonic() >= self._next_telemetry_time:
            if self._telemetry_callback:
                self._telemetry_callback(machine)
            self._next_telemetry_time = time.monotonic() + self._telemetry_interval

class Homing(State):
    @property
    def name(self): return 'Homing'
    # This is a placeholder. A real implementation would be more complex,
    # moving one motor at a time and handling timeouts.
    def enter(self, machine):
        super().enter(machine)
        machine.log.info("Homing sequence started...")
        # For now, we will simulate a successful home.
        machine.flags['is_homed'] = True
        machine.flags['current_m1_steps'] = 0
        machine.flags['current_m2_steps'] = 0
        machine.log.info("Homing complete (simulated).")
        # In a real implementation, you would then move to the parking spot.
        machine.go_to_state('Idle')
    def update(self, machine):
        pass # The enter method does everything for this simple simulation

class Moving(State):
    @property
    def name(self): return 'Moving'
    # This is a placeholder. A real implementation would use trajectory
    # planning (e.g., Bresenham's algorithm) for smooth, coordinated motion.
    def enter(self, machine):
        super().enter(machine)
        self.target_m1 = machine.flags['target_m1_steps']
        self.target_m2 = machine.flags['target_m2_steps']
        machine.log.info(f"Moving to ({self.target_m1}, {self.target_m2})...")
        machine.hardware['motor1_enable'].value = False # Enable motors
        machine.hardware['motor2_enable'].value = False
    def update(self, machine):
        # For now, we will simulate arriving instantly.
        machine.flags['current_m1_steps'] = self.target_m1
        machine.flags['current_m2_steps'] = self.target_m2
        
        # --- The State Sequencer Logic ---
        next_state = machine.flags.get('on_move_complete', 'Idle')
        machine.flags['on_move_complete'] = None # Clear the flag
        
        machine.log.info(f"Move complete. Transitioning to '{next_state}'.")
        machine.go_to_state(next_state)

class Dispensing(State):
    @property
    def name(self): return 'Dispensing'
    def enter(self, machine):
        super().enter(machine)
        self.pump_key = machine.flags.get('dispense_pump')
        self.cycles_left = machine.flags.get('dispense_cycles')
        self.pump_pin = machine.hardware['pumps'][self.pump_key]
        self.pump_state = 'aspirating'
        self.timings = machine.config['pump_timings']
        
        machine.log.info(f"Dispensing {self.cycles_left} cycles from {self.pump_key}.")
        # Start the first aspirate cycle
        self.pump_pin.value = True
        self._next_toggle_time = time.monotonic() + self.timings['aspirate_time']

    def update(self, machine):
        if time.monotonic() >= self._next_toggle_time:
            if self.pump_state == 'aspirating':
                self.pump_pin.value = False
                self.pump_state = 'dispensing'
                self._next_toggle_time = time.monotonic() + self.timings['dispense_time']
                self.cycles_left -= 1
            elif self.pump_state == 'dispensing':
                if self.cycles_left > 0:
                    self.pump_pin.value = True
                    self.pump_state = 'aspirating'
                    self._next_toggle_time = time.monotonic() + self.timings['aspirate_time']
                else:
                    # We are finished
                    machine.log.info("Dispense complete.")
                    response = Message.create_message(
                        subsystem_name=machine.name,
                        status="SUCCESS",
                        payload={"pump": self.pump_key, "cycles": machine.flags.get('dispense_cycles')}
                    )
                    machine.postman.send(response.serialize())
                    machine.go_to_state('Idle')