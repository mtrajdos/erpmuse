from kivy.app import App
from kivy.uix.image import Image as KivyImage
from kivy.uix.boxlayout import BoxLayout
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
from pythonosc import udp_client
import time

class EmoScenes(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.initialize_variables()
        self.setup_ui()
        self.load_data()
        self.setup_logging()
        Window.bind(on_key_down=self.on_key_down)
        
    def initialize_variables(self):
        print("Initializing EmoScenes")
        self.scene_time = None
        self.cross_time = None
        self.int_DurationPic = 0.600000
        self.current_trial = 1
        self.current_block = 0
        self.client = udp_client.SimpleUDPClient('127.0.0.1', 1337)
        self.last_trial_end_time = None
        self.last_scene_time = None
        self.trial_start_time = None
        self.intended_iti = None
        self.next_trial_scheduled = False
        self.estimated_processing_time = 0.020000
        self.scene_stimuli = []
        self.preloaded_images = {}
        self.showing_instructions = False
        self.ITIs = self.generate_random_ITIs(500)

    def setup_ui(self):
        self.layout = BoxLayout(orientation="horizontal")
        self.image = KivyImage(size_hint=(1, 1), allow_stretch=True, keep_ratio=False)
        self.layout.add_widget(self.image)
        self.fixation_path = "sprites/fixation_cross.png"

    def load_data(self):
        self.load_stimuli_from_folder()
        self.randomize_stimuli()

    def generate_random_ITIs(self, num_ITIs):
        print(f"Generating {num_ITIs} random ITIs")
        return np.random.uniform(1.000000, 3.000000, num_ITIs)
            
    def randomize_stimuli(self):
        print(f"Randomizing stimuli for block {self.current_block}")
        print(f"Number of stimuli before randomization: {len(self.scene_stimuli)}")
        random.shuffle(self.scene_stimuli)
        print(f"Number of stimuli after randomization: {len(self.scene_stimuli)}")
        print(f"First 5 stimuli after randomization: {self.scene_stimuli[:5]}")
        self.preload_images()

    def load_stimuli_from_folder(self, folder_name="stimuli"):
        print(f"Loading stimuli from folder: {folder_name}")
        folder_path = os.path.join(os.path.dirname(__file__), folder_name)
        if not os.path.exists(folder_path):
            print(f"Error: Folder '{folder_path}' does not exist.")
            return
        try:
            all_files = os.listdir(folder_path)
            self.scene_stimuli = [f for f in all_files if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            print(f"Found {len(self.scene_stimuli)} stimuli in {folder_name}")
            if self.scene_stimuli:
                print(f"First 5 stimuli: {self.scene_stimuli[:5]}")
            else:
                print("No stimuli found. Check file extensions and permissions.")
        except Exception as e:
            print(f"Error reading directory: {e}")
        self.preload_images()

    def preload_images(self):
        print(f"Preloading {len(self.scene_stimuli)} images")
        for filename in self.scene_stimuli:
            image_path = os.path.join(os.path.dirname(__file__), "stimuli", filename)
            if os.path.exists(image_path):
                self.preloaded_images[filename] = KivyImage(source=image_path, allow_stretch=True, keep_ratio=False)
            else:
                print(f"Error: Image file not found: {image_path}")
        print(f"Preloaded {len(self.preloaded_images)} images")
        print(f"First 5 preloaded images: {list(self.preloaded_images.keys())[:5]}")

    def setup_logging(self):
        print("Setting up logging")
        log_dir = os.path.join(os.getcwd(), "logs") if platform.system() == "Windows" else os.path.join("/storage/emulated/0/Download", "logs")
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now(pytz.timezone("Europe/Berlin")).strftime("%Y%m%d_%H%M%S")
        log_filename = os.path.join(log_dir, f"FFP-{self.current_block}_{timestamp}.txt")
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

    def start_osc_server(self):
        print("Starting OSC server")
        self.osc_server.start()

    def show_instructions(self):
        print(f"Showing instructions for block {self.current_block}")
        self.showing_instructions = True
        self.instruction_images = self.get_instruction_images()
        self.instruction_index = 0
        self.show_next_instruction()

    def get_instruction_images(self):
        if self.current_block == 0:
            return ["Instruktion_prebaseline1.jpg", "Instruktion_prebaseline2.jpg"]
        elif self.current_block == 1:
            return ["Instruktion1.jpg", "Instruktion2.jpg"]
        elif self.current_block in [2, 3]:
            return ["Instruktion2.jpg"]
        elif self.current_block == 4:
            return ["Instruktion3.jpg"]
        return []

    def show_next_instruction(self):
        if self.instruction_index < len(self.instruction_images):
            instr_path = os.path.join(os.path.dirname(__file__), "instructionsDE", self.instruction_images[self.instruction_index])
            if os.path.exists(instr_path):
                self.image.source = instr_path
                self.image.reload()
                print(f"Showing instruction {self.instruction_index + 1} of {len(self.instruction_images)}")
            else:
                print(f"Error: Instruction image not found: {instr_path}")
            self.instruction_index += 1
        else:
            print("All instructions shown. Transitioning to trials.")
            self.showing_instructions = False
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

    def transition_to_next_block(self):
        self.current_block += 1
        if self.current_block < 4:
            print(f"Transitioning to block {self.current_block}")
            self.randomize_stimuli()
            self.current_trial = 1
            self.show_instructions()
        else:
            self.end_experiment()

    def show_fixation_cross(self, duration):
        print(f"Showing fixation cross for {duration:.6f} seconds")
        with self.layout.canvas.before:
            Color(119 / 255, 119 / 255, 119 / 255)
            self.rect = Rectangle(size=self.layout.size, pos=self.layout.pos)
        self.image.source = self.fixation_path
        self.image.allow_stretch = False
        self.image.keep_ratio = True
        self.image.reload()
        
        self.cross_time = datetime.now(pytz.timezone("Europe/Berlin")).timestamp()
        Clock.schedule_once(self.show_trial, duration)

    def show_trial(self, dt):
        print(f"Showing trial stimulus for trial {self.current_trial} out of 125")
        print(f"Current block: {self.current_block}")
        
        self.trial_start_time = time.time()
        if self.current_trial > len(self.scene_stimuli):
            print(f"Error: Trial index {self.current_trial} exceeds the number of stimuli ({len(self.scene_stimuli)}).")
            self.end_experiment()
            return

        stim_file = self.scene_stimuli[self.current_trial - 1]
        print(f"Current stimulus: {stim_file}")

        if stim_file in self.preloaded_images:
            self.layout.clear_widgets()
            self.image = self.preloaded_images[stim_file]
            self.layout.add_widget(self.image)
            self.image.size = Window.size
            self.image.pos = (0, 0)
            self.image.reload()
            print(f"Loaded and displayed stimulus image: {stim_file}")
        else:
            print(f"Error: Image {stim_file} not found in preloaded images.")
            self.end_trial(0)
            return
        
        self.log_trial_data(stim_file)
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
        print("Ending trial and scheduling next")
        self.datafilepointer.flush()
        self.next_trial_scheduled = False
        self.current_trial += 1
        self.schedule_next_trial()

    def end_experiment(self):
        print("Ending experiment")
        if self.datafilepointer:
            self.datafilepointer.close()
        self.stop()
        print("Experiment finished. Goodbye!")

    def on_stop(self):
        print("Stopping application")

    def on_window_resize(self, window, width, height):
        self.image.size = (width, height)

    def build(self):
        return self.layout

if __name__ == "__main__":
    try:
        EmoScenes().run()
    except Exception as e:
        Logger.error(f'Application Error: {str(e)}')