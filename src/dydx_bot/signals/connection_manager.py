"""ConnectionManager: Singleton WebSocket connection manager for signal engines."""

class ConnectionManager:
    _instance = None

    def __init__(self):
        if ConnectionManager._instance is not None:
            raise Exception("This class is a singleton!")
        ConnectionManager._instance = self
        self.connection = None  # Placeholder for WebSocket connection

    @staticmethod
    def get_instance():
        if ConnectionManager._instance is None:
            ConnectionManager()
        return ConnectionManager._instance

    def connect(self):
        """Establish WebSocket connection."""
        self.connection = "WebSocket Connection Established"  # Mock connection

    def disconnect(self):
        """Close WebSocket connection."""
        self.connection = None

    def is_connected(self):
        """Check if WebSocket connection is active."""
        return self.connection is not None
