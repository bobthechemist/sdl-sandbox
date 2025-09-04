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
    """
    The 'Motion Engine' state. It executes a planned move from a start point
    to a target point in a non-blocking way.
    """
    @property
    def name(self): return 'Moving'

    def enter(self, machine):
        """
        Called once on entry. This is where we plan the entire move.
        """
        super().enter(machine)
        
        # 1. Read start and target positions from the machine's flags
        start_m1 = machine.flags['current_m1_steps']
        start_m2 = machine.flags['current_m2_steps']
        self.target_m1 = machine.flags['target_m1_steps']
        self.target_m2 = machine.flags['target_m2_steps']
        
        machine.log.info(f"Moving from ({start_m1}, {start_m2}) to ({self.target_m1}, {self.target_m2}).")

        # 2. Calculate the plan: steps and direction for each motor
        delta_m1 = self.target_m1 - start_m1
        delta_m2 = self.target_m2 - start_m2
        
        self.steps_left_m1 = abs(delta_m1)
        self.steps_left_m2 = abs(delta_m2)
        
        # Set motor direction pins (True/False may need to be adjusted for your wiring)
        machine.hardware['motor1_dir'].value = True if delta_m1 > 0 else False
        machine.hardware['motor2_dir'].value = True if delta_m2 > 0 else False

        # 3. Enable the motors
        machine.hardware['motor1_enable'].value = False
        machine.hardware['motor2_enable'].value = False
        time.sleep(0.01) # Short delay to ensure drivers are fully enabled

    def update(self, machine):
        """
        Called on every loop. This is the core stepper pulse generator.
        This is a simple implementation that steps both motors on each loop.
        A more advanced version would use Bresenham's algorithm for smoother lines.
        """
        super().update(machine)
        
        # Check for unexpected endstops (Safety First!)
        # Note: Endstop value is False when pressed due to Pull.UP
        if not machine.hardware['endstop_m1'].value or not machine.hardware['endstop_m2'].value:
            machine.hardware['motor1_enable'].value = True # Immediately disable motors
            machine.hardware['motor2_enable'].value = True
            machine.flags['is_homed'] = False # We no longer know our position
            machine.flags['error_message'] = "FAULT: Endstop triggered during move!"
            machine.go_to_state('Error')
            return # Stop processing immediately

        move_is_done = True
        
        # Pulse Motor 1 if it still has steps to go
        if self.steps_left_m1 > 0:
            step_pin = machine.hardware['motor1_step']
            step_pin.value = True
            step_pin.value = False # This pulse is very short
            self.steps_left_m1 -= 1
            move_is_done = False
        
        # Pulse Motor 2 if it still has steps to go
        if self.steps_left_m2 > 0:
            step_pin = machine.hardware['motor2_step']
            step_pin.value = True
            step_pin.value = False
            self.steps_left_m2 -= 1
            move_is_done = False
            
        # If both motors have completed their moves
        if move_is_done:
            # Update the final position in the machine's flags
            machine.flags['current_m1_steps'] = self.target_m1
            machine.flags['current_m2_steps'] = self.target_m2

            # Use the State Sequencer to decide where to go next
            next_state = machine.flags.get('on_move_complete', 'Idle')
            machine.flags['on_move_complete'] = None # Clear the flag for the next command
            
            machine.log.info(f"Move complete. Transitioning to '{next_state}'.")
            machine.go_to_state(next_state)

    def exit(self, machine):
        """
        Called once on exit. Ensures motors are disabled to save power.
        """
        super().exit(machine)
        machine.hardware['motor1_enable'].value = True
        machine.hardware['motor2_enable'].value = True

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