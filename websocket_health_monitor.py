"""
WebSocket Health Monitor for dYdX Connections
Monitors connection health and implements reconnection logic
"""
import asyncio
import time
import threading
from typing import Optional, Callable


class WebSocketHealthMonitor:
    """Monitors WebSocket connection health and handles reconnection"""
    
    def __init__(self, websocket_manager, reconnect_callback: Optional[Callable] = None):
        self.websocket_manager = websocket_manager
        self.reconnect_callback = reconnect_callback
        self.last_message_time = time.time()
        self.connection_start_time = time.time()
        self.message_count = 0
        self.reconnection_count = 0
        self.is_monitoring = False
        self._monitor_thread = None
        
        # Connection health thresholds
        self.max_silence_duration = 30  # Max seconds without messages before concern
        self.max_stale_duration = 60   # Max seconds before forced reconnection
        
    def start_monitoring(self):
        """Start the health monitoring thread"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._monitor_thread.start()
            print("🔍 WebSocket health monitoring started")
    
    def stop_monitoring(self):
        """Stop the health monitoring"""
        self.is_monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1)
        print("🔍 WebSocket health monitoring stopped")
    
    def on_message_received(self):
        """Call this when a message is received"""
        self.last_message_time = time.time()
        self.message_count += 1
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                current_time = time.time()
                silence_duration = current_time - self.last_message_time
                connection_age = current_time - self.connection_start_time
                
                # Check for concerning silence
                if silence_duration > self.max_silence_duration:
                    print(f"⚠️  WebSocket silent for {silence_duration:.1f}s (concerning)")
                
                # Check for stale connection requiring reconnection
                if silence_duration > self.max_stale_duration:
                    print(f"❌ WebSocket stale for {silence_duration:.1f}s - attempting reconnection")
                    self._attempt_reconnection()
                
                # Log periodic health stats
                if self.message_count > 0 and self.message_count % 10000 == 0:
                    msg_rate = self.message_count / connection_age if connection_age > 0 else 0
                    print(f"📊 Connection health: {self.message_count} messages, "
                          f"{msg_rate:.1f} msg/s, {connection_age:.1f}s uptime")
                
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                print(f"❌ Health monitor error: {e}")
                time.sleep(5)
    
    def _attempt_reconnection(self):
        """Attempt to reconnect the WebSocket"""
        try:
            print("🔄 Attempting WebSocket reconnection...")
            self.reconnection_count += 1
            
            # Reset connection tracking
            self.connection_start_time = time.time()
            self.last_message_time = time.time()
            self.message_count = 0
            
            # Call reconnection callback if provided
            if self.reconnect_callback:
                success = self.reconnect_callback()
                if success:
                    print(f"✅ WebSocket reconnection successful (attempt #{self.reconnection_count})")
                else:
                    print(f"❌ WebSocket reconnection failed (attempt #{self.reconnection_count})")
            
        except Exception as e:
            print(f"❌ Reconnection attempt failed: {e}")
    
    def get_health_stats(self) -> dict:
        """Get current connection health statistics"""
        current_time = time.time()
        return {
            "message_count": self.message_count,
            "connection_age_seconds": current_time - self.connection_start_time,
            "silence_duration_seconds": current_time - self.last_message_time,
            "reconnection_count": self.reconnection_count,
            "is_healthy": (current_time - self.last_message_time) < self.max_silence_duration
        }


# Example usage for your existing layer2_dydx_callbacks.py:
"""
# In your DydxTradesStreamCallbacks.__init__():
self.health_monitor = WebSocketHealthMonitor(
    websocket_manager=self,
    reconnect_callback=self._handle_reconnection
)

# In your _handle_websocket_message():
self.health_monitor.on_message_received()

# Add reconnection method:
def _handle_reconnection(self) -> bool:
    try:
        self.disconnect()
        time.sleep(2)
        return self.connect()
    except Exception as e:
        print(f"Reconnection failed: {e}")
        return False

# Start monitoring after successful connection:
if self.connect():
    self.health_monitor.start_monitoring()
"""
