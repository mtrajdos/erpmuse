"""General configuration constants and paths for the experiment"""
import os
from kivy.utils import platform as kivy_platform

class Config:
    # Window configuration
    WINDOW_BORDERLESS = True
    FULLSCREEN_MODE = 'auto'
    VSYNC_ENABLED = '1'
    MAX_FPS = '0'  # Uncap FPS
    
    # UI configuration
    FIXATION_SIZE_RATIO = 0.05
    INSTRUCTION_FONT_SIZE = '24sp'
    INSTRUCTION_TEXT_WIDTH_RATIO = 0.8
    SQUARE_SIZE = (150, 150)
    BACKGROUND_COLOR = (119/255, 119/255, 119/255)
    
    # Experiment configuration
    CATEGORIES = ['highneg', 'lowneg', 'neutral', 'lowpos', 'highpos']
    STIMULI_PER_CATEGORY = 25
    TOTAL_BLOCKS = 400
    
    # Category to brightness square mapping
    CATEGORY_TO_SQUARE = {
        'highpos': 'square_255',
        'lowpos': 'square_255',
        'neutral': 'square_255',
        'lowneg': 'square_255',
        'highneg': 'square_255'
    }
    
    # Paths
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
    
    # Connection monitoring
    CONNECTION_CHECK_INTERVAL = 0.008  # 125Hz
    CONNECTION_RESUME_DELAY = 0.5