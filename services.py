"""Central service locator for shared instances"""

class Services:
    """Container for application services"""
    _osc_receiver = None
    
    @classmethod
    def get_osc_receiver(cls):
        """Get or create the OSC receiver instance"""
        if cls._osc_receiver is None:
            from osc_receiver import OSCReceiver
            cls._osc_receiver = OSCReceiver()
        return cls._osc_receiver
    
    @classmethod
    def start_all(cls):
        """Initialize and start all services"""
        cls.get_osc_receiver().start()
    
    @classmethod
    def stop_all(cls):
        """Stop all services"""
        if cls._osc_receiver:
            cls._osc_receiver.stop()
    # Test comment