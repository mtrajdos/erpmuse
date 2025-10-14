# config.py
"""Centralized configuration for the experiment"""
import os
from kivy.utils import platform as kivy_platform

class Config:    
    # =================== EXPERIMENT MODE ===================
    # Set this to True for ultra-fast testing
    SPEED_TEST_MODE = True
    
    # =================== TIMING PARAMETERS ===================
    if SPEED_TEST_MODE:
        # Speed test mode timing (in seconds)
        STIM_DURATION = 0.300
        ISI_MIN = 0.025
        ISI_MAX = 0.050
        OSC_TIMEOUT_THRESHOLD = 1.0
        CONNECTION_CHECK_INTERVAL = 0.100
    else:
        # Normal mode timing (in seconds)
        STIM_DURATION = 0.600
        ISI_MIN = 1.000
        ISI_MAX = 3.000
        OSC_TIMEOUT_THRESHOLD = 0.500
        CONNECTION_CHECK_INTERVAL = 0.050
    
    # Total trials (buffer)
    TOTAL_TRIALS = 50000
    
    # =================== PERFORMANCE FLAGS ===================
    ENABLE_CONNECTION_MONITORING = not SPEED_TEST_MODE
    SCHEDULE_DISPLAY_DELAY = 0  # Always immediate display
    
    # =================== WINDOW CONFIG ===================
    WINDOW_BORDERLESS = True
    FULLSCREEN_MODE = 'auto'
    VSYNC_ENABLED = '1'
    MAX_FPS = '0'  # Uncap FPS
    
    # =================== UI CONFIG ===================
    FIXATION_SIZE_RATIO = 0.05
    INSTRUCTION_FONT_SIZE = '24sp'
    INSTRUCTION_TEXT_WIDTH_RATIO = 0.8
    SQUARE_SIZE = (150, 150)
    BACKGROUND_COLOR = (119/255, 119/255, 119/255)
    CONNECTION_RESUME_DELAY = 0.5
    
    # =================== EXPERIMENT CONFIG ===================
    CATEGORIES = ['highneg', 'lowneg', 'neutral', 'lowpos', 'highpos']
    STIMULI_PER_CATEGORY = 25
    TOTAL_BLOCKS = 400  # Fixed value, not calculated
    
    # Category to brightness square mapping
    CATEGORY_TO_SQUARE = {
        'highpos': 'square_255',
        'lowpos': 'square_255',
        'neutral': 'square_255',
        'lowneg': 'square_0',
        'highneg': 'square_0'
    }
    
    # =================== PATHS ===================
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    STIMULI_FOLDER = os.path.join(BASE_DIR, "stimuli")
    SPRITES_FOLDER = os.path.join(BASE_DIR, "sprites")
    
    # Platform-specific paths
    if kivy_platform in ('android', 'ios'):
        LOG_DIR = "/storage/emulated/0/Download/logs"
        IS_MOBILE = True
    else:
        LOG_DIR = os.path.join(os.getcwd(), "logs")
        IS_MOBILE = False