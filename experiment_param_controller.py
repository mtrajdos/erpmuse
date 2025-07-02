"""Controls experiment parameters, timing, ISIs, and localization"""
import numpy as np
import textwrap

class ExperimentParamController:
    def __init__(self):
        # Timing configuration
        self.stim_duration = 0.600000  # 600ms
        self.isi_min = 1.000000
        self.isi_max = 3.000000
        self.total_trials = 50000
        
        # Generate ISIs
        self.isis = np.random.uniform(self.isi_min, self.isi_max, self.total_trials)
        
        # Language settings
        self.current_language = "EN"
        
        # Localization strings
        self.texts = {
            'DE': {
                'instructions': (
                    "Verschiedene Bilder werden auf dem Bildschirm vor Ihnen gezeigt. "
                    "Bitte betrachten Sie diese aufmerksam. Richten Sie Ihren Blick stets "
                    "auf den roten Kreuz in der Mitte des Bildschirms und versuchen Sie "
                    "dabei möglichst still zu sitzen. Wenn Sie Fragen haben, können Sie "
                    "diese jetzt stellen. Ansonsten tippen Sie irgendwo auf den Bildschirm, "
                    "wenn Sie startbereit sind."
                ),
                'disconnect': (
                    "Verbindung unterbrochen\n\n"
                    "Warten auf EEG-Signal...\n\n"
                    "Das Experiment wird automatisch fortgesetzt,\n"
                    "sobald die Verbindung wiederhergestellt ist."
                )
            },
            'PL': {
                'instructions': (
                    "Zostaną Państwu pokazane różne obrazy na ekranie przed Państwem. "
                    "Proszę uważnie je obserwować. Proszę zawsze patrzeć na czerwony "
                    "krzyż w centrum ekranu i starać się siedzieć jak najspokojniej. "
                    "Jeśli mają Państwo pytania, można je zadać teraz. W przeciwnym "
                    "razie proszę dotknąć ekran w dowolnym miejscu, aby rozpocząć."
                ),
                'disconnect': (
                    "Połączenie przerwane\n\n"
                    "Oczekiwanie na sygnał EEG...\n\n"
                    "Eksperyment zostanie automatycznie wznowiony\n"
                    "po przywróceniu połączenia."
                )
            },
            'EN': {
                'instructions': (
                    "Various images will be shown to you on the screen in front of you. "
                    "Please observe these carefully. Keep your gaze always on the red "
                    "cross in the center of the screen and try to sit as still as "
                    "possible. If you have questions, you can ask them now. Otherwise, "
                    "please tap anywhere on the screen to start."
                ),
                'disconnect': (
                    "Connection Interrupted\n\n"
                    "Waiting for EEG signal...\n\n"
                    "The experiment will resume automatically\n"
                    "when connection is restored."
                )
            }
        }
    
    def set_language(self, language):
        """Set the current language"""
        if language in self.texts:
            self.current_language = language
    
    def get_text(self, key):
        """Get localized text for a key"""
        return self.texts.get(self.current_language, {}).get(key, '')
    
    def get_wrapped_text(self, key):
        """Get wrapped version of localized text"""
        text = self.get_text(key)
        return textwrap.fill(text)
    
    def get_isi(self, trial_index):
        """Get ISI for a specific trial"""
        if 0 <= trial_index < len(self.isis):
            return self.isis[trial_index]
        return self.isi_min
    
    def get_experiment_params(self):
        """Get all experiment parameters for logging"""
        return {
            'stim_duration': self.stim_duration,
            'isi_min': self.isi_min,
            'isi_max': self.isi_max,
            'total_trials': self.total_trials,
            'total_images': 0  # Will be updated by flow controller
        }