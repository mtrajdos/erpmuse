from kivy.app import App
from kivy.uix.image import Image as KivyImage
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
import numpy as np
import os
from datetime import datetime
import pytz
import random
import platform
from oscServer import OscServer
from pythonosc import udp_client
import time

# Initialize EmoScenes class
#
# osc_server                OSC server object for receiving data/logging packets
# int_SubNumber             subject number
# scene_time                duration of stimulus
# cross_time                timestamp of displaying fixation cross
# int_DurationPic           duration of stimulus
# current_trial             counter of current trial number for logging
# current_block             counter of current block for logging
# datafilepointer           for writing log lines
# ITIs                      array holding generated random ITIs
# scene_stimuli             array of scene filenames to be displayed
# preloaded_images          dictionary for preloading all scenes for performance
# client                    client object for specifying IP and port for OSC
# layout                    Kivy BoxLayout for displaying stuff in the EmoScenes app
# image                     Image object for rendering instructions/scenes into it, filling the screen without keeping
#                           the original image file proportions
# last_trial_end_time       for timestamping when previous trial ended
# last_scene_time           for timestamping when stimulus was displayed in the previous trial
# trial_start_time          for timestamping when new trial has begun
# intended_iti              target ITI based on the random ITI value determined for current trial
# next_trial_scheduled      boolean for flagging whether upcoming trial is scheduled or not
# estimated_processing_time estimate for processing involving timestamping, loading trials and writing into log file
#                           calculated based on test trial logs and used for adjusting stimulus display accuracy

class EmoScenes(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.scene_time = None
        self.cross_time = None
        self.int_DurationPic = 0.600000
        self.current_trial = 0
        self.client = udp_client.SimpleUDPClient('127.0.0.1', 1337)
        self.last_trial_end_time = None
        self.last_scene_time = None
        self.trial_start_time = None
        self.intended_iti = None
        self.next_trial_scheduled = False
        self.estimated_processing_time = 0.020000
        self.scene_stimuli = []
        self.preloaded_images = {}
        self.osc_server = OscServer()
        self.current_block = 0
        self.datafilepointer = None
        self.layout = BoxLayout(orientation="horizontal")
        self.image = KivyImage(size_hint=(1, 1), allow_stretch=True, keep_ratio=False)
        self.layout.add_widget(self.image)
        self.load_vector_file("veclength300.txt")
        self.load_stimuli()
        self.setup_logging()
        Window.bind(on_key_down=self.on_key_down)
        self.ITIs = self.generate_random_ITIs(500)

    def start_osc_server(self):
        self.osc_server.start()

    def generate_random_ITIs(self, num_ITIs):
        return np.random.uniform(1.000000, 3.000000, num_ITIs)

    def load_vector_file(self, vector_file):
        self.RandVec = np.loadtxt(vector_file, dtype=int).flatten()

    def load_stimuli(self):
        self.scene_stimuli = self.load_stimuli_from_folder(
            "StimuliRenamedToPreventAccidentalUseInFFP2Youth/scenes"
        )
        self.preload_images()

    def load_stimuli_from_folder(self, folder_name):
        stimuli = []
        folder_path = os.path.join(os.path.dirname(__file__), folder_name)
        for filename in os.listdir(folder_path):
            if filename.endswith(".jpg"):
                stimuli.append(filename)
        return stimuli

    def preload_images(self):
        for filename in self.scene_stimuli:
            image_path = os.path.join(
                "StimuliRenamedToPreventAccidentalUseInFFP2Youth", "scenes", filename
            )
            self.preloaded_images[filename] = KivyImage(source=image_path)

    def setup_logging(self):
        if platform.system() == "Windows":
            log_dir = os.path.join(os.getcwd(), "LogScenes")
        else:
            log_dir = os.path.join("/storage/emulated/0/Download", "LogScenes")

        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        timestamp = datetime.now(pytz.timezone("Europe/Berlin")).strftime("%Y%m%d_%H%M%S")
        log_filename = os.path.join(
            log_dir, f"FFP-{self.current_block}_{timestamp}.txt"
        )

        print(f"Log file created: {log_filename}")
        try:
            self.datafilepointer = open(log_filename, "w")
        except Exception as e:
            print(f"Error opening log file: {e}")

        self.datafilepointer.write(
            "CrossTime,SceneTime,PicDuration,Target_ITI,Actual_ITI,ITI_Error,Block,Trial,Stimulus\n"
        )

    def handle_osc_message(self, address, *args):
        print(f"Received OSC message: {address} {args}")

    def on_start(self):
        Window.fullscreen = "auto"
        self.start_osc_server()
        self.show_instructions()

    def show_instructions(self):
        if self.current_block == 0:
            self.instruction_images = [
                "Instruktion_prebaseline1.jpg",
                "Instruktion_prebaseline2.jpg",
            ]
        elif self.current_block == 1:
            self.instruction_images = ["Instruktion1.jpg", "Instruktion2.jpg"]
        elif self.current_block == 2:
            self.instruction_images = ["Instruktion2.jpg"]
        elif self.current_block == 3:
            self.instruction_images = ["Instruktion2.jpg"]
        elif self.current_block == 4:
            self.instruction_images = ["Instruktion3.jpg"]
        self.instruction_index = 0
        self.show_next_instruction()

    def show_next_instruction(self):
        if self.instruction_index < len(self.instruction_images):
            instr_path = os.path.join(
                os.path.dirname(__file__),
                self.instruction_images[self.instruction_index],
            )
            self.image.source = instr_path
            self.image.reload()
            self.instruction_index += 1
        else:
            self.current_trial = 0
            self.schedule_next_trial()

    def on_key_down(self, window, key, *args):
        if self.instruction_index < len(self.instruction_images):
            self.show_next_instruction()
        elif self.current_block == 4:
            self.end_experiment()
        else:
            if not self.next_trial_scheduled:
                self.schedule_next_trial()

    def schedule_next_trial(self, dt=None):
        if self.next_trial_scheduled:
            return

        current_time = time.time()
        if self.last_trial_end_time is not None:
            actual_iti = current_time - self.last_trial_end_time
            print(f"Actual ITI: {actual_iti:.6f} seconds")
        else:
            actual_iti = 0

        if self.current_block == 0 and self.current_trial >= 125:
            np.random.shuffle(self.scene_stimuli)
            self.current_block += 1
            self.show_instructions()
            self.current_trial = 0
        elif self.current_block == 1 and self.current_trial >= 125:
            np.random.shuffle(self.scene_stimuli)
            self.current_block += 1
            self.show_instructions()
            self.current_trial = 0
        elif self.current_block == 2 and self.current_trial >= 125:
            np.random.shuffle(self.scene_stimuli)
            self.current_block += 1
            self.show_instructions()
            self.current_trial = 0
        elif self.current_block == 3 and self.current_trial >= 125:
            self.current_block += 1
            self.show_instructions()
        elif self.current_trial < len(self.RandVec):
            self.intended_iti = self.ITIs[self.current_trial]
            print(f"Intended ITI for next trial: {self.intended_iti:.6f} seconds")
            
            # Calculate fixation duration including compensation for stimulus duration and processing time
            fixation_duration = max(0.100000, self.intended_iti - self.int_DurationPic - self.estimated_processing_time)
            
            print(f"Adjusted fixation duration: {fixation_duration:.6f} seconds")
            
            Clock.schedule_once(lambda dt: self.show_fixation_cross(fixation_duration), 0)
            self.next_trial_scheduled = True
        else:
            if self.current_block == 4:
                self.end_experiment()
            else:
                self.show_instructions()
                self.current_trial = 0

        self.last_trial_end_time = current_time

    def show_fixation_cross(self, duration):
        print(f"Showing fixation cross for {duration:.6f} seconds")
        with self.layout.canvas.before:
            Color(119 / 255, 119 / 255, 119 / 255)
            self.rect = Rectangle(size=self.layout.size, pos=self.layout.pos)
        self.image.source = "fixation_cross.png"
        self.image.allow_stretch = False
        self.image.keep_ratio = True
        self.image.reload()
        
        now = datetime.now(pytz.timezone("Europe/Berlin"))
        self.cross_time = now.timestamp()

        Clock.schedule_once(self.show_trial, duration)
        
    def show_trial(self, dt):
        print("Showing trial stimulus")
        self.trial_start_time = time.time()
        if self.current_trial >= len(self.scene_stimuli):
            print(f"Error: Trial index {self.current_trial} exceeds the number of stimuli ({len(self.scene_stimuli)}).")
            self.end_experiment()
            return

        self.timestamp = datetime.now(pytz.timezone("Europe/Berlin"))
        stim_file = self.scene_stimuli[self.current_trial]

        self.current_trial += 1
        self.image.source = self.preloaded_images[stim_file].source
        self.image.allow_stretch = True
        self.image.keep_ratio = False
        self.image.reload()
        
        now = datetime.now(pytz.timezone("Europe/Berlin"))
        self.scene_time = now.timestamp()
        target_iti = self.ITIs[self.current_trial - 1]

        actual_iti = self.scene_time - self.last_scene_time if self.last_scene_time is not None else 0
        self.last_scene_time = self.scene_time

        iti_error = actual_iti - target_iti

        log_entry = f"{self.cross_time:.6f},{self.scene_time:.6f},{self.int_DurationPic:.6f},{target_iti:.6f},{actual_iti:.6f},{iti_error:.6f},{self.current_block},{self.current_trial},{stim_file}\n"
        self.datafilepointer.write(log_entry)

        print(f"Logged: {log_entry.strip()}")

        Clock.schedule_once(self.end_trial, self.int_DurationPic)
        
    def end_trial(self, dt):
        print("Ending trial and scheduling next")
        self.datafilepointer.flush()
        self.next_trial_scheduled = False
        self.schedule_next_trial()

    def end_experiment(self):
        if self.datafilepointer is not None:
            self.datafilepointer.close()
        self.stop()
        print("Experiment finished. Goodbye!")

    def on_stop(self):
        if self.osc_server:
            self.osc_server.server.shutdown()
            self.osc_server.server.server_close()
            print("OSC server stopped.")

    def build(self):
        return self.layout

if __name__ == "__main__":
    EmoScenes().run()