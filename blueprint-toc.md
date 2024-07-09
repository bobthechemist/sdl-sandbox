# Blueprint (MSE0) function and class list

## package contents
- __init__.py
- host_utilities.py
- messages.py
- sdl_communicator.py
- utility.py
- subsystems
    - host.py
    - pumps.py
    - test.py

## Functions and classes

### __init__.py

imports sdlCommunicator

### host_utilities.py

utilities that are only meant for the host system. Does a check to see if this is erroneously run on a microcontroller running circuitpython

`find_data_comports()` looks for circuitpython data ports that are open and returns the port and ID information

### messages.py

`valid_comm_types`: The types of communication between host and subsystem
`valid_status`: the valid ways to classify the status of a message
`make_message()`: creates a message with provided information and returns either dict or json

#### MessageBuffer

A class for managing messages

`is_empty()`: there are no messages in the buffer
`store_message()`: stores a message, requires that the message be in dict format
`get_oldest_message()`: Using a FILO method of retrieving messages, can convert to json
`json_to_dict()`: converts json into a dict, can handle invalid json returing a dict with raw key
`dict_to_json()`: converts dict to json without any error checking
`get_size_of_buffer()`: returns the size of the buffer
`store_json()`: converts a json message to dict before storing it

**thoughts** store_json should be wrapped into store_message, which should allow dict or json as valid formats and then do the conversion internally if necessary

### sdl_communicator.py

#### sdlCommunicator

Contains functions for managing serial communication between host and subsystem. Presently designed to work on either host or subsystem (handles appropriate importing of relevant modules). Creates two buffers (read/write) using the concept of an inbox and outbox.

`read_serial_data()` reads data on the serial line and stores into the read buffer
`write_serial_data()` looks for a message in the write buffer and sends it
`prep_message_for_write()` adds `\r\n` and encodes the message. 

**thoughts** changing names of read/write buffer to inbox and outbox might make programming concept a bit less opaque. Proper encoding of message probably can be incorporated directly into writing serial data.

### utility.py

`check_if_microcontroller()` looks for the python implementation and if it finds circuitpython, assumes this is a microcontroller

## Subsystems

Contains individual modules for each of the subsystem types. Everything here is wip

# Design thoughts

- Each microcontroller will import the relevant subsystem module which does two things
    - creates a dictionary that translates messages into operations
    - opens a communication link with the host
- The host "subsystem" looks for attached devices, opens the communication link, and creates a user interface
- The subsystems need to perform some type of polling either via a while loop or async functions. They will check for messages in the inbox and respond as appropriate. This functionality should be the same for all subsystems. (does that mean it belongs in sdlCommunicator?)
- The subsystems need to be able to send unsolicited information to the host, notifications, alerts. Unsure how to use logs and sync at this point. Log may be internal messages or "notes to self". Sync messages might be better refered to as config/settings/properties for purposes of initializing things. Requests are messages that require a response.
- Payload handling should accommodate both strings and json. strings will be parsed as a space-delimited list of command and arguments. json can be used with more sophisticated instructions or data are transfered. 
- subsystem functions need to follow some sort of template. They need to do their own keyword checking, they need to return a message, of type "RESPONSE" (?), in which the status and payload are updated appropriately