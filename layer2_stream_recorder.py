"""
Layer 2 Stream Recorder - Real API Integration with Recording Capability
Following TDD methodology - implementing start_recording() function completely
"""
import subprocess
import time
import socket
import threading
from pathlib import Path


def find_free_port(start_port=8080):
    """Find a free port starting from start_port"""
    for port in range(start_port, start_port + 100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(('localhost', port))
                return port
        except OSError:
            continue
    raise RuntimeError("No free port found")


class RecordingContext:
    """Context object that manages recording state and mitmproxy process"""
    
    def __init__(self, proxy_port=None):
        self._is_recording = True
        self._proxy_port = proxy_port or find_free_port()
        self._proxy_process = None
        self._proxy_thread = None
    
    def is_recording(self):
        """Check if recording is currently active"""
        return self._is_recording
    
    def is_proxy_running(self):
        """Check if mitmproxy is running and listening on the specified port"""
        if self._proxy_process is None:
            return False
        
        # Check if process is still alive
        if self._proxy_process.poll() is not None:
            return False
        
        # Check if port is actually listening
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', self._proxy_port))
                return result == 0
        except Exception:
            return False
    
    def get_proxy_port(self):
        """Get the port number where the proxy is listening"""
        return self._proxy_port
    
    def stop(self):
        """Stop the recording and cleanup resources"""
        self._is_recording = False
        if self._proxy_process:
            self._proxy_process.terminate()
            try:
                self._proxy_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._proxy_process.kill()
                self._proxy_process.wait()
            self._proxy_process = None
    
    def _start_proxy(self):
        """Start mitmproxy in a separate process"""
        # Create recordings directory if it doesn't exist
        recordings_dir = Path("recordings")
        recordings_dir.mkdir(exist_ok=True)
        
        # Start mitmproxy with dump addon to save flows
        cmd = [
            "mitmdump",
            "--listen-port", str(self._proxy_port),
            "--save-stream-file", str(recordings_dir / "traffic.mitm"),
            "--set", "confdir=~/.mitmproxy"
        ]
        
        try:
            self._proxy_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait a moment for proxy to start
            time.sleep(2)
            
            # Verify it started successfully
            if self._proxy_process.poll() is not None:
                stdout, stderr = self._proxy_process.communicate()
                raise RuntimeError(f"Failed to start mitmproxy: {stderr}")
                
        except Exception as e:
            raise RuntimeError(f"Error starting mitmproxy: {e}")


def start_recording(proxy_port=None):
    """
    Start recording HTTP/WebSocket traffic for dYdX API calls
    Returns a RecordingContext object that manages the recording session
    """
    context = RecordingContext(proxy_port)
    context._start_proxy()
    return context


def start_replay(recording_file="recordings/traffic.mitm"):
    """
    Start replay mode using previously recorded traffic
    Returns a RecordingContext object that serves recorded responses
    """
    context = RecordingContext()
    
    # Start mitmproxy in replay mode using recorded data
    recordings_dir = Path("recordings")
    recordings_dir.mkdir(exist_ok=True)
    
    # Check if recording file exists
    recording_path = Path(recording_file)
    if not recording_path.exists():
        raise RuntimeError(f"Recording file not found: {recording_path}")
    
    # Start mitmproxy with replay addon to serve recorded responses
    cmd = [
        "mitmdump",
        "--listen-port", str(context._proxy_port),
        "--server-replay", str(recording_path),
        "--set", "confdir=~/.mitmproxy",
        "--set", "server_replay_use_headers=false",  # Ignore headers when matching
        "--set", "server_replay_kill_extra=false",   # Don't kill extra flows
        "--set", "server_replay_reuse=true",         # Keep responses for multiple requests
        "--set", "connection_strategy=lazy"          # Use lazy connection strategy
    ]
    
    try:
        context._proxy_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Combine stdout and stderr for better debugging
            text=True
        )
        
        # Wait longer for proxy to start
        time.sleep(3)
        
        # Check if process died immediately (error condition)
        poll_result = context._proxy_process.poll()
        if poll_result is not None:
            stdout, _ = context._proxy_process.communicate()
            # Check if it's an actual error or successful startup
            if "HTTP(S) proxy listening" not in stdout:
                raise RuntimeError(f"Failed to start replay proxy: {stdout}")
            # If "listening" message is present, proxy started successfully even if process exited
        
        # Verify port is actually listening
        max_retries = 10
        for attempt in range(max_retries):
            if context.is_proxy_running():
                break
            time.sleep(0.5)
        else:
            # Get output for debugging
            try:
                stdout, _ = context._proxy_process.communicate(timeout=1)
            except subprocess.TimeoutExpired:
                context._proxy_process.terminate()
                stdout, _ = context._proxy_process.communicate()
            raise RuntimeError(f"Replay proxy not responding after {max_retries/2} seconds. Output: {stdout}")
            
    except Exception as e:
        if context._proxy_process:
            context._proxy_process.terminate()
        raise RuntimeError(f"Error starting replay proxy: {e}")
    
    return context
