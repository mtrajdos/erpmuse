from kivy.app import App
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
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
import threading
import socket

class FFP2ScenesApp(App):
    def __init__(self, int_SubNumber, **kwargs):
        super().__init__(**kwargs)
        self.osc_server = OscServer()  # Instantiate the OSC server
        self.int_SubNumber = int_SubNumber
        self.scene_time = None
        self.cross_time = None
        self.int_DurationPic = 0.6  # Duration for picture display
        self.fixation_duration = 0.5  # Duration for fixation cross
        self.current_trial = 0
        self.current_block = 0  # Start with the prebaseline block 0
        self.datafilepointer = None
        self.ITIs = self.generate_random_ITIs(500)  # Generate random ITIs
        self.scene_stimuli = []  # This will hold all the mixed emotional scene images
        self.preloaded_images = {}  # Dictionary to hold preloaded images

        # OSC Client Initialization
        self.client = udp_client.SimpleUDPClient('127.0.0.1', 1337)  # Adjust IP and port as needed

        # Load the stimulus vectors (randomized trial order)
        self.load_vector_file("veclength300.txt")
        self.load_stimuli()

        # Prepare logging
        self.setup_logging()

        # Kivy UI elements
        self.layout = BoxLayout(orientation="vertical")
        self.image = Image(source="background.png")

        # Bind key press event
        Window.bind(on_key_down=self.on_key_down)

    def start_osc_server(self):
        """Starts the OSC server on a separate thread."""
        self.osc_server.start()  # Start the server

    def generate_random_ITIs(self, num_ITIs):
        """Generate random ITIs between 1000ms and 2000ms."""
        return np.random.uniform(1.0, 2.0, num_ITIs)

    def load_vector_file(self, vector_file):
        """Loads the randomized trial order from a file."""
        self.RandVec = np.loadtxt(vector_file, dtype=int).flatten()

    def load_stimuli(self):
        """Loads stimuli from the 'scenes' folder and pre-loads images into memory."""
        self.scene_stimuli = self.load_stimuli_from_folder(
            "StimuliRenamedToPreventAccidentalUseInFFP2Youth/scenes"
        )
        random.shuffle(self.scene_stimuli)
        self.preload_images()

    def load_stimuli_from_folder(self, folder_name):
        """Loads all image files from a folder and returns a list of filenames."""
        stimuli = []
        folder_path = os.path.join(os.path.dirname(__file__), folder_name)
        for filename in os.listdir(folder_path):
            if filename.endswith(".jpg"):
                stimuli.append(filename)
        return stimuli

    def preload_images(self):
        """Pre-loads all images into memory."""
        for filename in self.scene_stimuli:
            image_path = os.path.join(
                "StimuliRenamedToPreventAccidentalUseInFFP2Youth", "scenes", filename
            )
            self.preloaded_images[filename] = Image(source=image_path)

    def setup_logging(self):
        """Sets up the log file for recording trial data."""
        if platform.system() == "Windows":
            log_dir = os.path.join(os.getcwd(), "LogScenes")
        else:
            log_dir = os.path.join("/storage/emulated/0/Download", "LogScenes")

        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        timestamp = datetime.now(pytz.timezone("Europe/Berlin")).strftime("%Y%m%d_%H%M%S")
        log_filename = os.path.join(
            log_dir, f"FFP-{self.int_SubNumber}-{self.current_block}_{timestamp}.txt"
        )

        print(f"Log file created: {log_filename}")
        try:
            self.datafilepointer = open(log_filename, "w")
        except Exception as e:
            print(f"Error opening log file: {e}")

        self.datafilepointer.write(
            "CrossTime\t\tSceneTime\t\tSub_Nr\tBlock\tTrial\tITI\tPic_Duration\tStimulus\n"
        )

    def handle_osc_message(self, address, *args):
        """Handles incoming OSC messages."""
        print(f"Received OSC message: {address} {args}")

    def show_instructions(self):
        """Displays the instruction screens before the trials start."""
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
        
    def show_dynamic_instruction(self):
        """Render dynamic instructions with grey background and centered text."""
        # Clear the layout
        self.layout.clear_widgets()

        # Create a FloatLayout to allow absolute positioning
        float_layout = FloatLayout()

        # Add a grey background
        with float_layout.canvas.before:
            Color(119/255, 119/255, 119/255)  # Set background to grey
            float_layout.rect = Rectangle(size=Window.size)

        # Bind the rectangle size to the window size
        def update_rect(instance, value):
            instance.rect.size = instance.size
        float_layout.bind(size=update_rect)

        # Create the Label with centered text
        instruction_label = Label(
            text="Hello world!",
            font_size='30sp',
            color=(1, 1, 1, 1),  # White text
            size_hint=(None, None),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}  # Center the label
        )

        # Add the Label to the FloatLayout only if it's not already a child
        if instruction_label not in float_layout.children:
            float_layout.add_widget(instruction_label)

        # Add the FloatLayout to the main layout
        self.layout.add_widget(float_layout)

        # Force a layout update
        self.layout.do_layout()

    def show_next_instruction(self):
        """Displays the next instruction image."""
        if self.instruction_index < len(self.instruction_images):
            instr_path = os.path.join(
                os.path.dirname(__file__),
                self.instruction_images[self.instruction_index],
            )
            self.image.source = instr_path
            self.image.reload()
            self.instruction_index += 1
        else:
            self.current_trial = 0  # Reset trial for the new block
            self.schedule_next_trial()  # Proceed to the first trial

    def on_key_down(self, window, key, *args):
        """Handles key press events to move forward in the experiment."""
        if self.instruction_index < len(self.instruction_images):
            self.show_next_instruction()
        elif self.current_block == 4:  # After the final instruction (Instruktion3.jpg)
            self.end_experiment()  # End the experiment when any key is pressed
        else:
            self.schedule_next_trial()

    def schedule_next_trial(self, dt=None):
        """Schedules the next trial, starting with the fixation cross."""
        if self.current_block == 0 and self.current_trial >= 125:  # Pre-baseline block
            np.random.shuffle(self.scene_stimuli)
            self.current_block += 1  # Move to block 1
            self.show_instructions()  # Show end of pre-baseline instructions
            self.current_trial = 0
        elif self.current_block == 1 and self.current_trial >= 125:  # Block 1
            np.random.shuffle(self.scene_stimuli)
            self.current_block += 1  # Move to block 2
            self.show_instructions()  # Show instructions for block 2
            self.current_trial = 0
        elif self.current_block == 2 and self.current_trial >= 125:  # Block 2
            np.random.shuffle(self.scene_stimuli)
            self.current_block += 1  # Move to block 3
            self.show_instructions()  # Show instructions for block 3
            self.current_trial = 0
        elif self.current_block == 3 and self.current_trial >= 125:  # Block 3 (final block)
            self.current_block += 1  # Move to block 4 (but we're actually ending here)
            self.show_instructions()  # Show final instruction (Instruktion3.jpg)
        elif self.current_trial < len(self.RandVec):
            Clock.schedule_once(self.show_fixation_cross, 0)
        else:
            if self.current_block == 4:  # If we are at the end after block 3's instruction
                self.end_experiment()  # End experiment after Instruktion3.jpg is shown
            else:
                self.show_instructions()  # Show instructions for the next block if not finished yet
                self.current_trial = 0  # Reset trial for the new block
        
    def show_fixation_cross(self, dt):
        """Displays a fixation cross before showing the stimulus image."""
        self.layout.clear_widgets()
        with self.layout.canvas.before:
            Color(119 / 255, 119 / 255, 119 / 255)  # Set background to grey
            self.rect = Rectangle(size=self.layout.size, pos=self.layout.pos)
        self.image = Image(source="fixation_cross.png", allow_stretch=False, keep_ratio=True)
        self.layout.add_widget(self.image)
        
        # Get the current time for CrossTime
        now = datetime.now(pytz.timezone("Europe/Berlin"))
        self.cross_time = now.timestamp()  # Store CrossTime

        Clock.schedule_once(self.show_trial, self.fixation_duration)
        
    def show_trial(self, dt):
        """Displays the stimulus image for the current trial."""
        if self.current_trial >= len(self.scene_stimuli):
            print(f"Error: Trial index {self.current_trial} exceeds the number of stimuli ({len(self.scene_stimuli)}).")
            self.end_experiment()
            return

        self.timestamp = datetime.now(pytz.timezone("Europe/Berlin"))  # Retrieve time for log filename
        stim_file = self.scene_stimuli[self.current_trial]

        self.current_trial += 1
        self.layout.clear_widgets()
        self.image = self.preloaded_images[stim_file]
        self.layout.add_widget(self.image)
        
        # Get current time including milliseconds and microseconds for SceneTime
        now = datetime.now(pytz.timezone("Europe/Berlin"))
        self.scene_time = now.timestamp()  # This will include milliseconds and microseconds
        self.ITI = self.ITIs[self.current_trial]  # Assign ITI for this trial

        # Prepare log entry with CrossTime and SceneTime
        log_entry = f"{self.cross_time:.6f}\t{self.scene_time:.6f}\t{self.int_SubNumber}\t{self.current_block}\t{self.current_trial}\t{self.ITI:.6f}\t{self.int_DurationPic}\t\t{stim_file}\n"
        self.datafilepointer.write(log_entry)

        print(f"Logged: {log_entry.strip()}")  # Debugging statement to see what is logged

        Clock.schedule_once(self.log_data_and_schedule_next, self.int_DurationPic)
        
    def log_data_and_schedule_next(self, dt):
        """Logs the data for the current trial and schedules the next."""
        self.datafilepointer.flush()  # Ensure data is written to disk
        self.schedule_next_trial()

    def end_experiment(self):
        """Ends the experiment and closes the log file."""
        if self.datafilepointer is not None:
            self.datafilepointer.close()
        self.stop()
        print("Experiment finished. Goodbye!")
        
    def on_start(self):
        """Starts the experiment and sets the app to fullscreen mode."""
        Window.fullscreen = "auto"  # Set to true fullscreen
        self.start_osc_server()  # Start OSC server
        self.show_instructions()

    def on_stop(self):
        """Stops the OSC server when the app exits."""
        if self.osc_server:
            self.osc_server.server.shutdown()  # Gracefully shut down the OSC server
            self.osc_server.server.server_close()  # Close the socket
            print("OSC server stopped.")

    def build(self):
        """Builds the Kivy layout and returns it."""
        return self.layout

if __name__ == "__main__":
    FFP2ScenesApp(1).run()