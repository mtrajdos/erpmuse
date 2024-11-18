from kivy.app import App
from kivy.uix.image import Image as KivyImage
from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.logger import Logger
import numpy as np
import os
from datetime import datetime
import pytz
import random
import platform
import time

class SimplifiedEmoScenes(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.initialize_variables()
        self.setup_ui()
        self.load_data()
        self.setup_logging()
        Window.bind(on_key_down=self.on_key_down)
        Window.bind(on_resize=self.on_window_resize)

    def initialize_variables(self):
        print("Initializing EmoScenes")
        # Timing variables
        self.scene_time = None
        self.cross_time = None
        self.int_DurationPic = 0.600000
        self.estimated_processing_time = 0.020000

        # Trial tracking
        self.current_trial = 1
        self.current_block = 0
        self.last_trial_end_time = None
        self.last_scene_time = None
        self.trial_start_time = None
        self.intended_iti = None
        self.next_trial_scheduled = False

        # Data structures
        self.scene_stimuli = ['checkerboard.png'] * 125
        self.preloaded_images = {}
        self.preloaded_instructions = {}
        self.showing_instructions = False
        self.ITIs = self.generate_random_ITIs(500)

        # Asset paths
        self.fixation_path = "sprites/fixation_cross.png"
        self.square_path = "sprites/red_square.png"

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

    def load_data(self):
        self.preload_instruction_images()
        self.preload_images()

    def preload_instruction_images(self):
        instruction_sets = {
            0: ["background.png", "Instruktion_prebaseline1.jpg", "Instruktion_prebaseline2.jpg"],
            1: ["Instruktion1.jpg", "Instruktion2.jpg"],
            2: ["Instruktion2.jpg"],
            3: ["Instruktion2.jpg"],
            4: ["Instruktion3.jpg"]
        }
        
        for block, instructions in instruction_sets.items():
            for instr in instructions:
                instr_path = os.path.join(os.path.dirname(__file__), "instructionsDE", instr)
                if os.path.exists(instr_path):
                    self.preloaded_instructions[instr] = KivyImage(source=instr_path)

    def preload_images(self):
        self.preloaded_images['checkerboard.png'] = KivyImage(source='sprites/checkerboard.png', allow_stretch=True, keep_ratio=False)

    def generate_random_ITIs(self, num_ITIs):
        print(f"Generating {num_ITIs} random ITIs")
        return np.random.uniform(1.000000, 5.000000, num_ITIs)

    def setup_logging(self):
        print("Setting up logging")
        log_dir = os.path.join(os.getcwd(), "logs") if platform.system() == "Windows" else os.path.join("/storage/emulated/0/Download", "logs")
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now(pytz.timezone("Europe/Berlin")).strftime("%Y%m%d_%H%M%S")
        log_filename = os.path.join(log_dir, f"ShamScenes_{timestamp}.txt")
        try:
            self.datafilepointer = open(log_filename, "w")
            self.datafilepointer.write("CrossTime,SceneTime,PicDuration,Target_ITI,Actual_ITI,ITI_Error,Block,Trial,Stimulus\n")
            print(f"Log file created: {log_filename}")
        except Exception as e:
            print(f"Error opening log file: {e}")

    def on_start(self):
        print("Application starting")
        Window.fullscreen = "auto"
        self.show_instructions()

    def show_instructions(self):
        print(f"Showing instructions for block {self.current_block}")
        self.showing_instructions = True
        self.instruction_images = self.get_instruction_images()
        self.instruction_index = 0
        # Ensure cross is hidden before showing instructions
        self.fixation_cross.opacity = 0
        self.show_next_instruction()

    def get_instruction_images(self):
        if self.current_block == 0:
            return ["background.png", "Instruktion_prebaseline1.jpg", "Instruktion_prebaseline2.jpg"]
        elif self.current_block == 1:
            return ["Instruktion1.jpg", "Instruktion2.jpg"]
        elif self.current_block in [2, 3]:
            return ["Instruktion2.jpg"]
        elif self.current_block == 4:
            return ["Instruktion3.jpg"]
        return []

    def show_next_instruction(self):
        if self.instruction_index < len(self.instruction_images):
            instr_file = self.instruction_images[self.instruction_index]
            if instr_file in self.preloaded_instructions:
                # Hide fixation cross and square during instructions
                self.fixation_cross.opacity = 0
                self.white_square.opacity = 0
                
                # Show instruction on background image
                self.background_image.opacity = 1
                self.background_image.source = os.path.join(os.path.dirname(__file__), "instructionsDE", instr_file)
                self.background_image.reload()
                
                print(f"Showing instruction {self.instruction_index + 1} of {len(self.instruction_images)}")
            else:
                print(f"Error: Instruction image not found: {instr_file}")
            self.instruction_index += 1
        else:
            print("All instructions shown. Transitioning to trials.")
            self.showing_instructions = False
            # Show the fixation cross immediately after instructions end
            self.background_image.opacity = 0
            self.fixation_cross.opacity = 1
            self.white_square.opacity = 0  # Ensure square is hidden
            self.schedule_next_trial()

    def on_key_down(self, window, key, *args):
        print(f"Key pressed: {key}")
        if self.showing_instructions:
            self.show_next_instruction()
        elif self.current_block == 4:
            self.end_experiment()
        elif not self.next_trial_scheduled:
            self.schedule_next_trial()

    def schedule_next_trial(self, dt=None):
        if self.next_trial_scheduled:
            return

        print(f"Scheduling trial {self.current_trial} in block {self.current_block}")
        current_time = time.time()
        
        if self.last_trial_end_time is not None:
            actual_iti = current_time - self.last_trial_end_time
            print(f"Actual ITI: {actual_iti:.6f} seconds")

        if self.current_trial > 125:
            self.transition_to_next_block()
            return

        if self.current_trial <= len(self.scene_stimuli):
            self.intended_iti = self.ITIs[self.current_trial - 1]
            fixation_duration = max(0.100000, self.intended_iti - self.int_DurationPic - self.estimated_processing_time)
            print(f"Intended ITI: {self.intended_iti:.6f} s, Adjusted fixation duration: {fixation_duration:.6f} s")
            Clock.schedule_once(lambda dt: self.show_fixation_cross(fixation_duration), 0)
            self.next_trial_scheduled = True
        else:
            print("Error: Ran out of stimuli before block completion")
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
        
        self.cross_time = datetime.now(pytz.timezone("Europe/Berlin")).timestamp()
        Clock.schedule_once(self.show_trial, duration)

    def show_trial(self, dt):
        self.trial_start_time = time.time()

        # Show the fixed checkerboard image
        self.background_image.opacity = 1
        self.background_image.source = os.path.join(os.path.dirname(__file__), "sprites", "checkerboard.png")
        self.background_image.reload()

        # Show the red square in the bottom right corner
        self.fixation_cross.opacity = 1
        self.white_square.opacity = 1
        self.white_square.pos = (Window.width - self.white_square.width, 0)

        self.log_trial_data("checkerboard.png")
        Clock.schedule_once(self.end_trial, self.int_DurationPic)

    def log_trial_data(self, stim_file):
        now = datetime.now(pytz.timezone("Europe/Berlin"))
        self.scene_time = now.timestamp()
        target_iti = self.ITIs[self.current_trial - 1]
        actual_iti = self.scene_time - self.last_scene_time if self.last_scene_time is not None else 0
        self.last_scene_time = self.scene_time
        iti_error = actual_iti - target_iti
        log_entry = f"{self.cross_time:.6f},{self.scene_time:.6f},{self.int_DurationPic:.6f},{target_iti:.6f},{actual_iti:.6f},{iti_error:.6f},{self.current_block},{self.current_trial},{stim_file}\n"
        self.datafilepointer.write(log_entry)
        print(f"Logged: {log_entry.strip()}")

    def end_trial(self, dt):
        self.datafilepointer.flush()
        
        # Check if this is trial 125 (end of block)
        if self.current_trial == 125:
            # Hide all visual elements after 600ms
            self.background_image.opacity = 0
            self.fixation_cross.opacity = 0
            self.white_square.opacity = 0
            Clock.schedule_once(lambda dt: self.transition_to_next_block(), 0)
        else:
            self.next_trial_scheduled = False
            self.current_trial += 1
            self.schedule_next_trial()

    def transition_to_next_block(self):
        self.current_block += 1
        if self.current_block < 4:
            print(f"Transitioning to block {self.current_block}")
            self.current_trial = 1
            self.show_instructions()
        else:
            self.end_experiment()

    def end_experiment(self):
        print("Ending experiment")
        if self.datafilepointer:
            self.datafilepointer.close()
        self.stop()
        print("Experiment finished. Goodbye!")

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