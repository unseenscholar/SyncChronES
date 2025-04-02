# SyncChronES
A synchronous chronological event stamping utility

**SyncChronES Application Documentation**

**1. Overview**

SyncChronES is a Python-based application that logs mouse click events and provides automated mouse clicking functionality.

**2. Features**

* **Timestamp Logging:** Records mouse click events with high-precision timestamps.
   
* **Automated Clicking:** Schedules and executes mouse clicks at specified times or intervals.
   
* **Customization:**
   * Save directory selection for timestamp logs.
   * File prefixing for log files.
   * Click type selection (left, right, double).
   * Click location options (current position or custom coordinates).
   * Repeat mode with interval and repetition settings.
   
* **User Interface:**
   * Real-time timestamp display.
   * Monitoring status indication.
   * Intuitive controls for starting/stopping logging and auto-clicking.
   * Settings for save location, file prefix, and click parameters.

**3. UI Elements and Functionality**

**3.1 Main Window**

* **Timestamp Display:** Shows the current timestamp with millisecond precision.
   
* **Monitoring Controls:**
   * `START MONITORING` / `STOP MONITORING` Button: Toggles mouse click logging.
   * Status Indicator:  A colored circle that indicates the monitoring status (Green for active, Red for inactive).
   * Monitoring Status Label: Text display of the current monitoring status.
   
* **Save Settings:**
   * Save Location:  Select the directory where timestamp logs are saved.
   * File Prefix: Edit the prefix of the log file.
   
* **Status Display:**
   * Last Capture:  Displays the timestamp of the most recent mouse click event.
   * Capture Count: Shows the total number of captured mouse clicks.
   * Clear Count: Resets the capture count.

**3.2 Auto-Click Section**

* **Auto-Click Controls:**
   * `START` / `STOP` Button: Toggles the auto-click functionality.
   * Auto-Click Status:  Displays the current status of the auto-clicker.
   * Countdown Display: Shows the time remaining until the next scheduled click.
   
* **Click Trigger Mode:**
   * Time-based Click Radio Button:  Selects time-based click scheduling.
   * Countdown Click Radio Button: Selects countdown-based click scheduling.
   * Time Input: Widget for setting the specific time for time-based clicks.
   * Countdown Input: Input for entering the countdown duration (in seconds) for countdown clicks.
   
* **Click Type Selection:**
   * Left Click:  Selects a left mouse click.
   * Right Click: Selects a right mouse click.
   * Double Click: Selects a double left mouse click.
   
* **Repeat Settings:**
   * Interval Input:  The interval between repeated clicks (in seconds).
   * Repetitions Input: The number of click repetitions.
   * Infinite Checkbox:  Enable infinite click repetitions.
   
* **Click Location Options:**
   * Current Mouse Position: Clicks at the current mouse cursor position.
   * Custom Coordinates:  Clicks at user-specified coordinates.
   * X Coordinate Input: X-coordinate for custom click locations.
   * Y Coordinate Input: Y-coordinate for custom click locations.

**4. Functionality**

* **Timestamp Capture:**
   * When monitoring is active, the application listens for mouse click events.
   * On each click, the application captures the current timestamp with millisecond precision.
   * Timestamps are displayed in the timestamp label and saved to a text file.
   * The filename for the timestamp log is generated using the specified prefix and the current date.
   * The save directory and file prefix can be configured by the user.
   
* **Automated Clicking:**
   * The auto-click functionality can be scheduled to perform clicks at a specific time or after a countdown.
   * Click type (left, right, or double), repetition interval, and number of repetitions can be customized.
   * The click location can be set to the current mouse position or custom coordinates.
   * The application uses `pynput.mouse.Controller` to control mouse actions.

**5. Settings**

* Application settings, including the save directory, are saved to and loaded from a JSON file (`timestamp_app_settings.json`) in the user's home directory.

**6. Dependencies**

* Python 3.6 or later
* PySide6
* pynput
* datetime
* json
* os
* sys
* threading

**7. Installation**

* Install the required dependencies using pip:
   ```bash
   pip install PySide6 pynput
   ```

**8. Usage**

1.  Run the `SyncChronES.py` script (Windows executable available).
2.  Use the `START MONITORING` button to begin logging mouse clicks.
3.  Configure the save location and file prefix as needed.
4.  Use the Auto-Click Scheduler to set up automated click events.
5.  The Help menu provides basic usage instructions.
****
