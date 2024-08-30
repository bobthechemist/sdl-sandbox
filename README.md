# sdl-sandbox
Prototyping space for self-driven laboratory projects

## Current status

The approach is to treach each subsystem and the host as finite state machines. Presently, the states that are considered include:

- **Initialize** Creates all of the connections, hardware setup, and sets default parameters. Includes setting up serial communication.
- **Listening** Reads the read buffer created for the state machine
- **Sending** Sends a message or command
- **Reacting** Will perform some tasks internally
- **Error** A problem was found and will be documented
- **Shutdown** Cleanly release resources

The `StateMachine` class can be use to create a state machine on either a microcontroller or PC host. It provides for storing data between states (in the `properties` dict) and includes a global (to the state machine) counter. The class provides functions to add states, start and stop the FSM, switch to a state and update the state.

The `State` abstract class provides the three main routines needed for a state (enter, update, exit), allows for the state to be named, and provides space for local (to the state) data through the properties dict and counter. It also maintains a timer `entered_at` to handle time-sensitive conditions and behaviors.

Each subsystem and host will need its own definitions for the six states above, plus any system-specific states. An example of the host as a fsm has been presented. During `Initialize`, it looks for any valid microcontrollers and for each one found, sets up serial communication with them. This information is stored in `properties['subsystems']` as an `sdlCommunicator`. Sending data and receiving data are accomplished by `write_serial_data` and `read_serial_data`, respectively. The data is expected to be in the format found in `messages`; namely, a JSON packet containing the subsystem name, the type of communication, the status of the action and the payload. In both reads and writes, the data pass through a buffer, so a write requires two steps:

- store the message in the write buffer
- write the serial data

Likewise, `read_serial_data` checks the serial line for data and stores it into the read buffer, which must be read with a second command. Separating the two helps prevent (I think) communication loss in the event of multiple messages being sent at the same time. I have not tested this feature yet.

The microcontrollers are currently running a non-FSM based routine (`test.py`) that listens for commands to blink the red light on the board or change the neopixel color.

The following code runs on host and demonstrates a simple FSM process. To avoid errors, two subsystems should be attached.

``` python
from mse0.subsystems.hostfsm import machine as host
from time import sleep

host.run('Initialize')
while host.running:
    host.update()
    sleep(0.001) # don't overload processor
```

After initializing the two communication channels, the host enters listening mode, as if it were waiting for user input. Using the timer, we simulate user input after five seconds, at which point the state changes to sending. In sending, we send two hardcoded messages to blink the red lights of each subsystem. The state then returns to listening and prints any messages received from the subsystems. After a few more seconds, the state changes to shutdown in order to cleanly exit the demo.

## Next steps

1. Convert the subsystem into a FSM.
2. Create a basic user interface
3. Template FSMs for the pump system and the sample chamber system
4. Tighten up code and refactor