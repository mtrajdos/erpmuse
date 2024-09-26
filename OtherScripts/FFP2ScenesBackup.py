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

class FFP2ScenesApp(App):
    def __init__(self, int_SubNumber, int_Block, **kwargs):
        super().__init__(**kwargs)
        self.int_SubNumber = int_SubNumber
        self.int_Block = int_Block
        self.int_DurationPic = 0.6  # Duration for picture display
        self.fixation_duration = 0.5  # Duration for fixation cross
        self.current_trial = 0
        self.datafilepointer = None
        self.ITIs = self.generate_random_ITIs(375)  # Generate random ITIs
        self.scene_stimuli = []  # This will hold all the mixed emotional scene images
        self.preloaded_images = {}  # Dictionary to hold preloaded images

        # Load the stimulus vectors (randomized trial order)
        self.load_vector_file("veclength300.txt")
        self.load_stimuli()

        # Prepare logging
        self.setup_logging()

        # Kivy UI elements
        self.layout = BoxLayout(orientation='vertical')
        self.image = KivyImage(size_hint=(1, 1), allow_stretch=True, keep_ratio=False)  # Make image fill the window
        self.layout.add_widget(self.image)

        # Bind key press event
        Window.bind(on_key_down=self.on_key_down)

    def generate_random_ITIs(self, num_ITIs):
        """Generate random ITIs between 1000ms and 2000ms."""
        return np.random.uniform(1.0, 2.0, num_ITIs)

    def load_vector_file(self, vector_file):
        """Loads the randomized trial order from a file."""
        self.RandVec = np.loadtxt(vector_file, dtype=int).flatten()

    def load_stimuli(self):
        """Loads stimuli from the 'scenes' folder and pre-loads images into memory."""
        self.scene_stimuli = self.load_stimuli_from_folder('StimuliRenamedToPreventAccidentalUseInFFP2Youth/scenes')
        random.shuffle(self.scene_stimuli)  # Randomize the order of emotional scene images
        self.preload_images()  # Pre-load all images into memory

    def load_stimuli_from_folder(self, folder_name):
        """Loads all image files from a folder and returns a list of filenames."""
        stimuli = []
        folder_path = os.path.join(os.path.dirname(__file__), folder_name)
        for filename in os.listdir(folder_path):
            if filename.endswith('.jpg'):
                stimuli.append(filename)  # Store only filename, not full path
        return stimuli

    def preload_images(self):
        """Pre-loads all images into memory."""
        for filename in self.scene_stimuli:
            image_path = os.path.join('StimuliRenamedToPreventAccidentalUseInFFP2Youth', 'scenes', filename)
            self.preloaded_images[filename] = KivyImage(source=image_path)  # Pre-load image

    def setup_logging(self):
        """Sets up the log file for recording trial data.""" 
        log_dir = os.path.join(os.getcwd(), 'LogScenes')  # Get the LogScenes folder in the current directory
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)  # Create the folder if it doesn't exist
        timestamp = datetime.now(pytz.timezone('Europe/Berlin')).strftime('%Y%m%d_%H%M%S')  # Adjust for your timezone
        log_filename = os.path.join(log_dir, f'FFP-{self.int_SubNumber}-{self.int_Block}_{timestamp}.txt')
        self.datafilepointer = open(log_filename, 'w')
        # Write header to log file
        self.datafilepointer.write('Date\t\tTime\t\tSub_Nr\tBlock\tTrial\tITI\tPic_Duration\tStimulus\n')

    def on_start(self):
        """Starts the experiment and sets the app to fullscreen mode.""" 
        Window.fullscreen = 'auto'  # Set to true fullscreen
        self.show_instructions()

    def show_instructions(self):
        """Displays the instruction screens before the trials start.""" 
        instruction_images = [
            'Instruktion_prebaseline1.jpg',
            'Instruktion_prebaseline2.jpg'
        ]
        self.instruction_index = 0
        self.instruction_images = instruction_images
        self.show_next_instruction()

    def show_next_instruction(self):
        """Displays the next instruction image.""" 
        if self.instruction_index < len(self.instruction_images):
            instr_path = os.path.join(os.path.dirname(__file__), self.instruction_images[self.instruction_index])
            self.image.source = instr_path
            self.image.reload()
            self.instruction_index += 1
        else:
            self.schedule_next_trial()  # Proceed to the first trial

    def on_key_down(self, window, key, *args):
        """Handles key press events to move forward in the experiment.""" 
        if self.instruction_index < len(self.instruction_images):
            self.show_next_instruction()
        else:
            self.schedule_next_trial()

    def schedule_next_trial(self, dt=None):
        """Schedules the next trial, starting with the fixation cross.""" 
        if self.current_trial < len(self.RandVec):
            Clock.schedule_once(self.show_fixation_cross, 0)
        else:
            self.end_experiment()

    def show_fixation_cross(self, dt):
        """Displays a fixation cross before showing the stimulus image.""" 
        with self.layout.canvas.before:
            Color(119/255, 119/255, 119/255)  # Set background to grey
            self.rect = Rectangle(size=self.layout.size, pos=self.layout.pos)
        self.image.source = 'fixation_cross.png'  # Ensure this image is available
        self.image.allow_stretch = False  # Prevent scaling for fixation cross
        self.image.keep_ratio = True  # Maintain aspect ratio for fixation cross
        self.image.reload()
        Clock.schedule_once(self.show_trial, self.fixation_duration)

    def show_trial(self, dt):
        """Displays the stimulus image for the current trial.""" 
        self.timestamp = datetime.now(pytz.timezone('Europe/Berlin'))  # Retrieve current time for logging
        stim_file = self.scene_stimuli[self.current_trial]
        self.current_trial += 1
        self.image.source = self.preloaded_images[stim_file].source  # Use preloaded image
        self.image.allow_stretch = True  # Allow stretching for scene images
        self.image.keep_ratio = False  # Do not maintain aspect ratio for scene images
        self.image.reload()
        Clock.schedule_once(self.log_data_and_schedule_next, self.int_DurationPic)

    def log_data_and_schedule_next(self, dt):
        """Logs the data for the current trial and schedules the next.""" 
        date_str = self.timestamp.strftime('%Y-%m-%d')
        time_str = self.timestamp.strftime('%H:%M:%S.%f')[:-3]  # Log with millisecond precision
        try:
            stimulus_filename = self.scene_stimuli[self.current_trial - 1]
            self.ITI = self.ITIs[self.current_trial - 1]  # Assign ITI for this trial
            log_entry = f'{date_str}\t{time_str}\t{self.int_SubNumber}\t{self.int_Block}\t{self.current_trial}\t{self.ITI:.3f}\t{self.int_DurationPic}\t\t{stimulus_filename}\n'
            self.datafilepointer.write(log_entry)
            self.datafilepointer.flush()  # Ensure data is written to file
        except Exception as e:
            print(f"Error writing to log file: {e}")
        self.schedule_next_trial()

    def end_experiment(self):
        """Closes the log file and ends the experiment.""" 
        self.datafilepointer.close()
        self.image.source = ""
        self.image.reload()

    def build(self):
        """Builds the Kivy layout and returns it.""" 
        return self.layout

if __name__ == '__main__':
    FFP2ScenesApp(1, 0).run()
