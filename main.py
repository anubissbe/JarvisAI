#!/usr/bin/env python3
"""
JarvisAI - Your Personal AI Assistant
This is the main entry point for running JarvisAI outside of Docker
"""

import os
import sys
import time
import logging
import argparse
import threading
import signal
import json
import tempfile
import subprocess
import queue
import re
import base64
import uuid
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

# Audio processing
try:
    import pyaudio
    import numpy as np
    import wave
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    print("Warning: Audio libraries not available. Install PyAudio for voice interaction.")

# Text and web capabilities
import requests
from requests.exceptions import RequestException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("jarvis.log")
    ]
)
logger = logging.getLogger('jarvis')

# Default configuration
DEFAULT_CONFIG = {
    "assistant_name": "Jarvis",
    "wake_word": "Hey Jarvis",
    "language": "en-US",
    "voice_id": "en-US-Standard-D",
    "volume": 1.0,
    "speech_rate": 1.0,
    "ollama_url": "http://localhost:11434",
    "model_name": "jarvis",
    "speech_service_url": "http://localhost:5000",
    "text_only": False,
    "debug": False
}


class JarvisAssistant:
    """JarvisAI Assistant - Core class that coordinates all functionality"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = config.get('assistant_name', 'Jarvis')
        self.wake_word = config.get('wake_word', 'Hey Jarvis').lower()
        self.text_only = config.get('text_only', False)
        self.ollama_url = config.get('ollama_url', 'http://localhost:11434')
        self.model_name = config.get('model_name', 'jarvis')
        self.speech_service_url = config.get('speech_service_url', 'http://localhost:5000')
        
        # Setup audio if available and not in text-only mode
        self.audio_device = None
        self.listening_thread = None
        self.audio_stream = None
        self.should_exit = threading.Event()
        self.audio_queue = queue.Queue()
        self.conversation_history = []
        
        # Add welcome message to history
        self.conversation_history.append({
            "role": "system",
            "content": f"You are {self.name}, an advanced AI assistant. Be helpful, concise, and friendly."
        })
        
        logger.info(f"{self.name} initialized with model: {self.model_name}")
        
        # Set up audio if not in text-only mode
        if not self.text_only and AUDIO_AVAILABLE:
            self._setup_audio()
    
    def _setup_audio(self):
        """Set up audio devices and streams"""
        try:
            self.audio_device = pyaudio.PyAudio()
            logger.info("Audio subsystem initialized")
        except Exception as e:
            logger.error(f"Failed to initialize audio: {e}")
            self.text_only = True
    
    def start(self):
        """Start the assistant"""
        logger.info(f"Starting {self.name}...")
        
        # Welcome message
        greeting = f"Hello, I am {self.name}, your personal AI assistant. How may I help you today?"
        print(f"\n{self.name}: {greeting}")
        
        if not self.text_only:
            self._speak(greeting)
            
            # Start the listening thread if audio is available
            if AUDIO_AVAILABLE:
                self.listening_thread = threading.Thread(target=self._listen_for_wake_word)
                self.listening_thread.daemon = True
                self.listening_thread.start()
                
                # Main loop for voice mode
                try:
                    while not self.should_exit.is_set():
                        time.sleep(0.1)
                except KeyboardInterrupt:
                    self.stop()
                    return
            else:
                logger.warning("Audio libraries not available. Falling back to text-only mode.")
                self.text_only = True
        
        # If in text-only mode, use command line input
        if self.text_only:
            self._text_mode_loop()
    
    def _listen_for_wake_word(self):
        """Listen for wake word in a separate thread"""
        # This is a simplified implementation - in a real system you'd use
        # a wake word detection library like Porcupine or Snowboy
        
        # Open audio stream
        try:
            chunk_size = 1024
            format = pyaudio.paInt16
            channels = 1
            rate = 16000
            
            self.audio_stream = self.audio_device.open(
                format=format,
                channels=channels,
                rate=rate,
                input=True,
                frames_per_buffer=chunk_size
            )
            
            logger.info("Listening for wake word...")
            print(f"\nSay '{self.wake_word}' to activate {self.name}...")
            
            # Simple state for wake word detection
            is_listening_for_command = False
            recording_frames = []
            silence_counter = 0
            
            while not self.should_exit.is_set():
                data = self.audio_stream.read(chunk_size, exception_on_overflow=False)
                audio_array = np.frombuffer(data, dtype=np.int16)
                
                # Simple voice activity detection
                energy = np.mean(np.abs(audio_array))
                
                if is_listening_for_command:
                    # Record command
                    recording_frames.append(data)
                    
                    # Detect end of command (silence)
                    if energy < 500:  # Threshold for silence
                        silence_counter += 1
                        if silence_counter > 20:  # ~1 second of silence
                            # Process the recorded command
                            self._process_voice_command(recording_frames, rate, channels, format)
                            
                            # Reset for next command
                            is_listening_for_command = False
                            recording_frames = []
                            silence_counter = 0
                            
                            # Prompt for next command
                            print(f"\nSay '{self.wake_word}' to activate {self.name}...")
                    else:
                        silence_counter = 0
                else:
                    # Simplified wake word detection (in a real system, use a proper wake word detector)
                    # Transcribe short audio segments and check for wake word
                    if energy > 1000:  # High energy might be speech
                        # Collect 2 seconds of audio for wake word detection
                        wake_word_frames = [data]
                        for _ in range(40):  # ~2 seconds at 1024 chunk size and 16kHz
                            if self.should_exit.is_set():
                                break
                            wake_word_frames.append(self.audio_stream.read(chunk_size, exception_on_overflow=False))
                        
                        # Check if wake word was said
                        if self._detect_wake_word(wake_word_frames, rate, channels, format):
                            is_listening_for_command = True
                            self._speak("I'm listening")
                            print(f"\n{self.name} is listening...")
        
        except Exception as e:
            logger.error(f"Error in audio listening thread: {e}")
            self.should_exit.set()
    
    def _detect_wake_word(self, audio_frames, rate, channels, format):
        """Detect wake word in audio frames"""
        # In a real implementation, use a proper wake word detection library
        # This is a simplified version using speech-to-text
        
        # Save audio frames to a temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = temp_file.name
        
        with wave.open(temp_path, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(self.audio_device.get_sample_size(format))
            wf.setframerate(rate)
            wf.writeframes(b''.join(audio_frames))
        
        # Send to speech service for transcription
        try:
            files = {'file': open(temp_path, 'rb')}
            response = requests.post(f"{self.speech_service_url}/api/stt", files=files)
            os.unlink(temp_path)  # Clean up temp file
            
            if response.status_code == 200:
                transcript = response.json().get('transcript', '').lower()
                logger.debug(f"Wake word detection transcript: {transcript}")
                
                # Check if wake word is in the transcript
                return self.wake_word.lower() in transcript
        except Exception as e:
            logger.error(f"Error in wake word detection: {e}")
            os.unlink(temp_path)  # Ensure cleanup
        
        return False
    
    def _process_voice_command(self, audio_frames, rate, channels, format):
        """Process a voice command from recorded audio frames"""
        # Save audio frames to a temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = temp_file.name
        
        with wave.open(temp_path, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(self.audio_device.get_sample_size(format))
            wf.setframerate(rate)
            wf.writeframes(b''.join(audio_frames))
        
        # Send to speech service for transcription
        try:
            files = {'file': open(temp_path, 'rb')}
            response = requests.post(f"{self.speech_service_url}/api/stt", files=files)
            os.unlink(temp_path)  # Clean up temp file
            
            if response.status_code == 200:
                transcript = response.json().get('transcript', '')
                if transcript:
                    logger.info(f"Transcribed command: {transcript}")
                    print(f"\nYou: {transcript}")
                    
                    # Process the command
                    self._process_command(transcript)
                else:
                    self._speak("I didn't catch that. Could you please repeat?")
            else:
                logger.error(f"Speech-to-text failed: {response.text}")
                self._speak("I'm having trouble understanding you right now.")
        
        except Exception as e:
            logger.error(f"Error processing voice command: {e}")
            os.unlink(temp_path)  # Ensure cleanup
            self._speak("I encountered an error processing your request.")
    
    def _text_mode_loop(self):
        """Run in text-only mode with command line input"""
        try:
            while not self.should_exit.is_set():
                user_input = input("\nYou: ")
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print(f"\n{self.name}: Goodbye! Have a great day.")
                    break
                
                if user_input.strip():
                    self._process_command(user_input)
        
        except KeyboardInterrupt:
            print(f"\n{self.name}: Goodbye! Have a great day.")
    
    def _process_command(self, command: str):
        """Process a user command/query"""
        # Add user message to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": command
        })
        
        # Send to Ollama for processing
        try:
            response = requests.post(
                f"{self.ollama_url}/api/chat",
                json={
                    "model": self.model_name,
                    "messages": self.conversation_history,
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                assistant_response = response.json().get('message', {}).get('content', '')
                
                if assistant_response:
                    # Add assistant response to conversation history
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": assistant_response
                    })
                    
                    # Keep conversation history to a reasonable size
                    if len(self.conversation_history) > 20:
                        # Keep the system message and last 9 exchanges
                        self.conversation_history = [self.conversation_history[0]] + self.conversation_history[-18:]
                    
                    # Output the response
                    print(f"\n{self.name}: {assistant_response}")
                    
                    # Speak the response if audio is enabled
                    if not self.text_only:
                        self._speak(assistant_response)
                else:
                    error_message = "I didn't receive a proper response from my language model."
                    print(f"\n{self.name}: {error_message}")
                    if not self.text_only:
                        self._speak(error_message)
            else:
                error_message = f"I'm having trouble connecting to my language model. Error code: {response.status_code}"
                print(f"\n{self.name}: {error_message}")
                if not self.text_only:
                    self._speak(error_message)
        
        except RequestException as e:
            error_message = "I'm having trouble connecting to my language model service."
            print(f"\n{self.name}: {error_message} ({str(e)})")
            if not self.text_only:
                self._speak(error_message)
    
    def _speak(self, text: str):
        """Convert text to speech and play it"""
        if not AUDIO_AVAILABLE:
            return
        
        try:
            # Send to speech service for TTS
            response = requests.post(
                f"{self.speech_service_url}/api/tts",
                json={"text": text, "voice": self.config.get("voice_id")}
            )
            
            if response.status_code == 200:
                # Save to temporary file
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                    temp_file.write(response.content)
                    temp_path = temp_file.name
                
                # Play the audio
                self._play_audio(temp_path)
                
                # Clean up
                os.unlink(temp_path)
            else:
                logger.error(f"Text-to-speech failed: {response.text}")
        
        except Exception as e:
            logger.error(f"Error in text-to-speech: {e}")
    
    def _play_audio(self, audio_file: str):
        """Play an audio file"""
        try:
            # Get audio file data
            wf = wave.open(audio_file, 'rb')
            
            # Create a stream
            stream = self.audio_device.open(
                format=self.audio_device.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True
            )
            
            # Read and play audio data
            chunk_size = 1024
            data = wf.readframes(chunk_size)
            
            while data:
                stream.write(data)
                data = wf.readframes(chunk_size)
            
            # Clean up
            stream.stop_stream()
            stream.close()
        
        except Exception as e:
            logger.error(f"Error playing audio: {e}")
    
    def stop(self):
        """Stop the assistant and clean up resources"""
        logger.info("Stopping assistant...")
        self.should_exit.set()
        
        # Close audio stream if active
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
        
        # Close audio device
        if self.audio_device:
            self.audio_device.terminate()
        
        # Wait for threads to finish
        if self.listening_thread and self.listening_thread.is_alive():
            self.listening_thread.join(timeout=2)
        
        logger.info("Assistant stopped")


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from file or use defaults"""
    config = DEFAULT_CONFIG.copy()
    
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                config.update(user_config)
            logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
    
    return config


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='JarvisAI - Your Personal AI Assistant')
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--text-only', action='store_true', help='Run in text-only mode')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Set up logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load configuration
    config = load_config(args.config)
    
    # Override with command line arguments
    if args.text_only:
        config['text_only'] = True
    if args.debug:
        config['debug'] = True
    
    # Create and start the assistant
    jarvis = JarvisAssistant(config)
    
    # Set up signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        print("\nShutting down Jarvis...")
        jarvis.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start the assistant
    try:
        jarvis.start()
    except KeyboardInterrupt:
        jarvis.stop()
    
    print("\nThank you for using JarvisAI. Goodbye!")


if __name__ == '__main__':
    main()