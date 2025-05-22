#!/usr/bin/env python3
"""
Test script for Speech Service
"""

import os
import sys
import unittest
import json
import tempfile
import shutil
import wave
import numpy as np
import requests
import time
from io import BytesIO
from unittest.mock import patch, MagicMock

# Add parent directory to path to import module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Try to import the speech service module
try:
    from speech_service.speech_service import (
        transcribe_audio, text_to_speech, AudioBuffer, app
    )
    SPEECH_MODULE_AVAILABLE = True
except ImportError:
    SPEECH_MODULE_AVAILABLE = False
    print("Warning: Cannot import speech_service module. Some tests will be skipped.")


class TestSpeechService(unittest.TestCase):
    """Tests for the Speech Service"""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures before running tests"""
        # Create temporary directory for test audio files
        cls.temp_dir = tempfile.mkdtemp()
        
        # Check if the speech service is running
        cls.service_url = os.environ.get('SPEECH_SERVICE_URL', 'http://localhost:5000')
        try:
            response = requests.get(f"{cls.service_url}/health", timeout=2)
            cls.service_available = response.status_code == 200
        except:
            cls.service_available = False
            print("Warning: Speech service not available at {cls.service_url}. Integration tests will be skipped.")

    @classmethod
    def tearDownClass(cls):
        """Clean up after tests"""
        # Remove temporary directory
        shutil.rmtree(cls.temp_dir)

    def test_audio_buffer(self):
        """Test the AudioBuffer class"""
        if not SPEECH_MODULE_AVAILABLE:
            self.skipTest("Speech service module not available")
        
        # Create an audio buffer
        buffer = AudioBuffer(max_length_seconds=1, sample_rate=16000, channels=1)
        
        # Test adding silent audio
        silent_audio = np.zeros(1600, dtype=np.float32)  # 100ms of silence
        is_active = buffer.add_audio(silent_audio)
        self.assertFalse(is_active)  # Should not detect activity
        
        # Test adding active audio
        active_audio = np.random.normal(0, 0.5, 1600).astype(np.float32)  # Noisy audio
        is_active = buffer.add_audio(active_audio)
        
        # Not necessarily active after just one frame, depending on threshold
        # But the buffer should have the audio
        audio_data = buffer.get_audio()
        self.assertEqual(len(audio_data), 3200)  # 1600 + 1600
        
        # Test buffer wrapping (overflow)
        for _ in range(20):  # Add more data than the buffer can hold
            buffer.add_audio(active_audio)
        
        # Buffer should be full now
        self.assertTrue(buffer.is_full)
        
        # Get the full buffer
        audio_data = buffer.get_audio()
        self.assertEqual(len(audio_data), 16000)  # 1 second at 16kHz
        
        # Test clearing the buffer
        buffer.clear()
        self.assertFalse(buffer.is_full)
        audio_data = buffer.get_audio()
        self.assertEqual(len(audio_data), 0)

    @unittest.skipIf(not SPEECH_MODULE_AVAILABLE, "Speech service module not available")
    @patch('speech_service.speech_service.whisper_model')
    def test_transcribe_audio(self, mock_whisper_model):
        """Test the transcribe_audio function"""
        # Mock whisper model transcribe method
        mock_segment = MagicMock()
        mock_segment.text = "This is a test transcript."
        mock_segments = [mock_segment]
        mock_info = MagicMock()
        
        # Set up the mock to return our fake segments
        mock_whisper_model.transcribe.return_value = (mock_segments, mock_info)
        
        # Create some test audio data
        audio_data = np.random.normal(0, 0.1, 16000).astype(np.float32)  # 1 second at 16kHz
        
        # Call the function
        transcript = transcribe_audio(audio_data)
        
        # Check results
        self.assertEqual(transcript, "This is a test transcript.")
        
        # Check that the model was called
        mock_whisper_model.transcribe.assert_called_once()
        
        # Test error handling
        mock_whisper_model.transcribe.side_effect = Exception("Transcription error")
        transcript = transcribe_audio(audio_data)
        self.assertEqual(transcript, "")

    @unittest.skipIf(not SPEECH_MODULE_AVAILABLE, "Speech service module not available")
    @patch('speech_service.speech_service.tts_engine')
    @patch('speech_service.speech_service.TTS_ENGINE', 'pyttsx3')
    def test_text_to_speech_pyttsx3(self, mock_tts_engine):
        """Test the text_to_speech function with pyttsx3"""
        # Set up the mock
        mock_tts_engine.save_to_file = MagicMock()
        mock_tts_engine.runAndWait = MagicMock()
        
        # Patch librosa.load to return fake audio data
        with patch('speech_service.speech_service.librosa.load') as mock_load:
            mock_load.return_value = (np.zeros(16000, dtype=np.float32), 16000)
            
            # Patch soundfile.write to do nothing
            with patch('speech_service.speech_service.sf.write') as mock_write:
                # Call the function
                output_path = text_to_speech("Test text")
                
                # Check results
                self.assertIsNotNone(output_path)
                self.assertTrue(os.path.dirname(output_path).endswith('audio'))
                
                # Check that the engine was called
                mock_tts_engine.save_to_file.assert_called_once()
                mock_tts_engine.runAndWait.assert_called_once()

    @unittest.skipIf(not hasattr(TestSpeechService, 'service_available') or 
                    not TestSpeechService.service_available, 
                    "Speech service not available")
    def test_health_endpoint(self):
        """Test the health check endpoint"""
        response = requests.get(f"{self.service_url}/health")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'healthy')
        
        # Check service details
        self.assertIn('whisper_model', data)
        self.assertIn('tts_engine', data)

    @unittest.skipIf(not hasattr(TestSpeechService, 'service_available') or 
                    not TestSpeechService.service_available, 
                    "Speech service not available")
    def test_languages_endpoint(self):
        """Test the languages endpoint"""
        response = requests.get(f"{self.service_url}/api/languages")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('languages', data)
        self.assertIsInstance(data['languages'], list)
        self.assertGreater(len(data['languages']), 0)
        
        # Check language format
        first_lang = data['languages'][0]
        self.assertIn('code', first_lang)
        self.assertIn('name', first_lang)

    @unittest.skipIf(not hasattr(TestSpeechService, 'service_available') or 
                    not TestSpeechService.service_available, 
                    "Speech service not available")
    def test_tts_endpoint_integration(self):
        """Test the text-to-speech endpoint"""
        # Prepare the request
        payload = {
            "text": "This is a test of the text to speech service."
        }
        
        # Make the request
        response = requests.post(
            f"{self.service_url}/api/tts",
            json=payload
        )
        
        # Check status code
        self.assertEqual(response.status_code, 200)
        
        # Check that we got audio data
        self.assertEqual(response.headers['Content-Type'], 'audio/wav')
        
        # Check that the audio file is valid
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(response.content)
            temp_path = temp_file.name
        
        # Verify it's a valid WAV file
        try:
            with wave.open(temp_path, 'rb') as wf:
                self.assertGreater(wf.getnframes(), 0)
        finally:
            os.unlink(temp_path)

    def test_create_test_audio_file(self):
        """Create a test audio file for STT testing"""
        try:
            import soundfile as sf
            
            # Create a simple sine wave
            duration_sec = 3
            sample_rate = 16000
            t = np.linspace(0, duration_sec, duration_sec * sample_rate)
            frequency = 440  # A4 note
            audio = 0.5 * np.sin(2 * np.pi * frequency * t)
            
            # Save to a WAV file
            file_path = os.path.join(self.temp_dir, 'test_audio.wav')
            sf.write(file_path, audio, sample_rate)
            
            print(f"\nCreated test audio file at: {file_path}")
            print("You can use this file to test the STT functionality manually.")
            
            # Verify the file exists
            self.assertTrue(os.path.exists(file_path))
            self.assertGreater(os.path.getsize(file_path), 0)
            
        except ImportError:
            self.skipTest("soundfile not available, skipping audio file creation")


def create_sine_wave(frequency, duration_sec, sample_rate=16000, amplitude=0.5):
    """Create a sine wave audio sample"""
    t = np.linspace(0, duration_sec, int(duration_sec * sample_rate))
    return amplitude * np.sin(2 * np.pi * frequency * t)


if __name__ == '__main__':
    # Run unit tests
    unittest.main()