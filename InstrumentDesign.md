# Instrument Design

First draft on howto for creating a new instrument for the SDL. Here we are creating a simple stir plate, which was made by gluing a magnet onto an old PC fan and enclosing it in a 3D printed case.

# Process overview

- Create the firmware
- Create the host device

# draft of steps

- Create folder in firmware for diystirplate
- Create in this folder __init__.py and states.py
- Update a templated __init__.py file
    - libraries (statemachine, postman, states)
    - create a machine instance
    - create and attach a postman instance
    - add states
    - initialize machine-wide flags
- Create states in states.py
    - State and Messages from shared_lib will be needed, add any other imports as the code requires
    - Include machine-wide constants
    - Each sate should call `super()`s. The abstracted class is currently pretty empty, but this is where we will eventually include logging and other logic to be a bit more consistent in what information about states is being recorded and stored for automation and autonomy.
