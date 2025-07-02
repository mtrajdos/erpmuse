"""Handles all experiment data logging"""
import os
import time
from datetime import datetime
import pytz
import platform
from kivy.logger import Logger

class ExperimentLogger:
    def __init__(self, config):
        self.config = config
        self.log_file = None
        self.log_file_path = None
        self.experiment_start_time = None
        
    def initialize(self, experiment_params):
        """Initialize logging system with POSIX timestamps"""
        os.makedirs(self.config.LOG_DIR, exist_ok=True)
        
        # Create log file with timestamp
        timestamp = datetime.now(pytz.timezone("Europe/Berlin")).strftime("%Y%m%d_%H%M%S")
        self.log_file_path = os.path.join(self.config.LOG_DIR, f"EmoScenes_{timestamp}.txt")
        self.log_file = open(self.log_file_path, "w")
        
        # Record experiment start time
        self.experiment_start_time = time.time()
        
        # Write header
        header = self._create_header(experiment_params)
        self.log_file.write(header)
        self.log_file.write("Timestamp,BlockTrial,StimFile,StimON,StimOFF,Stim_Duration,Target_ISI,Actual_ISI,ISI_Error\n")
        self.log_file.flush()
        
        Logger.info(f"Experiment logger initialized: {self.log_file_path}")
        
    def _create_header(self, params):
        """Create log file header with experiment information"""
        return (
            f"# Experiment Info:\n"
            f"# POSIX_Start: {self.experiment_start_time:.6f}\n"
            f"# System_Time: {datetime.now(pytz.timezone('Europe/Berlin')).strftime('%Y%m%d_%H%M%S')}\n"
            f"# Platform: {platform.system()}\n"
            f"# Mobile_Platform: {self.config.IS_MOBILE}\n"
            f"# ISI_Range: {params['isi_min']:.6f} - {params['isi_max']:.6f}\n"
            f"# Images_N: {params['total_images']}\n"
            f"# Log_Path: {self.log_file_path}\n"
            f"# VSync: Enabled\n"
            f"# Target_Stim_Duration: {params['stim_duration']:.6f}\n"
            f"#\n"
            f"# Format for break lines:\n"
            f"# BREAK,<POSIX_time>,<reason>,<details>\n"
            f"#\n"
        )
    
    def log_trial(self, trial_data):
        """Log trial data to file"""
        if not self.log_file:
            Logger.error("Attempted to log trial before initialization")
            return
            
        log_entry = (
            f"{trial_data['timestamp']:.6f},"
            f"{trial_data['block_trial']},"
            f"{trial_data['stim_file']},"
            f"{trial_data['stim_on']:.6f},"
            f"{trial_data['stim_off']:.6f},"
            f"{trial_data['stim_duration']:.6f},"
            f"{trial_data['target_isi']:.6f},"
            f"{trial_data['actual_isi']:.6f},"
            f"{trial_data['isi_error']:.6f}\n"
        )
        
        self.log_file.write(log_entry)
        self.log_file.flush()
    
    def log_break(self, reason, details):
        """Log experiment break/pause events"""
        if not self.log_file:
            return
            
        break_time = time.time()
        log_entry = f"BREAK,{break_time:.6f},{reason},{details}\n"
        self.log_file.write(log_entry)
        self.log_file.flush()
        
        Logger.info(f"Break logged: {reason} - {details}")
    
    def close(self):
        """Close log file"""
        if self.log_file:
            self.log_file.close()
            Logger.info(f"Log file closed: {self.log_file_path}")