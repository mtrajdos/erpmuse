"""Monitors EEG/OSC connection status"""
from kivy.clock import Clock
from kivy.logger import Logger

class ConnectionMonitor:
    def __init__(self, osc_receiver, config):
        self.osc_receiver = osc_receiver
        self.config = config
        
        # Monitoring state
        self.monitoring_event = None
        self.connection_lost_screen_active = False
        
        # Callbacks
        self.on_connection_lost = None
        self.on_connection_restored = None
        
    def start_monitoring(self):
        """Start monitoring connection at configured interval"""
        if not self.monitoring_event:
            self.monitoring_event = Clock.schedule_interval(
                self._check_connection,
                self.config.CONNECTION_CHECK_INTERVAL
            )
            Logger.info("Connection monitoring started")
    
    def stop_monitoring(self):
        """Stop monitoring connection"""
        if self.monitoring_event:
            self.monitoring_event.cancel()
            self.monitoring_event = None
            Logger.info("Connection monitoring stopped")
    
    def _check_connection(self, dt):
        """Check connection status and trigger callbacks"""
        is_connected = self.osc_receiver.is_connected()
        
        if not is_connected and not self.connection_lost_screen_active:
            # Connection lost
            self.connection_lost_screen_active = True
            if self.on_connection_lost:
                self.on_connection_lost()
                
        elif is_connected and self.connection_lost_screen_active:
            # Connection restored
            self.connection_lost_screen_active = False
            if self.on_connection_restored:
                self.on_connection_restored()
    
    def is_connected(self):
        """Check if currently connected"""
        return self.osc_receiver.is_connected()
    
    def set_callbacks(self, on_lost, on_restored):
        """Set connection event callbacks"""
        self.on_connection_lost = on_lost
        self.on_connection_restored = on_restored