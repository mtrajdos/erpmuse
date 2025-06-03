from kivy.config import Config
Config.set('graphics', 'fullscreen', 'auto')
Config.write()

from kivy.core.window import Window
Window.borderless = True

from kivy.app import App
from kivy.uix.image import Image as KivyImage
from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.logger import Logger
import numpy as np
import os
from datetime import datetime
import pytz
import platform
import time
import random

class TouchableFloatLayout(FloatLayout):
    def on_touch_down(self, touch):
        app = App.get_running_app()
        if app:
            app.handle_touch()
        return super().on_touch_down(touch)

class EmoScenes(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.initialize_variables()
        self.setup_ui()
        self.setup_logging()
        Window.bind(on_resize=self.on_window_resize)
        self.paused = False

    def initialize_variables(self):
        self.stim_duration = 0.006000
        self.current_trial = 1
        self.last_stim_off_time = None
        self.current_stim_on_time = None
        self.showing_background = True
        
        # Lower and upper bounds of ISI range, and count of ISIs to randomize (limiting the total number of trials)
        self.ISIs = np.random.uniform(1.000000, 3.000000, 50000)
        
        self.next_trial_scheduled = False
        self.trial_running = False
        self.showing_instructions = True
        
        # Initialize stimuli structure
        self.stimuli = {
            'categories': ['highneg', 'lowneg', 'neutral', 'lowpos', 'highpos'],
            'per_category': 25,
            'files_per_category': {},  # Dict mapping category -> list of files
            'sequence': [],
            'all_files': [],
            'folder': os.path.join(os.path.dirname(__file__), "stimuli")
        }
        
        self.load_stimuli()
        self.randomize_stimuli()
        self.preload_images()

    def setup_ui(self):
        """Setup stable UI with touch support"""
        self.layout = TouchableFloatLayout()

        # Core background from v2.2
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
            pos=(Window.width - 110, 0),
            allow_stretch=False,
            keep_ratio=True,
            opacity=0
        )

        # Add widgets in stable order
        self.layout.add_widget(self.background_image)
        self.layout.add_widget(self.white_square)
        self.layout.add_widget(self.fixation_cross)

    def setup_logging(self):
        """Enhanced logging setup"""
        log_dir = os.path.join(os.getcwd(), "logs") if platform.system() == "Windows" else os.path.join("/storage/emulated/0/Download", "logs")
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now(pytz.timezone("Europe/Berlin")).strftime("%Y%m%d_%H%M%S")
        log_filename = os.path.join(log_dir, f"EmoScenes_{timestamp}.txt")
        self.datafilepointer = open(log_filename, "w")
        
        experiment_start_time = time.time()
        
        header = (
            f"# Experiment Info:\n"
            f"# POSIX_Start: {experiment_start_time:.6f}\n"
            f"# System_Time: {timestamp}\n"
            f"# ISI_Range: {np.min(self.ISIs):.6f} - {np.max(self.ISIs):.6f}\n"
            f"# Images_N: {len(self.preloaded_images)}\n"
            f"# Log_Path: {log_filename}\n"
            f"#\n"
            f"# Format for break lines:\n"
            f"# BREAK,<POSIX_time>,<reason>,<details>\n"
            f"#\n"
        )
        self.datafilepointer.write(header)
        self.datafilepointer.write("Timestamp,BlockTrial,StimFile,StimON,StimOFF,Stim_Duration,Target_ISI,Actual_ISI,ISI_Error\n")
        self.datafilepointer.flush()
        
        self.experiment_start_time = experiment_start_time

    def load_stimuli(self):
        """Load stimuli files and organize by category"""
        # Initialize category dictionary
        for category in self.stimuli['categories']:
            self.stimuli['files_per_category'][category] = []
        
        # Check if stimuli folder exists
        if not os.path.exists(self.stimuli['folder']):
            Logger.error(f"Stimuli folder not found: {self.stimuli['folder']}")
            return
        
        # Load all jpg files
        all_files = os.listdir(self.stimuli['folder'])
        self.stimuli['all_files'] = [f for f in all_files if f.endswith('.jpg')]
        
        # Categorize files
        for file in self.stimuli['all_files']:
            categorized = False
            for category in self.stimuli['categories']:
                if category in file.lower():
                    self.stimuli['files_per_category'][category].append(file)
                    categorized = True
                    break
            
            if not categorized:
                Logger.warning(f"File {file} could not be categorized")
        
        # Log loaded stimuli
        for category in self.stimuli['categories']:
            count = len(self.stimuli['files_per_category'][category])
            Logger.info(f"Loaded {count} stimuli for category: {category}")

    def randomize_stimuli(self):
        """Randomize stimuli sequence from loaded files"""
        block_stimuli = []
        
        # Sample from each category
        for category in self.stimuli['categories']:
            available = self.stimuli['files_per_category'][category]
            needed = self.stimuli['per_category']
            
            if len(available) >= needed:
                selected = random.sample(available, needed)
                block_stimuli.extend(selected)
            else:
                Logger.warning(f"Category {category} has only {len(available)} stimuli, needed {needed}")
                block_stimuli.extend(available)
        
        # Shuffle the block
        random.shuffle(block_stimuli)
        
        # Create extended sequence
        self.stimuli['sequence'] = block_stimuli * 1000
        
        Logger.info(f"Created stimulus sequence with {len(block_stimuli)} unique stimuli")

    def preload_images(self):
        """Stable image preloading"""
        self.preloaded_images = {}
        
        instruction_path = os.path.join(os.path.dirname(__file__), "instructionsDE", "Instruktion1.jpg")
        if os.path.exists(instruction_path):
            self.preloaded_images["instruction1"] = KivyImage(
                source=instruction_path,
                allow_stretch=True,
                keep_ratio=False
            )
        
        for stim_file in set(self.stimuli['sequence']):
            image_path = os.path.join(self.stimuli['folder'], stim_file)
            if os.path.exists(image_path):
                self.preloaded_images[stim_file] = KivyImage(
                    source=image_path,
                    allow_stretch=True,
                    keep_ratio=False
                )

    def handle_touch(self):
        """Touch-based flow control"""
        if self.showing_instructions:
            self.show_next_instruction()
        elif self.showing_background:
            self.start_experiment()
        elif not self.showing_background:
            self.end_experiment()

    def show_trial(self, dt):
        """Stable trial display with enhanced timing"""
        if self.trial_running:
            return
                
        intended_start = time.time()
        self.trial_running = True

        current_stim = self.stimuli['sequence'][self.current_trial - 1]
        if current_stim in self.preloaded_images:
            self.background_image.texture = self.preloaded_images[current_stim].texture
        else:
            Logger.error(f"Image not preloaded: {current_stim}")
            return

        prep_overhead = time.time() - intended_start
        
        def show_stimulus(dt):
            self.background_image.opacity = 1
            self.white_square.opacity = 1
            self.white_square.pos = (Window.width - self.white_square.width, 0)
            self.current_stim_on_time = time.time()
            adjusted_duration = max(0, self.stim_duration - prep_overhead)
            Clock.schedule_once(self.end_trial, adjusted_duration)
        
        Clock.schedule_once(show_stimulus, 0)

    def end_trial(self, dt):
        """Stable trial ending with enhanced logging"""
        self.current_stim_off_time = time.time()
        self.log_trial_data()
        
        self.background_image.opacity = 0
        self.white_square.opacity = 0
        
        self.last_stim_off_time = self.current_stim_off_time
        self.trial_running = False
        
        if self.current_trial == len(self.stimuli['sequence']):
            self.fixation_cross.opacity = 0
            Clock.schedule_once(lambda dt: self.end_experiment(), 0)
        else:
            next_isi = self.ISIs[self.current_trial]
            if self.last_stim_off_time and self.current_stim_on_time:
                actual_duration = self.current_stim_off_time - self.current_stim_on_time
                duration_drift = actual_duration - self.stim_duration
                adjusted_isi = max(0.100000, next_isi - duration_drift)
            else:
                adjusted_isi = next_isi
                
            self.current_trial += 1
            
            if self.current_trial == 125:
                self.randomize_stimuli()
            
            Clock.schedule_once(self.show_trial, adjusted_isi)

    def on_window_resize(self, window, width, height):
        """Stable window resizing"""
        self.rect.size = (width, height)
        self.fixation_cross.size = (width * 0.05, height * 0.05)
        self.background_image.size = (width, height)
        self.white_square.pos = (width - self.white_square.width, 0)

    def build(self):
        return self.layout
    
    def show_instructions(self):
        self.showing_instructions = True
        self.background_image.opacity = 1
        if "instruction1" in self.preloaded_images:
            self.background_image.texture = self.preloaded_images["instruction1"].texture
        else:
            self.background_image.source = os.path.join(os.path.dirname(__file__), "instructionsDE", "Instruktion1.jpg")
            self.background_image.reload()

    def show_next_instruction(self):
        self.showing_instructions = False
        self.background_image.opacity = 0
        self.fixation_cross.opacity = 0
        self.start_experiment()

    def start_experiment(self):
        """Initial experiment start after first touch"""
        self.showing_background = False
        self.fixation_cross.opacity = 1
        Clock.schedule_once(self.show_trial, self.ISIs[0])
        Logger.info(f"Experiment started, first ISI: {self.ISIs[0]:.6f}")

    def log_trial_data(self):
        now = time.time()
        stim_on = self.current_stim_on_time
        stim_off = self.current_stim_off_time
        target_isi = self.ISIs[self.current_trial - 1]
        
        actual_isi = 0
        if self.last_stim_off_time:
            actual_isi = stim_on - self.last_stim_off_time
        
        isi_error = actual_isi - target_isi
        stim_file = self.stimuli['sequence'][self.current_trial - 1]
        actual_stim_duration = stim_off - stim_on
        
        block_trial = f"t{self.current_trial:03d}"
        
        log_entry = (f"{now:.6f},"               # Timestamp
                    f"{block_trial},"            # Trial
                    f"{stim_file},"              # StimFile
                    f"{stim_on:.6f},"            # StimON
                    f"{stim_off:.6f},"           # StimOFF
                    f"{actual_stim_duration:.6f}," # Stim_Duration
                    f"{target_isi:.6f},"         # Target_ISI
                    f"{actual_isi:.6f},"         # Actual_ISI
                    f"{isi_error:.6f}\n")        # ISI_Error
                    
        self.datafilepointer.write(log_entry)
        self.datafilepointer.flush()

    def end_experiment(self):
        Logger.info("Experiment ending")
        if hasattr(self, 'datafilepointer'):
            self.datafilepointer.close()
        self.stop()

    def on_start(self):
        Window.fullscreen = "auto"
        self.background_image.opacity = 0
        self.fixation_cross.opacity = 0
        self.white_square.opacity = 0
        self.show_instructions()

if __name__ == "__main__":
    try:
        EmoScenes().run()
    except Exception as e:
        Logger.error(f'Application Error: {str(e)}')