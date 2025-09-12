# firmware/sidekick/states.py
# type: ignore
import time
import digitalio
from shared_lib.statemachine import State
from shared_lib.messages import Message
from firmware.common.common_states import listen_for_instructions
from . import kinematics

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
        machine.hardware['motor1_enable'].value = False 
        machine.hardware['motor2_enable'].value = False
    def update(self, machine):
        super().update(machine)
        listen_for_instructions(machine)
        if time.monotonic() >= self._next_telemetry_time:
            if self._telemetry_callback:
                self._telemetry_callback(machine)
            self._next_telemetry_time = time.monotonic() + self._telemetry_interval

class Homing(State):
    """
    Homing procedure
    """
    @property
    def name(self): return 'Homing'

    def enter(self, machine):
        super().enter(machine)
        machine.log.info("Starting corrected homing routine...")
        machine.flags['is_homed'] = False

        # Load settings
        self._backoff_steps = machine.config['homing_settings']['joint_backoff_steps']
        self._max_homing_steps = machine.config['safe_limits']['m1_max_steps'] + 2000
        
        # Internal state management
        self._homing_stage = 'START_M1'
        self._steps_taken = 0
        self._step_delay = 1 / machine.config['motor_settings']['max_speed_sps']
        self._next_step_time = time.monotonic()

        machine.hardware['motor1_enable'].value = False
        machine.hardware['motor2_enable'].value = False

    def update(self, machine):
        super().update(machine)

        # --- Phase 1: Home M1 (CW) ---
        if self._homing_stage == 'START_M1':
            machine.log.info("Phase 1: Homing Motor 1 (CW) with M2 disabled.")
            machine.hardware['motor2_enable'].value = True
            machine.hardware['motor1_dir'].value = True
            self._steps_taken = 0
            self._homing_stage = 'RUNNING_M1'

        elif self._homing_stage == 'RUNNING_M1':
            if not machine.hardware['endstop_m1'].value:
                # ABSOLUTE POSITION DEFINED
                machine.flags['current_m1_steps'] = 0
                machine.log.info(f"M1 endstop reached. Position DEFINED as {machine.flags['current_m1_steps']} steps.")
                self._homing_stage = 'START_M2_JOINT'
                return
            
            # (Pulse and timeout logic remains the same)
            if time.monotonic() >= self._next_step_time:
                step_pin = machine.hardware['motor1_step']
                step_pin.value = True; step_pin.value = False
                self._steps_taken += 1
                self._next_step_time = time.monotonic() + self._step_delay
            if self._steps_taken > self._max_homing_steps:
                machine.flags['error_message'] = "FAULT: Homing timeout on Motor 1!"
                machine.go_to_state('Error')

        # --- Phase 2: Joint move to find M2 endstop (CCW) ---
        elif self._homing_stage == 'START_M2_JOINT':
            machine.log.info("Phase 2: Joint CCW move to find M2 endstop.")
            machine.hardware['motor2_enable'].value = False
            machine.hardware['motor1_dir'].value = False
            machine.hardware['motor2_dir'].value = False
            self._steps_taken = 0 # Timeout counter
            self._homing_stage = 'RUNNING_M2_JOINT'

        elif self._homing_stage == 'RUNNING_M2_JOINT':
            if not machine.hardware['endstop_m2'].value:
                # ABSOLUTE POSITION DEFINED
                machine.flags['current_m2_steps'] = 1600
                # M1's position is its starting point (0) plus the steps taken in this phase
                machine.flags['current_m1_steps'] = 0 + self._steps_taken
                machine.log.info(f"M2 endstop reached. Positions DEFINED as M1={machine.flags['current_m1_steps']}, M2={machine.flags['current_m2_steps']}.")
                self._homing_stage = 'START_JOINT_BACKOFF'
                return

            # (Pulse and timeout logic remains the same)
            if time.monotonic() >= self._next_step_time:
                m1_pin = machine.hardware['motor1_step']; m2_pin = machine.hardware['motor2_step']
                m1_pin.value = True; m2_pin.value = True
                m1_pin.value = False; m2_pin.value = False
                self._steps_taken += 1
                self._next_step_time = time.monotonic() + self._step_delay
            if self._steps_taken > self._max_homing_steps:
                machine.flags['error_message'] = "FAULT: Homing timeout on M2 joint move!"
                machine.go_to_state('Error')

        # --- Phase 3: Back off the endstop ---
        elif self._homing_stage == 'START_JOINT_BACKOFF':
            machine.log.info(f"Phase 3: Backing off endstop with joint move (CW) for {self._backoff_steps} steps.")
            machine.hardware['motor1_dir'].value = True
            machine.hardware['motor2_dir'].value = True
            self._steps_taken = self._backoff_steps
            self._homing_stage = 'RUNNING_JOINT_BACKOFF'

        elif self._homing_stage == 'RUNNING_JOINT_BACKOFF':
            if self._steps_taken > 0:
                # (Backoff pulse logic remains the same)
                 if time.monotonic() >= self._next_step_time:
                    m1_pin = machine.hardware['motor1_step']; m2_pin = machine.hardware['motor2_step']
                    m1_pin.value = True; m2_pin.value = True
                    m1_pin.value = False; m2_pin.value = False
                    self._steps_taken -= 1
                    self._next_step_time = time.monotonic() + self._step_delay
            else:
                # --- CORRECTED POSITION UPDATE ---
                # The new position is the old position MINUS the backoff steps.
                machine.flags['current_m1_steps'] -= self._backoff_steps
                machine.flags['current_m2_steps'] -= self._backoff_steps
                machine.log.info(f"Back-off complete. Final positions UPDATED to: M1={machine.flags['current_m1_steps']}, M2={machine.flags['current_m2_steps']}.")
                self._homing_stage = 'PREPARE_SAFE_MOVE'

        # --- Final Phase: Prepare for Safe Move (Logic is the same) ---
        elif self._homing_stage == 'PREPARE_SAFE_MOVE':
            machine.log.info("Physical homing successful. Calculating park position move.")
            machine.flags['is_homed'] = True
            
            # Read the absolute park coordinates from the config
            park_x = machine.config['homing_settings']['park_move_x']
            park_y = machine.config['homing_settings']['park_move_y']
            
            # Use inverse kinematics to find the angles for the park position
            target_angles = kinematics.inverse_kinematics(machine, park_x, park_y)
            
            if target_angles is None:
                # This should not happen if the park position is well-chosen, but it's a critical safety check.
                machine.flags['error_message'] = f"FATAL: Park position ({park_x}, {park_y}) is unreachable."
                machine.go_to_state('Error')
                return

            theta1, theta2 = target_angles
            target_m1_steps, target_m2_steps = kinematics.degrees_to_steps(machine, theta1, theta2)

            machine.log.info(f"Target park pos: (x={park_x}, y={park_y}) -> (m1={target_m1_steps}, m2={target_m2_steps}) steps.")

            # Set the flags for the 'Moving' state
            machine.flags['target_m1_steps'] = target_m1_steps
            machine.flags['target_m2_steps'] = target_m2_steps
            machine.flags['on_move_complete'] = 'Idle'

            # Send success message to host *before* starting the move
            response = Message.create_message(
                subsystem_name=machine.name, status="SUCCESS",
                payload={"detail": "Homing successful. Moving to park position."}
            )
            machine.postman.send(response.serialize())
            machine.go_to_state('Moving')

    def exit(self, machine):
        super().exit(machine)
        
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
        machine.log.debug(f"current: {machine.flags['current_m1_steps']}, {machine.flags['current_m2_steps']}")
        self.target_m1 = machine.flags['target_m1_steps']
        self.target_m2 = machine.flags['target_m2_steps']
        machine.log.debug(f"target: {machine.flags['target_m1_steps']}, {machine.flags['target_m2_steps']}")
        
        machine.log.info(f"Moving from ({start_m1}, {start_m2}) to ({self.target_m1}, {self.target_m2}).")

        # 2. Calculate the plan: steps and direction for each motor
        delta_m1 = self.target_m1 - start_m1
        delta_m2 = self.target_m2 - start_m2
        
        self.steps_left_m1 = abs(delta_m1)
        self.steps_left_m2 = abs(delta_m2)
        
        # Set motor direction pins (True/False may need to be adjusted for your wiring)
        machine.hardware['motor1_dir'].value = False if delta_m1 > 0 else True
        # Is this stepper backwards?
        machine.hardware['motor2_dir'].value = False if delta_m2 > 0 else True

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
            
           # Send success message to host *before* leaving state
            response = Message.create_message(
                subsystem_name=machine.name, status="SUCCESS",
                payload={"detail": "Move successful"}
            )
            machine.postman.send(response.serialize())

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