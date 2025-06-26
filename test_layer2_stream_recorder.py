"""
Layer 2 Stream Recording Tests
Following STRICT TDD methodology - testing real API integration with recording capability
"""
import pytest
import requests
import time
from layer2_stream_recorder import start_recording


class TestStreamRecorder:
    """Test Layer 2 stream recording functionality with mitmproxy"""
    
    def test_start_recording_returns_recording_context(self):
        """Test that start_recording() returns a valid recording context"""
        # Arrange: No setup needed for this basic test
        
        # Act: Call the function that doesn't exist yet
        recording_context = start_recording()
        
        # Assert: Should return a context that indicates recording started
        assert recording_context is not None
        assert hasattr(recording_context, 'is_recording')
        assert recording_context.is_recording() is True
    
    def test_start_recording_actually_starts_proxy(self):
        """Test that start_recording() actually starts mitmproxy for capturing traffic"""
        # Arrange: No existing recording
        
        # Act: Start recording
        recording_context = start_recording()
        
        # Assert: Proxy should be running and ready to capture
        assert recording_context.is_proxy_running() is True
        assert recording_context.get_proxy_port() > 0
        
        # Cleanup: Stop recording to avoid conflicts
        recording_context.stop()
    
    def test_start_recording_creates_recording_file(self):
        """Test that start_recording() creates the recording file infrastructure"""
        # Arrange: Start recording
        recording_context = start_recording()
        
        try:
            # Assert: Recording should be active and proxy running
            assert recording_context.is_recording() is True
            assert recording_context.is_proxy_running() is True
            
            # Assert: Recording file infrastructure should exist
            import os
            assert os.path.exists("recordings"), "recordings directory should be created"
            
        finally:
            # Cleanup: Always stop recording
            recording_context.stop()
    
    def test_stop_recording_actually_stops_proxy(self):
        """Test that stop_recording() actually stops the mitmproxy process"""
        # Arrange: Start recording first
        recording_context = start_recording()
        assert recording_context.is_proxy_running() is True
        
        # Act: Stop the recording
        recording_context.stop()
        
        # Assert: Proxy should no longer be running
        assert recording_context.is_proxy_running() is False
        assert recording_context.is_recording() is False
    
    def test_start_replay_validates_recording_file_exists(self):
        """Test that start_replay() checks for recording file existence"""
        # Arrange: Remove recording file if it exists
        import os
        from pathlib import Path
        
        recordings_dir = Path("recordings")
        recording_file = recordings_dir / "traffic.mitm"
        
        # Temporarily move recording file if it exists
        backup_path = None
        if recording_file.exists():
            backup_path = recordings_dir / "traffic.mitm.backup"
            recording_file.rename(backup_path)
        
        try:
            # Act & Assert: start_replay should raise error when no recording file
            from layer2_stream_recorder import start_replay
            
            try:
                replay_context = start_replay()
                # If we get here, test failed - should have raised error
                replay_context.stop()
                assert False, "Expected RuntimeError for missing recording file"
            except RuntimeError as e:
                assert "Recording file not found" in str(e)
                
        finally:
            # Restore backup if we had one
            if backup_path and backup_path.exists():
                backup_path.rename(recording_file)
    
    def test_replay_serves_recorded_content_deterministically(self):
        """Test that replay serves recorded content deterministically - CRUCIAL METHODOLOGY TEST"""
        # NETWORK-INDEPENDENT SOLUTION: Test with local mock server instead of external service
        
        # Arrange: Create a simple local HTTP server that serves different responses when live
        import threading
        import http.server
        import socketserver
        import json
        import uuid
        
        # Create a handler that serves different UUIDs each time (simulates live service)
        class MockHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/test-endpoint':
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    # Serve a DIFFERENT UUID each time (simulates live httpbin.org/uuid behavior)
                    response = {"id": str(uuid.uuid4()), "timestamp": time.time()}
                    self.wfile.write(json.dumps(response).encode())
                else:
                    self.send_response(404)
                    self.end_headers()
            
            def log_message(self, format, *args):
                pass  # Suppress log output
        
        # Start mock server on free port
        mock_server = socketserver.TCPServer(("", 0), MockHandler)  # Port 0 = auto-assign free port
        mock_port = mock_server.server_address[1]  # Get the actual assigned port
        mock_thread = threading.Thread(target=mock_server.serve_forever, daemon=True)
        mock_thread.start()
        
        try:
            # Step 1: Record requests to our mock server
            recording_context = start_recording()
            record_proxy_port = recording_context.get_proxy_port()
            
            record_proxies = {
                'http': f'http://localhost:{record_proxy_port}',
                'https': f'http://localhost:{record_proxy_port}'
            }
            
            # Make a request through recording proxy to our mock server
            record_url = f'http://localhost:{mock_port}/test-endpoint'
            original_response = requests.get(record_url, proxies=record_proxies, timeout=5)
            original_data = original_response.json()
            time.sleep(1)  # Let mitmproxy process the recording
            
            # Stop recording
            recording_context.stop()
            
            # Step 2: Test replay serves same recorded response consistently
            from layer2_stream_recorder import start_replay
            replay_context = start_replay()
            replay_port = replay_context.get_proxy_port()
            
            replay_proxies = {
                'http': f'http://localhost:{replay_port}',
                'https': f'http://localhost:{replay_port}'
            }
            
            # Make same request multiple times against replay proxy
            replay_response1 = requests.get(record_url, proxies=replay_proxies, timeout=5)
            replay_response2 = requests.get(record_url, proxies=replay_proxies, timeout=5)
            
            replay_data1 = replay_response1.json()
            replay_data2 = replay_response2.json()
            
            # Assert: Both replayed responses should have identical data from recording
            # This proves --set server_replay_reuse=true is working
            assert replay_data1['id'] == replay_data2['id'], f"Replayed IDs must be identical: {replay_data1['id']} vs {replay_data2['id']}"
            assert replay_data1['id'] == original_data['id'], f"Replayed ID must match recorded: {replay_data1['id']} vs {original_data['id']}"
            
            # CRITICAL: This proves deterministic replay is working - same data returned consistently
            print(f"✅ DETERMINISTIC REPLAY CONFIRMED: ID {replay_data1['id']} served consistently")
            
        finally:
            # Cleanup
            if 'replay_context' in locals():
                replay_context.stop()
            mock_server.shutdown()
