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

class TouchableFloatLayout(FloatLayout):
    def on_touch_down(self, touch):
        app = App.get_running_app()
        if app:
            app.handle_touch()
        return super().on_touch_down(touch)

class SimplifiedEmoScenes(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.initialize_variables()
        self.setup_ui()
        self.setup_logging()
        Window.bind(on_resize=self.on_window_resize)
        
    def initialize_variables(self):
        self.stim_duration = 0.600000
        self.current_trial = 1
        self.last_stim_off_time = None
        self.current_stim_on_time = None
        self.scene_stimuli = [f'checkerboard{brightness}.png' for brightness in [255, 225, 195, 175, 155]] * 125
        random.shuffle(self.scene_stimuli)
        self.showing_background = True
        self.ITIs = np.random.uniform(2.000000, 4.000000, 625)
        self.next_trial_scheduled = False
        self.trial_running = False

    def handle_touch(self):
        if self.showing_background:
            self.start_experiment()
        elif not self.showing_background:
            self.end_experiment()

    def start_experiment(self):
        """Initial experiment start after first touch"""
        self.showing_background = False
        self.fixation_cross.opacity = 1
        # Show fixation for first ITI duration before first trial
        Clock.schedule_once(self.show_trial, self.ITIs[0])

    def show_trial(self, dt):
        if self.trial_running:
            return
            
        self.trial_running = True
        
        # Prepare and show stimulus
        self.background_image.source = os.path.join(os.path.dirname(__file__), "sprites", self.scene_stimuli[self.current_trial - 1])
        self.background_image.reload()
        
        def show_stimulus(dt):
            self.background_image.opacity = 1
            self.white_square.opacity = 1
            self.white_square.pos = (Window.width - self.white_square.width, 0)
            self.current_stim_on_time = time.time()
            Clock.schedule_once(self.end_trial, self.stim_duration)
            
        Clock.schedule_once(show_stimulus, 0)

    def log_trial_data(self):
        now = time.time()  # Unix timestamp
        stim_on = self.current_stim_on_time
        stim_off = self.current_stim_off_time
        target_iti = self.ITIs[self.current_trial - 1]
        
        actual_iti = 0
        if self.last_stim_off_time:
            actual_iti = stim_on - self.last_stim_off_time
        
        iti_error = actual_iti - target_iti
        stim_file = self.scene_stimuli[self.current_trial - 1]
        
        # Calculate actual stimulus duration
        actual_stim_duration = stim_off - stim_on
        
        log_entry = (f"{now:.6f},"           # Timestamp
                    f"{self.current_trial},"  # Trial
                    f"{stim_file},"           # StimFile
                    f"{stim_on:.6f},"         # StimON
                    f"{stim_off:.6f},"        # StimOFF
                    f"{actual_stim_duration:.6f}," # Stim_Duration (actual)
                    f"{target_iti:.6f},"      # Target_ITI
                    f"{actual_iti:.6f},"      # Actual_ITI
                    f"{iti_error:.6f}\n")     # ITI_Error
                    
        self.datafilepointer.write(log_entry)
        self.datafilepointer.flush()

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
            size=(55, 55),
            pos=(Window.width - 55, 0),
            allow_stretch=False,
            keep_ratio=True,
            opacity=0
        )

        self.layout.add_widget(self.background_image)
        self.layout.add_widget(self.white_square)
        self.layout.add_widget(self.fixation_cross)

    def setup_logging(self):
        log_dir = os.path.join(os.getcwd(), "logs") if platform.system() == "Windows" else os.path.join("/storage/emulated/0/Download", "logs")
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now(pytz.timezone("Europe/Berlin")).strftime("%Y%m%d_%H%M%S")
        log_filename = os.path.join(log_dir, f"ShamScenes_{timestamp}.txt")
        self.datafilepointer = open(log_filename, "w")
        self.datafilepointer.write("Timestamp,Trial,StimFile,StimON,StimOFF,Stim_Duration,Target_ITI,Actual_ITI,ITI_Error\n")

    def end_experiment(self):
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
        self.white_square.pos = (width - self.white_square.width, 0)

    def build(self):
        return self.layout

if __name__ == "__main__":
    try:
        SimplifiedEmoScenes().run()
    except Exception as e:
        Logger.error(f'Application Error: {str(e)}')