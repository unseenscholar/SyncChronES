import sys
import os
import json
import threading
from pynput.mouse import Listener, Controller, Button
import time
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QFileDialog, QFrame, QDialog,
    QScrollArea, QMenuBar, QRadioButton, QCheckBox, QGridLayout, QTimeEdit
)
from PySide6.QtCore import QTimer, Qt, Slot, QEvent, QTime
from PySide6.QtGui import QFont, QIcon, QAction

# Custom event type for thread communication
class TimestampCaptureEvent(QEvent):
    EVENT_TYPE = QEvent.Type(QEvent.registerEventType())
    
    def __init__(self):
        super().__init__(TimestampCaptureEvent.EVENT_TYPE)

class SyncChronESApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Set theme colors
        self.bg_color = "#2E3440"         # Dark blue-gray
        self.text_color = "#ECEFF4"       # Off-white
        self.accent_color = "#88C0D0"     # Light blue
        self.alert_color = "#BF616A"      # Red
        self.success_color = "#A3BE8C"    # Green
        self.highlight_color = "#EBCB8B"   # Yellow
        self.secondary_bg = "#3B4252"     # Lighter background
        
        # Initialize state variables
        self.is_recording = False
        self.mouse_listener = None
        self.capture_count = 0
        self.auto_click_active = False  # Initialize auto_click_active here
        
        # Default save location
        self.default_save_dir = os.path.join(os.path.expanduser("~"), "TimestampCaptures")
        
        # Load settings if they exist
        self.settings_file = os.path.join(os.path.expanduser("~"), "timestamp_app_settings.json")
        self.save_dir = self.load_settings()
        
        # Create save directory if it doesn't exist
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
        
        self.setup_menu()
        self.setup_ui()
        
        # Configure the main window
        self.setWindowTitle("SyncChronES")
        self.setMinimumSize(400, 600)
        
        # Set up a timer for timestamp updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timestamp)
        self.timer.start(1)  # Update every millisecond
        
        # Set window to stay on top
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        
        # Connect event filter
        self.installEventFilter(self)

    def setup_ui(self):
        # Apply the dark theme with smaller font sizes
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: {self.bg_color};
                color: {self.text_color};
            }}
            QLabel {{
                color: {self.text_color};
            }}
            QPushButton {{
                background-color: {self.accent_color};
                color: {self.bg_color};
                border: none;
                padding: 6px;
                font-weight: bold;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {self.highlight_color};
            }}
            QLineEdit, QTimeEdit {{
                background-color: {self.secondary_bg};
                color: {self.text_color};
                border: 1px solid {self.accent_color};
                border-radius: 4px;
                padding: 3px;
            }}
            QScrollArea {{
                border: none;
            }}
        """)
        
        # Create a scroll area as the central widget
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        central_widget = QWidget()
        scroll_area.setWidget(central_widget)
        self.setCentralWidget(scroll_area)
        
        # Main layout for the scrollable area
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Timestamp Capture Section
        timestamp_section = QWidget()
        ts_layout = QVBoxLayout(timestamp_section)
        ts_layout.setSpacing(10)
        
        header_label = QLabel("Sensor Click Event Logger")
        header_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        ts_layout.addWidget(header_label)
        
        # Timestamp display
        self.timestamp_label = QLabel("00:00:00.000")
        self.timestamp_label.setFont(QFont("Consolas", 24))
        self.timestamp_label.setAlignment(Qt.AlignCenter)
        self.timestamp_label.setStyleSheet(f"""
            background-color: {self.secondary_bg};
            color: {self.accent_color};
            border: 2px groove #4C566A;
            border-radius: 4px;
            padding: 5px;
        """)
        self.timestamp_label.setMinimumHeight(60)
        ts_layout.addWidget(self.timestamp_label)
        
        # Controls frame (Monitoring)
        controls_frame = QFrame()
        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        
        self.status_indicator = QLabel()
        self.status_indicator.setFixedSize(15, 15)
        self.status_indicator.setStyleSheet(f"""
            background-color: {self.alert_color};
            border-radius: 7px;
        """)
        controls_layout.addWidget(self.status_indicator)
        
        self.recording_status = QLabel("Not Monitoring")
        self.recording_status.setFont(QFont("Segoe UI", 10))
        controls_layout.addWidget(self.recording_status)
        
        controls_layout.addStretch()
        
        self.toggle_button = QPushButton("START MONITORING")
        self.toggle_button.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.toggle_button.setMinimumWidth(120)
        self.toggle_button.clicked.connect(self.toggle_recording)
        controls_layout.addWidget(self.toggle_button)
        
        ts_layout.addWidget(controls_frame)
        
        # Settings frame (Save location and file prefix)
        settings_frame = QFrame()
        settings_layout = QVBoxLayout(settings_frame)
        settings_layout.setSpacing(5)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        
        save_loc_frame = QFrame()
        save_loc_layout = QHBoxLayout(save_loc_frame)
        save_loc_layout.setContentsMargins(0, 0, 0, 0)
        
        save_loc_label = QLabel("Save Location:")
        save_loc_label.setFont(QFont("Segoe UI", 9))
        save_loc_layout.addWidget(save_loc_label)
        
        self.save_location_entry = QLineEdit(self.save_dir)
        self.save_location_entry.setMinimumWidth(200)
        save_loc_layout.addWidget(self.save_location_entry, 1)
        
        browse_button = QPushButton("Browse")
        browse_button.setFont(QFont("Segoe UI", 9))
        browse_button.clicked.connect(self.browse_save_location)
        save_loc_layout.addWidget(browse_button)
        
        settings_layout.addWidget(save_loc_frame)
        
        file_name_frame = QFrame()
        file_name_layout = QHBoxLayout(file_name_frame)
        file_name_layout.setContentsMargins(0, 0, 0, 0)
        
        file_name_label = QLabel("File Prefix:")
        file_name_label.setFont(QFont("Segoe UI", 9))
        file_name_layout.addWidget(file_name_label)
        
        self.file_prefix_entry = QLineEdit("timestamps")
        file_name_layout.addWidget(self.file_prefix_entry)
        file_name_layout.addStretch()
        
        settings_layout.addWidget(file_name_frame)
        ts_layout.addWidget(settings_frame)
        
        # Status frame (Capture count and last capture)
        status_frame = QFrame()
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(0, 0, 0, 0)
        
        status_label = QLabel("Status:")
        status_label.setFont(QFont("Segoe UI", 9))
        status_layout.addWidget(status_label)
        
        self.last_capture_label = QLabel("Ready to capture")
        self.last_capture_label.setFont(QFont("Segoe UI", 9))
        status_layout.addWidget(self.last_capture_label)
        status_layout.addStretch()
        
        ts_layout.addWidget(status_frame)
        
        # Count frame (Captures count and Clear Count button)
        count_frame = QFrame()
        count_layout = QHBoxLayout(count_frame)
        count_layout.setContentsMargins(0, 0, 0, 0)
        
        count_label = QLabel("Captures:")
        count_label.setFont(QFont("Segoe UI", 9))
        count_layout.addWidget(count_label)
        
        self.count_display = QLabel("0")
        self.count_display.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.count_display.setStyleSheet(f"color: {self.accent_color};")
        count_layout.addWidget(self.count_display)
        
        count_layout.addStretch()
        
        clear_button = QPushButton("Clear Count")
        clear_button.setFont(QFont("Segoe UI", 9))
        clear_button.clicked.connect(self.clear_count)
        count_layout.addWidget(clear_button)
        
        ts_layout.addWidget(count_frame)
        
        main_layout.addWidget(timestamp_section)
        
        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)
        
        # Auto-Click Section
        auto_click_section = self.create_auto_click_section()
        main_layout.addWidget(auto_click_section)
        
        main_layout.addStretch()

    def create_auto_click_section(self):
        """Creates and returns the auto-click UI section as a QWidget."""
        auto_click_section = QWidget()
        layout = QVBoxLayout(auto_click_section)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        header_label = QLabel("Automated Click Scheduler")
        header_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        layout.addWidget(header_label)
        
        # Place auto-click main controls (Start button and countdown) at the top
        auto_click_controls = QFrame()
        auto_click_controls_layout = QHBoxLayout(auto_click_controls)
        auto_click_controls_layout.setContentsMargins(0, 0, 0, 0)
        
        self.auto_click_button = QPushButton("START")
        self.auto_click_button.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.auto_click_button.setMinimumWidth(120)
        self.auto_click_button.clicked.connect(self.toggle_auto_click)
        auto_click_controls_layout.addWidget(self.auto_click_button)
        
        self.auto_click_status = QLabel("Ready")
        self.auto_click_status.setFont(QFont("Segoe UI", 10))
        auto_click_controls_layout.addWidget(self.auto_click_status)
        
        auto_click_controls_layout.addStretch()
        
        self.countdown_display = QLabel("Next click: Not scheduled")
        self.countdown_display.setFont(QFont("Segoe UI", 10))
        auto_click_controls_layout.addWidget(self.countdown_display)
        
        layout.addWidget(auto_click_controls)
        
        # Click Trigger Mode Frame
        trigger_frame = QFrame()
        trigger_layout = QVBoxLayout(trigger_frame)
        trigger_layout.setContentsMargins(0, 0, 0, 0)
        
        trigger_label = QLabel("Click Trigger Mode:")
        trigger_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        trigger_layout.addWidget(trigger_label)
        
        trigger_options = QFrame()
        trigger_options_layout = QHBoxLayout(trigger_options)
        
        self.time_based_radio = QRadioButton("Time-based Click")
        self.time_based_radio.setChecked(True)
        self.time_based_radio.toggled.connect(self.update_trigger_mode)
        
        self.countdown_radio = QRadioButton("Countdown Click")
        self.countdown_radio.toggled.connect(self.update_trigger_mode)
        
        trigger_options_layout.addWidget(self.time_based_radio)
        trigger_options_layout.addWidget(self.countdown_radio)
        trigger_options_layout.addStretch()
        
        trigger_layout.addWidget(trigger_options)
        
        # Instead of a text input for time, use QTimeEdit for easier selection
        self.time_input_frame = QFrame()
        time_input_layout = QHBoxLayout(self.time_input_frame)
        time_input_layout.setContentsMargins(0, 0, 0, 0)
        
        time_label = QLabel("Time:")
        time_label.setFont(QFont("Segoe UI", 9))
        time_input_layout.addWidget(time_label)
        
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm:ss")
        self.time_edit.setTime(QTime.currentTime())
        time_input_layout.addWidget(self.time_edit)
        
        trigger_layout.addWidget(self.time_input_frame)
        
        # Countdown input remains for countdown click mode
        self.countdown_input_frame = QFrame()
        countdown_input_layout = QHBoxLayout(self.countdown_input_frame)
        countdown_input_layout.setContentsMargins(0, 0, 0, 0)
        
        countdown_label = QLabel("Countdown (sec):")
        countdown_label.setFont(QFont("Segoe UI", 9))
        countdown_input_layout.addWidget(countdown_label)
        
        self.countdown_input = QLineEdit("10")
        countdown_input_layout.addWidget(self.countdown_input)
        
        trigger_layout.addWidget(self.countdown_input_frame)
        self.countdown_input_frame.setVisible(False)  # Initially hidden
        
        layout.addWidget(trigger_frame)
        
        # Click Type Selection
        click_type_frame = QFrame()
        click_type_layout = QVBoxLayout(click_type_frame)
        click_type_layout.setContentsMargins(0, 0, 0, 0)
        
        click_type_label = QLabel("Click Type:")
        click_type_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        click_type_layout.addWidget(click_type_label)
        
        click_options = QFrame()
        click_options_layout = QHBoxLayout(click_options)
        
        self.left_click_radio = QRadioButton("Left Click")
        self.left_click_radio.setChecked(True)
        
        self.right_click_radio = QRadioButton("Right Click")
        self.double_click_radio = QRadioButton("Double Click")
        
        click_options_layout.addWidget(self.left_click_radio)
        click_options_layout.addWidget(self.right_click_radio)
        click_options_layout.addWidget(self.double_click_radio)
        click_options_layout.addStretch()
        
        click_type_layout.addWidget(click_options)
        layout.addWidget(click_type_frame)
        
        # Remove Repeat Mode toggle; always show repetition settings
        repeat_frame = QFrame()
        repeat_layout = QVBoxLayout(repeat_frame)
        repeat_layout.setContentsMargins(0, 0, 0, 0)
        
        repeat_settings = QFrame()
        repeat_settings_layout = QGridLayout(repeat_settings)
        
        interval_label = QLabel("Interval (sec):")
        interval_label.setFont(QFont("Segoe UI", 9))
        self.interval_input = QLineEdit("5")
        self.interval_input.setFont(QFont("Segoe UI", 9))
        
        repetitions_label = QLabel("Repetitions:")
        repetitions_label.setFont(QFont("Segoe UI", 9))
        self.repetitions_input = QLineEdit("1")
        self.repetitions_input.setFont(QFont("Segoe UI", 9))
        
        infinite_label = QLabel("Infinite:")
        infinite_label.setFont(QFont("Segoe UI", 9))
        self.infinite_checkbox = QCheckBox()
        
        repeat_settings_layout.addWidget(interval_label, 0, 0)
        repeat_settings_layout.addWidget(self.interval_input, 0, 1)
        repeat_settings_layout.addWidget(repetitions_label, 1, 0)
        repeat_settings_layout.addWidget(self.repetitions_input, 1, 1)
        repeat_settings_layout.addWidget(infinite_label, 2, 0)
        repeat_settings_layout.addWidget(self.infinite_checkbox, 2, 1)
        
        repeat_layout.addWidget(repeat_settings)
        layout.addWidget(repeat_frame)
        
        # Click Location Options
        location_frame = QFrame()
        location_layout = QVBoxLayout(location_frame)
        location_layout.setContentsMargins(0, 0, 0, 0)
        
        location_label = QLabel("Click Location:")
        location_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        location_layout.addWidget(location_label)
        
        location_options = QFrame()
        location_options_layout = QHBoxLayout(location_options)
        
        self.current_pos_radio = QRadioButton("Current Mouse Position")
        self.current_pos_radio.setChecked(True)
        self.current_pos_radio.toggled.connect(self.update_location_mode)
        
        self.custom_pos_radio = QRadioButton("Custom Coordinates")
        self.custom_pos_radio.toggled.connect(self.update_location_mode)
        
        location_options_layout.addWidget(self.current_pos_radio)
        location_options_layout.addWidget(self.custom_pos_radio)
        location_options_layout.addStretch()
        
        location_layout.addWidget(location_options)
        
        self.coords_frame = QFrame()
        coords_layout = QHBoxLayout(self.coords_frame)
        coords_layout.setContentsMargins(0, 0, 0, 0)
        
        x_label = QLabel("X:")
        x_label.setFont(QFont("Segoe UI", 9))
        self.x_coord_input = QLineEdit()
        self.x_coord_input.setFont(QFont("Segoe UI", 9))
        
        y_label = QLabel("Y:")
        y_label.setFont(QFont("Segoe UI", 9))
        self.y_coord_input = QLineEdit()
        self.y_coord_input.setFont(QFont("Segoe UI", 9))
        
        get_current_button = QPushButton("Get Current")
        get_current_button.setFont(QFont("Segoe UI", 9))
        get_current_button.clicked.connect(self.get_current_position)
        
        coords_layout.addWidget(x_label)
        coords_layout.addWidget(self.x_coord_input)
        coords_layout.addWidget(y_label)
        coords_layout.addWidget(self.y_coord_input)
        coords_layout.addWidget(get_current_button)
        
        location_layout.addWidget(self.coords_frame)
        self.coords_frame.setVisible(False)
        
        layout.addWidget(location_frame)
        
        layout.addStretch()
        
        return auto_click_section

    def load_settings(self):
        """Load app settings from JSON file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    return settings.get('save_dir', self.default_save_dir)
        except Exception as e:
            print(f"Error loading settings: {e}")
        return self.default_save_dir
    
    def save_settings(self):
        """Save app settings to JSON file"""
        try:
            settings = {'save_dir': self.save_dir}
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    @Slot()
    def browse_save_location(self):
        folder_path = QFileDialog.getExistingDirectory(
            self, "Select Save Location", self.save_dir
        )
        if folder_path:
            self.save_dir = folder_path
            self.save_location_entry.setText(folder_path)
            self.save_settings()
    
    @Slot()
    def update_timestamp(self):
        current_time = datetime.now().strftime("%H:%M:%S.%f")[:-1]
        self.timestamp_label.setText(current_time)
    
    @Slot()
    def toggle_recording(self):
        if self.is_recording:
            self.is_recording = False
            if self.mouse_listener:
                self.mouse_listener.stop()
                self.mouse_listener = None
            self.toggle_button.setText("START MONITORING")
            self.recording_status.setText("Not Monitoring")
            self.status_indicator.setStyleSheet(f"""
                background-color: {self.alert_color};
                border-radius: 7px;
            """)
            self.last_capture_label.setText("Monitoring stopped")
        else:
            self.is_recording = True
            self.toggle_button.setText("STOP MONITORING")
            self.recording_status.setText("Monitoring Active")
            self.status_indicator.setStyleSheet(f"""
                background-color: {self.success_color};
                border-radius: 7px;
            """)
            self.last_capture_label.setText("Waiting for clicks...")
            self.start_mouse_listener()
    
    def start_mouse_listener(self):
        def on_click(x, y, button, pressed):
            if pressed and self.is_recording:
                QApplication.instance().postEvent(self, TimestampCaptureEvent())
            return True
        
        self.mouse_listener = Listener(on_click=on_click)
        self.mouse_listener.daemon = True
        self.mouse_listener.start()
    
    def eventFilter(self, obj, event):
        if isinstance(event, TimestampCaptureEvent) and self.is_recording:
            self.capture_timestamp()
            return True
        return super().eventFilter(obj, event)
    
    def capture_timestamp(self):
        timestamp = datetime.now()
        formatted_time = timestamp.strftime("%H:%M:%S.%f")[:-1]
        
        current_save_dir = self.save_location_entry.text()
        if not os.path.exists(current_save_dir):
            try:
                os.makedirs(current_save_dir)
            except Exception as e:
                self.last_capture_label.setText(f"Error: {str(e)}")
                return
        
        date_str = timestamp.strftime("%Y-%m-%d")
        prefix = self.file_prefix_entry.text() or "timestamps"
        filename = os.path.join(current_save_dir, f"{prefix}_{date_str}.txt")
        
        try:
            with open(filename, "a") as f:
                f.write(f"{timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-1]}\n")
            self.last_capture_label.setText(f"Captured: {formatted_time}")
            self.capture_count += 1
            self.count_display.setText(str(self.capture_count))
            current_color = self.success_color if self.is_recording else self.alert_color
            self.status_indicator.setStyleSheet(f"""
                background-color: {self.highlight_color};
                border-radius: 7px;
            """)
            QTimer.singleShot(100, lambda: self.status_indicator.setStyleSheet(f"""
                background-color: {current_color};
                border-radius: 7px;
            """))
        except Exception as e:
            self.last_capture_label.setText(f"Error: {str(e)}")
    
    @Slot()
    def clear_count(self):
        self.capture_count = 0
        self.count_display.setText("0")
        self.last_capture_label.setText("Counter reset")
        
    def setup_menu(self):
        menu_bar = self.menuBar()
        help_menu = menu_bar.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

    def show_about_dialog(self):
        about_dialog = AboutDialog()
        about_dialog.exec()
        
    def update_trigger_mode(self):
        if self.time_based_radio.isChecked():
            self.time_input_frame.setVisible(True)
            self.countdown_input_frame.setVisible(False)
        else:
            self.time_input_frame.setVisible(False)
            self.countdown_input_frame.setVisible(True)

    def update_location_mode(self):
        if self.custom_pos_radio.isChecked():
            self.coords_frame.setVisible(True)
        else:
            self.coords_frame.setVisible(False)

    def get_current_position(self):
        try:
            mouse = Controller()
            pos = mouse.position
            self.x_coord_input.setText(str(pos[0]))
            self.y_coord_input.setText(str(pos[1]))
        except Exception as e:
            self.auto_click_status.setText(f"Error: {str(e)}")

    def toggle_auto_click(self):
        if self.auto_click_active:
            self.auto_click_active = False
            self.auto_click_button.setText("START")
            self.auto_click_status.setText("Stopped")
            self.countdown_display.setText("Next click: Not scheduled")
        else:
            self.setup_auto_click()

    def setup_auto_click(self):
        try:
            self.auto_click_active = True
            self.auto_click_button.setText("STOP")
            self.auto_click_status.setText("Active")
            current_time = datetime.now()
            
            if self.time_based_radio.isChecked():
                # Use time from QTimeEdit
                qtime = self.time_edit.time()
                target_time = current_time.replace(
                    hour=qtime.hour(), minute=qtime.minute(), second=qtime.second(), microsecond=0
                )
                if target_time < current_time:
                    target_time += timedelta(days=1)
            else:
                try:
                    seconds = float(self.countdown_input.text())
                    target_time = current_time + timedelta(seconds=seconds)
                except ValueError:
                    self.auto_click_status.setText("Error: Invalid countdown")
                    self.auto_click_active = False
                    self.auto_click_button.setText("START")
                    return
            
            self.click_settings = {
                'target_time': target_time,
                'click_type': 'left' if self.left_click_radio.isChecked() else 
                              'right' if self.right_click_radio.isChecked() else 'double',
                # Repeat is always enabled; for one click, set repetitions to 1
                'repeat': True,
                'interval': float(self.interval_input.text()) if self.interval_input.text() else 5,
                'repetitions': int(self.repetitions_input.text()) if self.repetitions_input.text() and not self.infinite_checkbox.isChecked() else -1,
                'custom_pos': self.custom_pos_radio.isChecked(),
                'x_coord': int(self.x_coord_input.text()) if self.x_coord_input.text() else 0,
                'y_coord': int(self.y_coord_input.text()) if self.y_coord_input.text() else 0,
                'current_repetition': 0
            }
            
            self.update_click_countdown()
            
        except Exception as e:
            self.auto_click_status.setText(f"Error: {str(e)}")
            self.auto_click_active = False
            self.auto_click_button.setText("START")

    def update_click_countdown(self):
        if not self.auto_click_active:
            return
            
        current_time = datetime.now()
        target_time = self.click_settings['target_time']
        
        if current_time >= target_time:
            self.perform_click()
            if self.click_settings['repeat']:
                self.click_settings['current_repetition'] += 1
                if (self.click_settings['repetitions'] != -1 and 
                    self.click_settings['current_repetition'] >= self.click_settings['repetitions']):
                    self.auto_click_active = False
                    self.auto_click_button.setText("START")
                    self.auto_click_status.setText("Completed")
                    self.countdown_display.setText("Next click: Not scheduled")
                    return
                next_time = current_time + timedelta(seconds=self.click_settings['interval'])
                self.click_settings['target_time'] = next_time
        
        if self.auto_click_active:
            time_diff = target_time - current_time
            seconds_remaining = max(0, time_diff.total_seconds())
            hours, remainder = divmod(seconds_remaining, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            if hours > 0:
                countdown_text = f"Next click in: {int(hours)}h {int(minutes)}m {int(seconds)}s"
            elif minutes > 0:
                countdown_text = f"Next click in: {int(minutes)}m {int(seconds)}s"
            else:
                countdown_text = f"Next click in: {seconds:.1f}s"
                
            self.countdown_display.setText(countdown_text)
            
            if seconds_remaining > 10:
                QTimer.singleShot(500, self.update_click_countdown)
            else:
                QTimer.singleShot(100, self.update_click_countdown)

    def perform_click(self):
        try:
            mouse = Controller()
            if self.click_settings['custom_pos']:
                mouse.position = (self.click_settings['x_coord'], self.click_settings['y_coord'])
            
            click_type = self.click_settings['click_type']
            if click_type == 'left':
                mouse.click(Button.left)
            elif click_type == 'right':
                mouse.click(Button.right)
            elif click_type == 'double':
                mouse.click(Button.left)
                time.sleep(0.1)
                mouse.click(Button.left)
                
            self.auto_click_status.setText(f"Click at {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
            
        except Exception as e:
            self.auto_click_status.setText(f"Error: {str(e)}")
            
    def closeEvent(self, event):
        if self.mouse_listener:
            self.mouse_listener.stop()
        self.timer.stop()
        self.auto_click_active = False
        event.accept()

class AboutDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("About SyncChronES")
        self.setMinimumSize(400, 250)
        
        layout = QVBoxLayout()
        
        about_text = (
            "<h2>Synchronous Chronological Event Stamp</h2>"
            "<p>Version: 1.2.0</p>"
            "<p>Copyright © 2024 SyncChronES</p>"
            "<p>License: MIT</p>"
            "<p>Creator: Viswajith S Nair</p>"
            "<p>Email: <a href='mailto:viswajithsn@gmail.com'>viswajithsn@gmail.com</a></p>"
        )
        
        label = QLabel(about_text)
        label.setOpenExternalLinks(True)
        layout.addWidget(label)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)        
        self.setLayout(layout)

class HelpDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("User Guide")
        self.setMinimumSize(500, 300)
        
        layout = QVBoxLayout()
        
        help_text = (
            "<h2>How To</h2>"
            "<p>1. Click the Start Monitoring option to begin logging mouse clicks.</p>"
            "<p>2. The timestamp display updates in real-time.</p>"
            "<p>3. Auto-click scheduling: choose either a specific time using the picker or a countdown.</p>"
            "<p>4. Set the click type and repetition settings (set repetitions to 1 for a single click).</p>"
        )
        
        label = QLabel(help_text)
        label.setOpenExternalLinks(True)
        layout.addWidget(label)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)
        
        self.setLayout(layout)

def main():
    app = QApplication(sys.argv)
    window = SyncChronESApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
