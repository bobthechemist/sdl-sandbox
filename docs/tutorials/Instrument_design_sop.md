# Standard Operating Procedure: Agentic Firmware Design for Talos-SDL

**Objective:** 
This document provides a step-by-step guide for non-developers to rapidly design, generate, and deploy custom firmware for a sensor-equipped microcontroller using a frontier AI model (LLM). By following this agentic approach, you can go from a hardware concept to a functioning Talos-SDL instrument in a matter of hours.

## Prerequisites
Before beginning, ensure you have:

1. Your microcontroller and hardware components fully assembled.
2. A list of the specific pins your components are connected to (e.g., I2C pins, digital I/O, PWM pins).
3. Any necessary hardware operational limits (e.g., calibration minimums/maximums, acceptable ranges for commands). *Note: AI models cannot guess physical constraints unique to your specific mechanical setup.*
4. The Talos-SDL repository cloned to your local machine.

## Phase 1: Preparation & Context Generation

To ensure the AI understands the Talos-SDL architecture, you must provide it with the current codebase context.

1. **Run the Context Generator:**
   Navigate to your Talos-SDL directory and run the context generation script:
   ```bash
   python utility/create_code_context.py <firmware>
   ```
2. **Select an Example:**
   Replace <firmware> with the example you want to pass to the coding agent. If you do not know which one to choose, the use `sidekick` as this is the firmware that the developer used to build Talos-sdl.
3. **Locate the Output:**
   The script will generate a compiled text file in the `temp/` directory named something like `code_context_YYMMDD.md`. 

## Phase 2: Drafting the Instrument Specification

Next, you will define what your instrument actually does using a standardized template.

1. **Copy the Template:**
   Navigate to `docs/developer_guides/ai_agent_prompt_templates/` and copy the file named `my_instrument_spec.md` into your `temp/` directory.
2. **Rename the File:**
   Rename this copied file to reflect your new instrument (e.g., `<INSTRUMENT_NAME>_spec.md`).
3. **Complete the Specification:**
   Open the file and fill in all the bracketed fields. 
   * Be as specific as possible regarding pin assignments, expected command arguments, sensor output units, and initialization requirements.
   * *Tip: If you are unsure how to describe a complex sensor interaction, you can provide the sensor's datasheet to an AI chat interface and ask it to help you fill out the `my_instrument_spec.md` template.*

---

## Phase 3: Assembling the AI Prompt

You will now combine the context, your specification, and the master AI instructions into a single prompt.

1. **Prepare the Master Prompt:**
   Navigate to `docs/developer_guides/ai_agent_prompt_templates/` and copy the file named `firmware_generation_template.md` into your `temp/` directory. Rename it to `<INSTRUMENT_NAME>_prompt.md`.
2. **Insert the Components:**
   Open `<INSTRUMENT_NAME>_prompt.md`. Inside this document, there will be designated sections to paste your inputs:
   * **Input 1:** Open `code_context_YYMMDD.md`, copy all its contents, and paste it into the designated "Code Context" section.
   * **Input 2:** Open your completed `<INSTRUMENT_NAME>_spec.md`, copy its contents, and paste it into the designated "Instrument Spec" section.
3. **Generate the Firmware:**
   Copy the entirety of your assembled `<INSTRUMENT_NAME>_prompt.md` text and paste it into the frontier AI model of your choice (e.g., GPT-4, Claude 3.5 Sonnet, Gemini Pro). Submit the prompt and await the generated code.

## Phase 4: Implementation

Once the AI provides the code, you need to integrate it into your local Talos-SDL repository.

1. **Create the Firmware Directory:**
   In your local repository, navigate to the `firmware/` directory and create a new folder named after your instrument.
2. **Create the Core Files:**
   Inside this new folder, manually create three blank Python files:
   * `__init__.py`
   * `handlers.py`
   * `states.py`
3. **Add Linter Ignores:** (Optional)
   At the very top of each of these three files, type `# type: ignore`. This prevents your code editor from raising unnecessary warnings about missing microcontroller-specific libraries.
4. **Paste the Code:**
   Carefully copy the corresponding code blocks provided by the AI and paste them into their respective files.
5. **Update the Firmware Database:**
   Open the global `host/firmware_db` file. Add your new instrument's entry, being absolutely sure to list any external libraries (e.g., sensor driver libraries) the AI included in the `states.py` or `handlers.py` imports.
6. **Deploy the firmware:**
   Execute `python deploy.py <drive> <firmware>` where `<drive>` is the drive letter associated with your microcontroller and `<firmware>` is the name of your new instrument. This script will copy the necessary files to your circuitpython drive. *Keep in mind that this will overwrite and remove files on your microcontroller.*

## Phase 5: Validation

With the code in place, it is time to test the instrument.

1. **Power Cycle:**
   **Crucial Step:** You must physically power cycle the microcontroller (unplug it and plug it back in) for the new `boot.py` and structural changes to take full effect. A simple soft reset button is often not enough.
2. **Verify Hardware Pins:**
   Review the `__init__.py` and `states.py` files. *AI models frequently hallucinate or guess incorrect pin numbers.* Cross-reference the pin numbers in the generated code with your physical wiring to ensure they match perfectly. Correct them if necessary.
3. **Test Commands:**
   Use your interface to send basic commands to the device. 
4. **Monitor the Console / REPL:**
   If a command fails or the device reports a problem without a clear error message, open the REPL or console output (e.g., via Thonny). 
   * Look for tracebacks or exception errors.
   * Common issues include: missing step contexts in `statemachine.py`, incorrect I2C addresses, or missing libraries.
5. **Iterate:**
   If you encounter bugs, copy the error output from the console and paste it back into your chat with the AI. Ask it to correct the specific file, then copy and paste the updated code into your local files.