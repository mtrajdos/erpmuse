from kivy.app import App
from kivy.uix.image import Image as KivyImage
from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.logger import Logger
import numpy as np
import random
import os
from datetime import datetime
import pytz
import platform
import time

class SimplifiedEmoScenes(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.initialize_variables()
        self.setup_ui()
        self.setup_logging()
        Window.bind(on_key_down=self.on_key_down)
        Window.bind(on_resize=self.on_window_resize)

    def initialize_variables(self):
        print("Initializing EmoScenes")
        # Timing variables
        self.stim_on_time = None
        self.stim_off_time = None
        self.stim_duration = 0.600000
        self.estimated_processing_time = 0.007000

        # Trial tracking
        self.current_trial = 0
        self.last_trial_end_time = None
        self.last_stimulus_offset_time = None  
        self.trial_start_time = None
        self.intended_iti = None
        self.next_trial_scheduled = False

        # Data structures
        self.scene_stimuli = [f'checkerboard{brightness}.png' for brightness in [255, 225, 195, 175, 155]] * 125  # Repeat each 125 times
        random.shuffle(self.scene_stimuli)  # Randomize the order
        self.preloaded_images = {}
        self.showing_background = True
        self.ITIs = self.generate_random_ITIs(625)  # Generate 625 ITIs

        # Asset paths
        self.fixation_path = "sprites/fixation_cross.png"
        self.square_path = "sprites/white_square.png"

    def setup_ui(self):
        # Create main layout
        self.layout = FloatLayout()

        # Set up grey background
        with self.layout.canvas.before:
            Color(119/255, 119/255, 119/255)
            self.rect = Rectangle(size=self.layout.size, pos=self.layout.pos)

        # Create background image
        self.background_image = KivyImage(
            size_hint=(1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            allow_stretch=True,
            keep_ratio=False,
            opacity=0
        )

        # Create fixation cross
        self.fixation_cross = KivyImage(
            source=self.fixation_path,
            size_hint=(None, None),
            size=(Window.width * 0.05, Window.height * 0.05),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            allow_stretch=False,
            keep_ratio=True,
            opacity=0
        )

        self.white_square = KivyImage(
            source=self.square_path,
            size_hint=(None, None),
            size=(55, 55),
            pos=(Window.width - 55, 0),
            allow_stretch=False,
            keep_ratio=True,
            opacity=0
        )

        # Add widgets in correct order (background first, overlays last)
        self.layout.add_widget(self.background_image)    # Bottom layer
        self.layout.add_widget(self.white_square)        # Middle layer
        self.layout.add_widget(self.fixation_cross)      # Top layer
        
    def preload_images(self):
        for brightness in [255, 225, 195, 175, 155]:
            image_name = f'checkerboard{brightness}.png'
            self.preloaded_images[image_name] = KivyImage(
                source=os.path.join('sprites', image_name),
                allow_stretch=True,
                keep_ratio=False
            )

    def generate_random_ITIs(self, num_ITIs):
        print(f"Generating {num_ITIs} random ITIs")
        return np.random.uniform(0.010000, 0.020000, num_ITIs)

    def setup_logging(self):
        print("Setting up logging")
        log_dir = os.path.join(os.getcwd(), "logs") if platform.system() == "Windows" else os.path.join("/storage/emulated/0/Download", "logs")
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now(pytz.timezone("Europe/Berlin")).strftime("%Y%m%d_%H%M%S")
        log_filename = os.path.join(log_dir, f"ShamScenes_{timestamp}.txt")
        try:
            self.datafilepointer = open(log_filename, "w")
            self.datafilepointer.write("StimON,StimOFF,StimDuration,Target_ITI,Actual_ITI,ITI_Error,Trial,StimFile\n")
            print(f"Log file created: {log_filename}")
        except Exception as e:
            print(f"Error opening log file: {e}")

    def show_trial(self, dt):
        self.trial_start_time = time.time()
        now = datetime.now(pytz.timezone("Europe/Berlin"))
        self.stim_on_time = now.timestamp()

        # Show the checkerboard image for this trial
        self.background_image.opacity = 1
        self.background_image.source = os.path.join(os.path.dirname(__file__), "sprites", self.scene_stimuli[self.current_trial])
        self.background_image.reload()

        # Show fixation cross and square
        self.fixation_cross.opacity = 1
        self.white_square.opacity = 1
        self.white_square.pos = (Window.width - self.white_square.width, 0)

        Clock.schedule_once(self.end_trial, self.stim_duration)

    def log_trial_data(self, stim_file):
        self.stim_off_time = datetime.now(pytz.timezone("Europe/Berlin")).timestamp()
        target_iti = self.ITIs[self.current_trial - 1]
        
        # Calculate actual ITI (from last stimulus offset to current stimulus onset plus stimulus duration)
        if self.last_stimulus_offset_time is not None:
            # Add stimulus duration to match the target ITI definition
            actual_iti = (self.stim_on_time - self.last_stimulus_offset_time) + self.stim_duration
        else:
            actual_iti = 0
        
        iti_error = actual_iti - target_iti
        log_entry = f"{self.stim_on_time:.6f},{self.stim_off_time:.6f},{self.stim_duration:.6f},{target_iti:.6f},{actual_iti:.6f},{iti_error:.6f},{self.current_trial},{stim_file}\n"
        self.datafilepointer.write(log_entry)
        print(f"Logged: {log_entry.strip()}")
        
        # Store the stimulus offset time for next trial's ITI calculation
        self.last_stimulus_offset_time = self.stim_off_time

    def end_trial(self, dt):
        self.log_trial_data(self.scene_stimuli[self.current_trial])
        self.datafilepointer.flush()

        if self.current_trial == 624:  # Since we start from 0
            self.datafilepointer.flush()
            self.background_image.opacity = 0
            self.fixation_cross.opacity = 0
            self.white_square.opacity = 0
            Clock.schedule_once(lambda dt: self.end_experiment(), 0)
        else:
            self.next_trial_scheduled = False
            self.current_trial += 1
            self.schedule_next_trial()
            
    def on_key_down(self, window, key, *args):
        print(f"Key pressed: {key}")
        if self.showing_background:
            self.showing_background = False
            self.schedule_next_trial()
        elif not self.next_trial_scheduled:
            self.schedule_next_trial()

    def schedule_next_trial(self, dt=None):
        if self.next_trial_scheduled:
            return

        print(f"Scheduling trial {self.current_trial}")
        current_time = time.time()

        if self.current_trial == 625:
            self.end_experiment()
            return

        if self.current_trial < 625:
            self.intended_iti = self.ITIs[self.current_trial]
            fixation_duration = max(0.100000, self.intended_iti - self.stim_duration - self.estimated_processing_time)
            print(f"Intended ITI: {self.intended_iti:.6f} s, Adjusted fixation duration: {fixation_duration:.6f} s")
            Clock.schedule_once(lambda dt: self.show_fixation_cross(fixation_duration), 0)
            self.next_trial_scheduled = True
        else:
            print("Error: Ran out of stimuli")
            self.end_experiment()

        self.last_trial_end_time = current_time

    def show_fixation_cross(self, duration):
        print(f"Showing fixation cross for {duration:.6f} seconds")
        # Ensure grey background
        with self.layout.canvas.before:
            Color(119 / 255, 119 / 255, 119 / 255)
            self.rect = Rectangle(size=self.layout.size, pos=self.layout.pos)
        
        # Show fixation cross, hide square
        self.fixation_cross.opacity = 1
        self.white_square.opacity = 0
        self.fixation_cross.size = (Window.width * 0.05, Window.height * 0.05)
        
        # Hide background image but maintain grey background
        self.background_image.opacity = 0
        
        Clock.schedule_once(self.show_trial, duration)

    def transition_to_next_block(self):
        self.current_block += 1
        if self.current_block < 4:
            print(f"Transitioning to block {self.current_block}")
            self.current_trial = 0
            self.show_instructions()
        else:
            self.end_experiment()

    def end_experiment(self):
        print("Ending experiment")
        if self.datafilepointer:
            self.datafilepointer.close()
        self.stop()
        print("Experiment finished. Goodbye!")
        
    def on_start(self):
        print("Application starting")
        Window.fullscreen = "auto"
        # Show just the grey background initially
        self.background_image.opacity = 0
        self.fixation_cross.opacity = 0
        self.white_square.opacity = 0

    def on_stop(self):
        print("Stopping application")

    def on_window_resize(self, window, width, height):
        self.fixation_cross.size = (width * 0.05, height * 0.05)
        self.background_image.size = (width, height)
        self.white_square.pos = (width - self.white_square.width, 0)

    def build(self):
        return self.layout

if __name__ == "__main__":
    try:
        SimplifiedEmoScenes().run()
    except Exception as e:
        Logger.error(f'Application Error: {str(e)}')