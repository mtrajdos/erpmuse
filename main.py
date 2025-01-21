from kivy.config import Config
Config.set('graphics', 'fullscreen', 'auto')
Config.set('kivy', 'exit_on_escape', '0')
Config.set('kivy', 'pause_on_minimize', '0')  # Prevent app from being killed when minimized
Config.write()

from kivy.core.window import Window
Window.borderless = True
Window.keep_screen_on = True  # Keep screen from turning off

# Add these lines
from kivy.utils import platform
if platform == 'android':
    from pythonforandroid import acquire_wake_lock, release_wake_lock
    acquire_wake_lock('PARTIAL_WAKE_LOCK', 'ShamScenes::WakeLock')

from kivy.app import App
from kivy.uix.image import Image as KivyImage
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.logger import Logger
from kivy.utils import get_color_from_hex
import numpy as np
import random
import os
from datetime import datetime
import pytz
import platform
import time
from pythonosc import dispatcher
from pythonosc import osc_server
from pythonosc import udp_client
import threading
from MuseMonitor import MuseSimulator

# Global OSC Configuration
class OSCConfig:
    IP = "127.0.0.1"
    PORT = 5002
    TIMEOUT = 0.5
    
class TouchableFloatLayout(FloatLayout):
    def on_touch_down(self, touch):
        app = App.get_running_app()
        if app:
            app.handle_touch()
        return super().on_touch_down(touch)

class ConnectionStatus(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (None, None)
        self.size = (600, 120)  # Increased size for instruction
        self.pos_hint = {'center_x': 0.5, 'top': 0.98}
        
        # Connection status with larger font
        self.status_label = Label(
            text="EEG Status: Waiting for connection...",
            size_hint=(None, None),
            size=(600, 40),
            pos_hint={'center_x': 0.5},
            color=get_color_from_hex('#FF0000'),
            font_size='18sp',
            bold=True
        )
        
        # EEG values display with better formatting
        self.eeg_label = Label(
            text="Waiting for EEG data...",
            size_hint=(None, None),
            size=(600, 40),
            pos_hint={'center_x': 0.5},
            font_size='14sp',
            color=get_color_from_hex('#FFFFFF')
        )
        
        # Instructions label
        self.instruction_label = Label(
            text="Touch anywhere to start the experiment",
            size_hint=(None, None),
            size=(600, 40),
            pos_hint={'center_x': 0.5},
            font_size='16sp',
            color=get_color_from_hex('#FFFF00')  # Yellow for visibility
        )
        
        self.add_widget(self.status_label)
        self.add_widget(self.eeg_label)
        self.add_widget(self.instruction_label)
        
    def update_status(self, is_connected):
        self.status_label.text = "EEG Status: Connected" if is_connected else "EEG Status: Waiting..."
        self.status_label.color = get_color_from_hex('#00FF00') if is_connected else get_color_from_hex('#FF0000')
    
    def update_eeg_data(self, timestamp, values):
        value_str = ", ".join([f"{v:.1f}" for v in values])
        self.eeg_label.text = f"EEG Data: {value_str}"
        
    def hide_instruction(self):
        """Hide the instruction after experiment starts"""
        self.instruction_label.opacity = 0

class OSCManager:
    def __init__(self, status_callback):
        self.status_callback = status_callback
        self.server = None
        self.server_thread = None
        self.is_connected = False
        self.last_data_time = time.time()
        self.timeout_threshold = OSCConfig.TIMEOUT
        self._connection_check_event = None
        
    def eeg_handler(self, address: str, *args):
        """Handle incoming EEG data"""
        self.last_data_time = time.time()
        
        if not self.is_connected:
            self.is_connected = True
            self.status_callback.update_status(True)
            Logger.info("EEG connection established")
        
        try:
            eeg_values = [float(arg) for arg in args]
            self.status_callback.update_eeg_data(self.last_data_time, eeg_values)
        except Exception as e:
            Logger.error(f"Error processing EEG data: {str(e)}")
    
    def check_connection(self):
        """Check if EEG data is being received"""
        current_time = time.time()
        time_since_last = current_time - self.last_data_time
        
        if time_since_last < self.timeout_threshold:
            if not self.is_connected:
                self.is_connected = True
                self.status_callback.update_status(True)
                Logger.info("EEG connection detected")
            return True
        else:
            if self.is_connected:
                self.is_connected = False
                self.status_callback.update_status(False)
                Logger.warning(f"EEG connection lost (No data for {time_since_last:.2f}s)")
            return False
    
    def start_server(self):
        """Start the OSC server"""
        try:
            disp = dispatcher.Dispatcher()
            disp.map("/muse/eeg", self.eeg_handler)
            
            self.server = osc_server.ThreadingOSCUDPServer(
                (OSCConfig.IP, OSCConfig.PORT), disp)
            
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            Logger.info(f"OSC Server listening on {OSCConfig.IP}:{OSCConfig.PORT}")
            
            # Start periodic connection checks
            def check_connection_periodic(dt):
                self.check_connection()
            self._connection_check_event = Clock.schedule_interval(check_connection_periodic, 0.1)
            
            return True
            
        except Exception as e:
            Logger.error(f"Failed to start OSC server: {str(e)}")
            return False
    
    def stop_server(self):
        """Stop the OSC server and cleanup"""
        if self._connection_check_event:
            self._connection_check_event.cancel()
        
        if self.server:
            self.server.shutdown()
            self.server = None
            
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=1.0)
            self.server_thread = None

class SimplifiedShamApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Initialize components
        self.connection_status = ConnectionStatus()
        self.osc_manager = None
        self.simulator = None
        self.simulator_thread = None
        
        # Initialize experiment variables
        self.initialize_variables()
        self.setup_ui()
        self.setup_logging()
        Window.bind(on_resize=self.on_window_resize)
        
        # Start OSC components
        self.start_osc_components()
        
    def create_block(self):
        """Create a single block of 120 trials (60 pairs) with alternating regular and inverted patterns"""
        # Create base stimuli pairs maintaining strict alternation
        base_stimuli = [
            ('checkerboard255.png', 'checkerboard255_inverted.png'),
            ('checkerboard225.png', 'checkerboard225_inverted.png'),
            ('checkerboard195.png', 'checkerboard195_inverted.png')
        ]
        
        # Create pairs ensuring exact alternation
        
        pairs = []
        for stim_pair in base_stimuli:
            for _ in range(20):  # 20 pairs per brightness level
                regular, inverted = stim_pair
                # Always keep pairs together, just randomize pair order
                pairs.append((regular, inverted))
        
        # Shuffle the pairs (but keep pairs intact)
        random.shuffle(pairs)
        
        # Flatten the pairs into a sequence
        shuffled_block = []
        for regular, inverted in pairs:
            # Each pair is always [regular, inverted]
            shuffled_block.extend([regular, inverted])
            
        Logger.info(f"Created block with {len(shuffled_block)} trials")
        return shuffled_block
        
    def initialize_variables(self):
        self.stim_duration = 0.600000
        self.current_trial = 1
        self.last_stim_off_time = None
        self.current_stim_on_time = None
        
        #100000 trials with 120 stimuli each
        self.block_number = 100000
        
        self.scene_stimuli = []
        for block in range(self.block_number):
            block_stimuli = self.create_block()
            self.scene_stimuli.extend(block_stimuli)
            
            # Validate pairs in each block
            for i in range(0, len(block_stimuli), 2):
                stim1 = block_stimuli[i].replace('.png', '')
                stim2 = block_stimuli[i + 1].replace('.png', '')
                if ('inverted' in stim1 and 'inverted' not in stim2) or \
                   ('inverted' not in stim1 and 'inverted' in stim2):
                    base1 = stim1.replace('_inverted', '')
                    base2 = stim2.replace('_inverted', '')
                    if base1 != base2:
                        Logger.warning(f"Mismatched pair in block {block + 1}: {stim1} - {stim2}")
            
        Logger.info(f"Created experiment with {len(self.scene_stimuli)} total trials")
        self.showing_background = True
        self.ITIs = np.random.uniform(1.005000, 3.005000, len(self.scene_stimuli))
        self.next_trial_scheduled = False
        self.trial_running = False
        
    def start_osc_components(self):
        """Initialize and start OSC server and simulator"""
        try:
            # Start OSC manager first
            self.osc_manager = OSCManager(self.connection_status)
            if self.osc_manager.start_server():
                Logger.info("OSC server started successfully")
                
                # Only start simulator if we're not receiving real data
                if not self.osc_manager.check_connection:
                    self.simulator = MuseSimulator(port=OSCConfig.PORT)
                    self.simulator_thread = threading.Thread(target=self.simulator.run)
                    self.simulator_thread.daemon = True
                    self.simulator_thread.start()
                    Logger.info("EEG simulator started")
                
            else:
                Logger.error("Failed to start OSC server - simulator not started")
        except Exception as e:
            Logger.error(f"Error starting OSC components: {str(e)}")

    def handle_touch(self):
        if self.showing_background:
            self.start_experiment()
        elif not self.showing_background:
            self.end_experiment()

    def start_experiment(self):
        """Initial experiment start after first touch"""
        Logger.info("Starting experiment...")
        self.showing_background = False
        self.connection_status.hide_instruction()
        self.fixation_cross.opacity = 1
        
        # Show fixation for first ITI duration before first trial
        first_iti = self.ITIs[0]
        Logger.info(f"Scheduling first trial with ITI: {first_iti:.6f}")
        Clock.schedule_once(self.show_trial, first_iti)
            
    def pause_for_connection(self, next_callback):
        """Pause trials until EEG connection is restored"""
        if hasattr(self, 'osc_manager'):
            is_connected = self.osc_manager.check_connection()
            if not is_connected and not hasattr(self, '_paused_logged'):
                self._paused_logged = True
                self.log_break("PAUSE", "EEG disconnected")
                Logger.warning("Trial paused - waiting for EEG connection...")
            elif is_connected:
                if hasattr(self, '_paused_logged'):
                    del self._paused_logged
                    self.log_break("RESUME", "EEG connected")
                Clock.schedule_once(next_callback, 0)
            else:
                self._paused_logged = False
                return
            Clock.schedule_once(lambda dt: self.pause_for_connection(next_callback), 0.1)
        else:
            Clock.schedule_once(next_callback, 0)
            
    def show_trial(self, dt):
        if self.trial_running:
            Logger.debug("Trial skipped - already running")
            return
            
        # Brief connection check before proceeding - TODO DEBUG
        # if hasattr(self, 'osc_manager') and not self.osc_manager.check_connection():
            # self.trial_running = False
            # Logger.debug("Waiting for EEG before starting trial")
            # self.pause_for_connection(lambda: self.show_trial(0))
            # return

        self.trial_running = True
        Logger.info(f"Starting trial {self.current_trial}")
        
        # Prepare stimulus
        current_stim = self.scene_stimuli[self.current_trial - 1]
        self.background_image.source = os.path.join(os.path.dirname(__file__), "sprites", current_stim)
        self.background_image.reload()
        
        def show_stimulus(dt):
            self.background_image.opacity = 1
            self.white_square.opacity = 1
            self.white_square.pos = (Window.width - self.white_square.width, 0)  # Correct positioning
            self.current_stim_on_time = time.time()
            Clock.schedule_once(self.end_trial, self.stim_duration)
            Logger.debug(f"Trial {self.current_trial} stimulus shown at {self.current_stim_on_time:.6f}")
        
        Clock.schedule_once(show_stimulus, 0)

    def end_trial(self, dt):
        # Record time before making any visual changes
        self.current_stim_off_time = time.time()
        
        # Log data before making visual changes
        self.log_trial_data()
        
        # Hide stimuli
        self.background_image.opacity = 0
        self.white_square.opacity = 0
        self.last_stim_off_time = self.current_stim_off_time
        self.trial_running = False
        
        if self.current_trial == len(self.scene_stimuli):
            self.fixation_cross.opacity = 0
            Clock.schedule_once(lambda dt: self.end_experiment(), 0)
        else:
            self.current_trial += 1
            Clock.schedule_once(self.show_trial, self.ITIs[self.current_trial - 1])

    def log_trial_data(self):
        now = time.time()
        stim_on = self.current_stim_on_time
        stim_off = self.current_stim_off

    def log_trial_data(self):
        now = time.time()
        stim_on = self.current_stim_on_time
        stim_off = self.current_stim_off_time
        target_iti = self.ITIs[self.current_trial - 1]
        
        actual_iti = 0
        if self.last_stim_off_time:
            actual_iti = stim_on - self.last_stim_off_time
        
        iti_error = actual_iti - target_iti
        stim_file = self.scene_stimuli[self.current_trial - 1]
        actual_stim_duration = stim_off - stim_on
        
        # Get EEG connection status
        eeg_connected = self.osc_manager.is_connected if hasattr(self, 'osc_manager') else False
        
        log_entry = (f"{now:.6f},"           # Timestamp
                    f"{self.current_trial},"  # Trial
                    f"{stim_file},"           # StimFile
                    f"{stim_on:.6f},"         # StimON
                    f"{stim_off:.6f},"        # StimOFF
                    f"{actual_stim_duration:.6f}," # Stim_Duration
                    f"{target_iti:.6f},"      # Target_ITI
                    f"{actual_iti:.6f},"      # Actual_ITI
                    f"{iti_error:.6f},"       # ITI_Error
                    f"{1 if eeg_connected else 0}\n")  # EEG Status
                    
        Logger.info(f"Trial {self.current_trial}: {stim_file}")
        self.datafilepointer.write(log_entry)
        self.datafilepointer.flush()

    def log_break(self, reason, details=""):
        """Log a break in the experiment (pause, resume, connection events)"""
        break_time = time.time()
        break_line = f"BREAK,{break_time:.6f},{reason},{details}\n"
        self.datafilepointer.write(break_line)
        self.datafilepointer.flush()

    def setup_ui(self):
        self.layout = TouchableFloatLayout()
        with self.layout.canvas.before:
            Color(119/255, 119/255, 119/255)
            self.rect = Rectangle(size=Window.size, pos=(0, 0))

        self.background_image = KivyImage(
            size_hint=(1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            allow_stretch=True,
            keep_ratio=False,
            opacity=0
        )

        self.fixation_cross = KivyImage(
            source="sprites/fixation_cross.png",
            size_hint=(None, None),
            size=(Window.width * 0.05, Window.height * 0.05),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            allow_stretch=False,
            keep_ratio=True,
            opacity=0
        )

        self.white_square = KivyImage(
            source="sprites/white_square.png",
            size_hint=(None, None),
            size=(110, 110),
            pos=(Window.width - 110, Window.height - 110),  # Position from top-right
            allow_stretch=True,
            keep_ratio=False,
            opacity=0
        )

        self.layout.add_widget(self.background_image)
        self.layout.add_widget(self.white_square)
        self.layout.add_widget(self.fixation_cross)
        self.layout.add_widget(self.connection_status)

    def setup_logging(self):
        log_dir = os.path.join(os.getcwd(), "logs") if platform.system() == "Windows" else os.path.join("/storage/emulated/0/Download", "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        timestamp = datetime.now(pytz.timezone("Europe/Berlin")).strftime("%Y%m%d_%H%M%S")
        log_filename = os.path.join(log_dir, f"ShamScenes_{timestamp}.txt")
        
        self.datafilepointer = open(log_filename, "w")
        
        # Write header with experiment info
        header = (
            f"# Experiment Info:\n"
            f"# Start_Time: {timestamp}\n"
            f"# OSC_IP: {OSCConfig.IP}\n"
            f"# OSC_Port: {OSCConfig.PORT}\n"
            f"# Log_Path: {log_filename}\n"
            f"#\n"
            f"# Format for break lines:\n"
            f"# BREAK,<time>,<reason>,<details>\n"
            f"#\n"
        )
        self.datafilepointer.write(header)
        self.datafilepointer.write("Timestamp,Trial,StimFile,StimON,StimOFF,Stim_Duration,Target_ITI,Actual_ITI,ITI_Error,EEGConnected\n")
        self.datafilepointer.flush()
        Logger.info(f"Logging to: {log_filename}")

    def end_experiment(self):
        Logger.info("Experiment ending")
        if platform == 'android':
            release_wake_lock()
        if hasattr(self, 'simulator'):
            self.simulator.stop()
        if hasattr(self, 'osc_manager'):
            self.osc_manager.stop_server()
        if hasattr(self, 'datafilepointer'):
            self.datafilepointer.close()
        self.stop()

    def on_start(self):
        Window.fullscreen = "auto"
        self.background_image.opacity = 0
        self.fixation_cross.opacity = 0
        self.white_square.opacity = 0

    def on_window_resize(self, window, width, height):
        self.rect.size = (width, height)
        self.fixation_cross.size = (width * 0.05, height * 0.05)
        self.background_image.size = (width, height)
        
        self.white_square.pos = (width - 110, height - 110)  # Maintain exact corner position
    def build(self):
        return self.layout

if __name__ == "__main__":
    try:
        SimplifiedShamApp().run()
    except Exception as e:
        Logger.error(f'Application Error: {str(e)}')