"""Main application entry point"""
import traceback

from kivy.config import Config as KivyConfig
from kivy.core.window import Window
from kivy.app import App
from kivy.logger import Logger
from kivy.utils import platform as kivy_platform

# Import modules - use clear names
from config import Config as AppConfig
from experiment_logger import ExperimentLogger
from experiment_flow_controller import ExperimentFlowController
from experiment_param_controller import ExperimentParamController
from ui_controller import UIController
from connection_monitor import ConnectionMonitor
from stimuli_analyzer import StimuliAnalyzer
from services import Services

# Window configuration (use KivyConfig instead of Config)
Window.borderless = True
KivyConfig.set('graphics', 'fullscreen', 'auto')
KivyConfig.set('graphics', 'vsync', '1')
KivyConfig.set('graphics', 'maxfps', '0')
KivyConfig.write()

class EmoScenes(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Initialize configuration FIRST
        self.config = AppConfig()
        
        # Start services
        Services.start_all()
        
        # Initialize stimuli analyzer
        self.stimuli_analyzer = StimuliAnalyzer()
        
        # Initialize controllers
        self.param_controller = ExperimentParamController(self.config)
        self.logger = ExperimentLogger(self.config)
        self.ui_controller = UIController(self.config, self.param_controller)
        
        # Create connection monitor with the OSC receiver from Services
        self.connection_monitor = ConnectionMonitor(
            Services.get_osc_receiver(),  # Use Services
            self.config
        )
        
        # Initialize flow controller with dependencies
        self.flow_controller = ExperimentFlowController(
            self.config,
            self.ui_controller,
            self.logger,
            self.connection_monitor
        )
        
        # Setup platform specifics
        self._setup_platform()
        
        # Setup callbacks
        self._setup_callbacks()
        
        # OSC receiver is already started by Services.start_all()
        
    def _setup_platform(self):
        """Configure platform-specific settings"""
        if self.config.IS_MOBILE and kivy_platform == 'android':
            try:
                from jnius import autoclass
                Process = autoclass('android.os.Process')
                Process.setThreadPriority(Process.THREAD_PRIORITY_URGENT_DISPLAY)
                Logger.info("Set Android thread priority to URGENT_DISPLAY")
            except Exception as e:
                Logger.warning(f"Could not set Android priority: {e}")
    
    def _setup_callbacks(self):
        """Setup inter-module callbacks"""
        # Connection monitor callbacks
        self.connection_monitor.set_callbacks(
            on_lost=self.flow_controller.pause_experiment,
            on_restored=self.flow_controller.resume_experiment
        )
        
        # Flow controller callbacks
        self.flow_controller.on_experiment_end = self.end_experiment
        
        # UI touch handler
        self.ui_controller.set_touch_handler(self.flow_controller.handle_touch)
    
    def build(self):
        """Build the app UI"""
        return self.ui_controller.layout
    
    def on_start(self):
        """Called when app starts"""
        Window.fullscreen = "auto"
        
        # Run stimuli complexity analysis BEFORE experiment initialization
        Logger.info("Running stimuli complexity and brightness analysis...")
        try:
            self.stimuli_analyzer.analyze_all_categories()
        except Exception as e:
            Logger.error(f"Error during stimuli analysis: {e}")
        
        # Initialize experiment parameters
        experiment_params = self.param_controller.get_experiment_params()
        self.flow_controller.initialize(experiment_params)
        
        # Initialize logger
        self.logger.initialize(experiment_params)
        
        # Initialize flow controller
        self.flow_controller.initialize(self.param_controller)
        
        # Update total images count for logging
        experiment_params['total_images'] = len(self.flow_controller.preloaded_images)
        
        # Show instructions
        self.ui_controller.show_instructions()
        
        Logger.info("Application started")
    
    def end_experiment(self):
        """Clean up and end the experiment"""
        Logger.info("Ending experiment")
        
        # Stop monitoring
        self.connection_monitor.stop_monitoring()
        
        # Stop OSC receiver through Services
        Services.stop_all()  # Use Services
        
        # Close logger
        self.logger.close()
        
        # Exit app
        self.stop()

if __name__ == "__main__":
    try:
        EmoScenes().run()
    except Exception as e:
        print("=" * 60)
        print("FULL TRACEBACK:")
        print("=" * 60)
        traceback.print_exc()
        print("=" * 60)
        Logger.error(f'Application Error: {str(e)}')
        raise  # Re-raise to see Kivy's error handling too