"""Controls the experimental flow, stimulus presentation, and trial management"""
import os
import random
import time
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.uix.image import Image as KivyImage
import numpy as np

class ExperimentFlowController:
    def __init__(self, config, ui_controller, logger, connection_monitor):
        self.config = config
        self.ui_controller = ui_controller
        self.logger = logger
        self.connection_monitor = connection_monitor
        
        # Experiment state
        self.current_trial = 1
        self.last_stim_off_time = None
        self.current_stim_on_time = None
        self.current_stim_off_time = None
        self.in_instruction_phase = True
        self.in_experiment_phase = False
        self.paused = False
        self.pause_start_time = None
        
        # Trial scheduling
        self.next_trial_scheduled = None
        self.stimulus_currently_displayed = False
        self.current_square = None
        
        # Stimulus data
        self.stimuli = {
            'categories': self.config.CATEGORIES,
            'per_category': self.config.STIMULI_PER_CATEGORY,
            'files_per_category': {},
            'sequence': [],
            'all_files': [],
            'folder': self.config.STIMULI_FOLDER
        }
        
        # Preloaded images
        self.preloaded_images = {}
        
        # Timing diagnostics
        self.timing_diagnostics = []
        self.schedule_time = None
        self.requested_duration = None
        
    def initialize(self, experiment_params):
        """Initialize experiment flow with parameters"""
        self.experiment_params = experiment_params
        self.load_and_categorize_stimulus_files()
        self.create_randomized_stimulus_sequence()
        self.preload_images()
        
    def load_and_categorize_stimulus_files(self):
        """Load and categorize all stimulus files"""
        # Initialize category lists
        for category in self.stimuli['categories']:
            self.stimuli['files_per_category'][category] = []
        
        # Check stimuli folder exists
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
        
        # Log counts
        for category in self.stimuli['categories']:
            count = len(self.stimuli['files_per_category'][category])
            Logger.info(f"Loaded {count} stimuli for category: {category}")
    
    def create_randomized_stimulus_sequence(self):
        """Create randomized sequence of stimulus blocks"""
        self.stimuli['sequence'] = []
        
        # Create randomized blocks
        for _ in range(self.config.TOTAL_BLOCKS):
            block_stimuli = []
            
            # Sample from each category
            for category in self.stimuli['categories']:
                available = self.stimuli['files_per_category'][category]
                needed = self.stimuli['per_category']
                
                if len(available) >= needed:
                    selected = random.sample(available, needed)
                    block_stimuli.extend(selected)
                else:
                    Logger.warning(f"Category {category} has only {len(available)} stimuli")
                    block_stimuli.extend(available)
            
            # Shuffle block
            random.shuffle(block_stimuli)
            self.stimuli['sequence'].extend(block_stimuli)
        
        Logger.info(f"Created sequence with {len(self.stimuli['sequence'])} stimuli")
    
    def preload_images(self):
        """Preload all stimulus images into memory"""
        # Load stimulus images
        for stim_file in set(self.stimuli['sequence']):
            image_path = os.path.join(self.stimuli['folder'], stim_file)
            if os.path.exists(image_path):
                self.preloaded_images[stim_file] = KivyImage(
                    source=image_path,
                    allow_stretch=True,
                    keep_ratio=False
                )
        
        # Also preload UI square images
        self.ui_controller.preload_square_images(self.preloaded_images)
        
        Logger.info(f"Preloaded {len(self.preloaded_images)} images")
    
    def start_experiment(self):
        """Start the experiment after instruction phase"""
        self.in_instruction_phase = False
        self.in_experiment_phase = True
        
        # Hide instructions and show fixation
        self.ui_controller.hide_instructions()
        self.ui_controller.show_fixation_cross()
        
        # Start connection monitoring
        self.connection_monitor.start_monitoring()
        
        # Schedule first trial
        first_isi = self.experiment_params.get_isi(0)
        Clock.schedule_once(self.prepare_trial, first_isi)
        Logger.info(f"Experiment started, first ISI: {first_isi:.6f}")
    
    def prepare_trial(self, dt):
        """Prepare and display stimulus for current trial"""
        # Check if paused or already displaying
        if self.paused or self.stimulus_currently_displayed:
            return
        
        # Check if experiment complete
        if self.current_trial > len(self.stimuli['sequence']):
            self.end_experiment()
            return
            
        self.stimulus_currently_displayed = True
        self.next_trial_scheduled = None
        
        # Get current stimulus
        current_stim = self.stimuli['sequence'][self.current_trial - 1]
        if current_stim not in self.preloaded_images:
            Logger.error(f"Image not preloaded: {current_stim}")
            return
        
        # Get stimulus category and square
        category = self.get_stimulus_category(current_stim)
        square_name = self.config.CATEGORY_TO_SQUARE.get(category)
        self.current_square = self.ui_controller.get_square_widget(square_name)
        
        # Schedule stimulus display on next frame
        Clock.schedule_once(lambda dt: self.display_stimulus(current_stim), 0)
    
    def display_stimulus(self, stimulus_file):
        """Display the stimulus"""
        if self.paused:
            self.stimulus_currently_displayed = False
            return
        
        # Show stimulus
        texture = self.preloaded_images[stimulus_file].texture
        self.ui_controller.show_stimulus(texture, self.current_square)
        self.current_stim_on_time = time.time()
        
        # Store timing info for diagnostics
        self.schedule_time = time.time()
        self.requested_duration = self.experiment_params.stim_duration
        
        # Schedule stimulus end
        Clock.schedule_once(self.complete_trial, self.experiment_params.stim_duration)
        
        Logger.info(f"Trial {self.current_trial}: Displaying {stimulus_file}")
    
    def complete_trial(self, dt):
        """Complete current trial and schedule next"""
        if self.paused:
            return
        
        # Record timing
        self.current_stim_off_time = time.time()
        
        # Log trial data
        self._log_current_trial()
        
        # Hide stimulus
        self.ui_controller.hide_stimulus(self.current_square)
        
        self.last_stim_off_time = self.current_stim_off_time
        self.stimulus_currently_displayed = False
        
        # Check if complete
        if self.current_trial >= len(self.stimuli['sequence']):
            self.ui_controller.hide_fixation_cross()
            Clock.schedule_once(lambda dt: self.end_experiment(), 0)
        else:
            # Calculate next ISI with drift compensation
            next_isi = self._calculate_next_isi()
            self.current_trial += 1
            
            # Schedule next trial
            self.next_trial_scheduled = Clock.schedule_once(self.prepare_trial, next_isi)
    
    def _calculate_next_isi(self):
        """Calculate next ISI with drift compensation"""
        next_isi = self.experiment_params.get_isi(self.current_trial)
        
        if self.last_stim_off_time and self.current_stim_on_time:
            actual_duration = self.current_stim_off_time - self.current_stim_on_time
            duration_drift = actual_duration - self.experiment_params.stim_duration
            adjusted_isi = max(0.100000, next_isi - duration_drift)
        else:
            adjusted_isi = next_isi
            
        return adjusted_isi
    
    def _log_current_trial(self):
        """Log data for current trial"""
        if not self.connection_monitor.is_connected():
            Logger.warning(f"Skipping log for trial {self.current_trial} - no connection")
            return
        
        # Prepare trial data
        trial_data = {
            'timestamp': time.time(),
            'block_trial': f"t{self.current_trial:03d}",
            'stim_file': self.stimuli['sequence'][self.current_trial - 1],
            'stim_on': self.current_stim_on_time,
            'stim_off': self.current_stim_off_time,
            'stim_duration': self.current_stim_off_time - self.current_stim_on_time,
            'target_isi': self.experiment_params.get_isi(self.current_trial - 1),
            'actual_isi': 0,
            'isi_error': 0
        }
        
        # Calculate actual ISI
        if self.last_stim_off_time:
            trial_data['actual_isi'] = self.current_stim_on_time - self.last_stim_off_time
            trial_data['isi_error'] = trial_data['actual_isi'] - trial_data['target_isi']
        
        self.logger.log_trial(trial_data)
    
    def pause_experiment(self):
        """Pause experiment"""
        if self.paused:
            return
            
        self.paused = True
        self.pause_start_time = time.time()
        
        # Cancel scheduled trial
        if self.next_trial_scheduled:
            self.next_trial_scheduled.cancel()
            self.next_trial_scheduled = None
        
        # Hide experiment elements
        self.ui_controller.hide_all_experiment_elements()
        self.ui_controller.show_connection_lost_screen()
        
        self.stimulus_currently_displayed = False
        
        # Log pause
        self.logger.log_break("CONNECTION_LOST", "EEG_stream_interrupted")
        Logger.warning("Experiment paused")
    
    def resume_experiment(self):
        """Resume experiment after pause"""
        if not self.paused:
            return
            
        pause_duration = time.time() - self.pause_start_time
        self.paused = False
        
        # Hide interruption screen and show fixation
        self.ui_controller.hide_connection_lost_screen()
        self.ui_controller.show_fixation_cross()
        
        # Log resume
        self.logger.log_break("CONNECTION_RESTORED", f"pause_duration={pause_duration:.6f}")
        Logger.info(f"Experiment resumed after {pause_duration:.2f}s pause")
        
        # Resume with next trial
        if not self.stimulus_currently_displayed and self.current_trial <= len(self.stimuli['sequence']):
            self.next_trial_scheduled = Clock.schedule_once(
                self.prepare_trial, 
                self.config.CONNECTION_RESUME_DELAY
            )
    
    def get_stimulus_category(self, stimulus_file):
        """Extract category from stimulus filename"""
        for category in self.stimuli['categories']:
            if category in stimulus_file.lower():
                return category
        return 'neutral'
    
    def end_experiment(self):
        """End the experiment"""
        Logger.info("Experiment ending")
        self.in_experiment_phase = False
        
        # Print timing summary if available
        if self.timing_diagnostics:
            self._print_timing_summary()
        
        # Signal end
        if hasattr(self, 'on_experiment_end'):
            self.on_experiment_end()
    
    def _print_timing_summary(self):
        """Print timing diagnostics summary"""
        Logger.info("=== Timing Summary ===")
        # Implementation of timing summary
        pass
    
    def handle_touch(self, touch):
        """Handle touch events"""
        if self.connection_monitor.connection_lost_screen_active:
            return
            
        if not touch.is_double_tap and not self.in_experiment_phase:
            self.start_experiment()
        elif touch.is_double_tap:
            self.end_experiment()