#!/usr/bin/env python3
"""
JarvisAI Speech Service
This service provides:
1. Speech-to-Text capabilities using local Whisper models
2. Text-to-Speech capabilities using various TTS engines
3. Wake word detection
4. Voice activity detection
"""

import os
import sys
import time
import uuid
import logging
import tempfile
import threading
import json
import wave
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from queue import Queue
from datetime import datetime

# Web server
from flask import Flask, request, jsonify, send_file

# Audio processing
import torch
import torchaudio
import pyaudio
import librosa
import soundfile as sf
from faster_whisper import WhisperModel

# TTS libraries
import pyttsx3
from TTS.api import TTS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("speech_service.log")
    ]
)
logger = logging.getLogger('speech_service')

# Configuration
AUDIO_DIR = os.environ.get('AUDIO_DIR', './audio')
HOST = os.environ.get('HOST', '0.0.0.0')
PORT = int(os.environ.get('PORT', '5000'))
WHISPER_MODEL = os.environ.get('WHISPER_MODEL', 'tiny')
USE_GPU = os.environ.get('USE_GPU', 'false').lower() == 'true'
TTS_ENGINE = os.environ.get('TTS_ENGINE', 'pyttsx3')  # Options: pyttsx3, coqui, espeak
TTS_VOICE = os.environ.get('TTS_VOICE', 'en-US-Standard-D')
SAMPLE_RATE = int(os.environ.get('SAMPLE_RATE', '16000'))
MAX_AUDIO_LENGTH_SECS = int(os.environ.get('MAX_AUDIO_LENGTH_SECS', '120'))
VOICE_ACTIVITY_THRESHOLD = float(os.environ.get('VOICE_ACTIVITY_THRESHOLD', '0.3'))

# Create directories
os.makedirs(AUDIO_DIR, exist_ok=True)

# Initialize Flask app
app = Flask(__name__)

# Initialize Whisper model
logger.info(f"Loading Whisper model: {WHISPER_MODEL}")
device = "cuda" if USE_GPU and torch.cuda.is_available() else "cpu"
compute_type = "float16" if device == "cuda" else "int8"

try:
    whisper_model = WhisperModel(
        WHISPER_MODEL, 
        device=device,
        compute_type=compute_type
    )
    logger.info(f"Whisper model loaded on {device}")
except Exception as e:
    logger.error(f"Failed to load Whisper model: {e}")
    whisper_model = None

# Initialize TTS engine
logger.info(f"Initializing TTS engine: {TTS_ENGINE}")
tts_engine = None

if TTS_ENGINE == 'pyttsx3':
    try:
        tts_engine = pyttsx3.init()
        voices = tts_engine.getProperty('voices')
        # Set voice to the first one available
        if voices:
            tts_engine.setProperty('voice', voices[0].id)
        tts_engine.setProperty('rate', 150)
        logger.info("pyttsx3 TTS engine initialized")
    except Exception as e:
        logger.error(f"Failed to initialize pyttsx3 TTS engine: {e}")

elif TTS_ENGINE == 'coqui':
    try:
        tts_engine = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")
        logger.info("Coqui TTS engine initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Coqui TTS engine: {e}")
        
        # Fallback to pyttsx3
        logger.info("Falling back to pyttsx3 TTS engine")
        try:
            tts_engine = pyttsx3.init()
            voices = tts_engine.getProperty('voices')
            if voices:
                tts_engine.setProperty('voice', voices[0].id)
            tts_engine.setProperty('rate', 150)
            TTS_ENGINE = 'pyttsx3'  # Update engine type to match the fallback
        except Exception as e2:
            logger.error(f"Failed to initialize fallback TTS engine: {e2}")


class AudioBuffer:
    """Ring buffer for audio with voice activity detection"""
    
    def __init__(
        self, 
        max_length_seconds: int = MAX_AUDIO_LENGTH_SECS,
        sample_rate: int = SAMPLE_RATE,
        channels: int = 1
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.max_length = max_length_seconds * sample_rate * channels
        self.buffer = np.zeros(self.max_length, dtype=np.float32)
        self.position = 0
        self.is_full = False
        self.lock = threading.Lock()
        self.active = False
        self.last_activity = 0
        self.vad_threshold = VOICE_ACTIVITY_THRESHOLD
        self.frame_ms = 30  # 30ms frames for VAD
        self.frame_size = int(sample_rate * self.frame_ms / 1000)
        self.activation_count = 0
        self.silence_count = 0
    
    def add_audio(self, audio_data: np.ndarray) -> bool:
        """Add audio data to the buffer and detect voice activity"""
        with self.lock:
            audio_len = len(audio_data)
            
            # Check for voice activity
            energy = np.mean(np.abs(audio_data))
            is_active = energy > self.vad_threshold
            
            if is_active:
                self.activation_count += 1
                self.silence_count = 0
                if self.activation_count >= 3:  # Need 3 consecutive active frames to start
                    self.active = True
                    self.last_activity = time.time()
            else:
                self.silence_count += 1
                self.activation_count = 0
                if self.silence_count >= 10:  # Need 10 consecutive silent frames to end
                    self.active = False
            
            # If buffer will overflow, wrap around
            if self.position + audio_len > self.max_length:
                # Fill to the end
                space_left = self.max_length - self.position
                self.buffer[self.position:] = audio_data[:space_left]
                
                # Wrap around
                self.position = audio_len - space_left
                self.buffer[:self.position] = audio_data[space_left:]
                self.is_full = True
            else:
                # Add directly
                self.buffer[self.position:self.position + audio_len] = audio_data
                self.position = (self.position + audio_len) % self.max_length
                if self.position == 0:
                    self.is_full = True
            
            return self.active
    
    def get_audio(self) -> np.ndarray:
        """Get the entire buffer as a continuous array"""
        with self.lock:
            if self.is_full:
                # Buffer is full, need to reconstruct the correct order
                return np.concatenate([
                    self.buffer[self.position:],
                    self.buffer[:self.position]
                ])
            else:
                # Buffer is not full, just return the used portion
                return self.buffer[:self.position]
    
    def clear(self):
        """Clear the buffer"""
        with self.lock:
            self.buffer = np.zeros(self.max_length, dtype=np.float32)
            self.position = 0
            self.is_full = False
            self.active = False
            self.activation_count = 0
            self.silence_count = 0


def transcribe_audio(audio_data: np.ndarray, sample_rate: int = SAMPLE_RATE) -> str:
    """Transcribe audio data using Whisper"""
    if whisper_model is None:
        logger.error("Whisper model not initialized")
        return ""
    
    try:
        # Save audio to a temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = temp_file.name
        
        sf.write(temp_path, audio_data, sample_rate)
        
        # Transcribe using Whisper
        segments, info = whisper_model.transcribe(temp_path, beam_size=5)
        
        # Collect all segments
        transcript = " ".join(segment.text for segment in segments)
        
        # Clean up
        os.unlink(temp_path)
        
        return transcript.strip()
    
    except Exception as e:
        logger.error(f"Error in transcription: {e}")
        return ""


def text_to_speech(text: str, output_path: Optional[str] = None) -> Optional[str]:
    """Convert text to speech using configured TTS engine"""
    if not text:
        return None
    
    try:
        # Generate a unique filename if not provided
        if output_path is None:
            os.makedirs(AUDIO_DIR, exist_ok=True)
            output_path = os.path.join(AUDIO_DIR, f"tts_{uuid.uuid4()}.wav")
        
        # Use the appropriate TTS engine
        if TTS_ENGINE == 'pyttsx3' and tts_engine:
            # Save to a temporary file first (pyttsx3 can be buggy with direct file output)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = temp_file.name
            
            tts_engine.save_to_file(text, temp_path)
            tts_engine.runAndWait()
            
            # Convert to standard format using librosa and soundfile
            audio, sr = librosa.load(temp_path, sr=SAMPLE_RATE, mono=True)
            sf.write(output_path, audio, SAMPLE_RATE)
            
            # Clean up temp file
            os.unlink(temp_path)
            
        elif TTS_ENGINE == 'coqui' and tts_engine:
            tts_engine.tts_to_file(text=text, file_path=output_path)
            
        else:
            logger.error("No TTS engine available")
            return None
        
        return output_path
    
    except Exception as e:
        logger.error(f"Error in text-to-speech: {e}")
        return None


# Flask routes
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    whisper_status = "loaded" if whisper_model is not None else "not loaded"
    tts_status = "loaded" if tts_engine is not None else "not loaded"
    
    return jsonify({
        "status": "healthy",
        "whisper_model": WHISPER_MODEL,
        "whisper_status": whisper_status,
        "tts_engine": TTS_ENGINE,
        "tts_status": tts_status,
        "device": device
    })


@app.route('/api/stt', methods=['POST'])
def speech_to_text():
    """Speech-to-text endpoint"""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    try:
        # Save the uploaded file
        file_path = os.path.join(AUDIO_DIR, f"upload_{uuid.uuid4()}.wav")
        file.save(file_path)
        
        # Load audio
        audio, sr = librosa.load(file_path, sr=SAMPLE_RATE, mono=True)
        
        # Transcribe
        transcript = transcribe_audio(audio, sr)
        
        # Clean up
        os.unlink(file_path)
        
        return jsonify({
            "transcript": transcript,
            "confidence": 0.9  # Mock confidence value
        })
    
    except Exception as e:
        logger.error(f"Error processing speech-to-text request: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/tts', methods=['POST'])
def text_to_speech_api():
    """Text-to-speech endpoint"""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.get_json()
    text = data.get('text')
    voice = data.get('voice', TTS_VOICE)
    
    if not text:
        return jsonify({"error": "No text provided"}), 400
    
    try:
        # Generate speech
        output_path = text_to_speech(text)
        
        if not output_path:
            return jsonify({"error": "Failed to generate speech"}), 500
        
        # Return audio file
        return send_file(
            output_path,
            mimetype="audio/wav",
            as_attachment=True,
            download_name=os.path.basename(output_path)
        )
    
    except Exception as e:
        logger.error(f"Error processing text-to-speech request: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/languages', methods=['GET'])
def get_languages():
    """Get available languages"""
    languages = [
        {"code": "en", "name": "English"},
        {"code": "fr", "name": "French"},
        {"code": "es", "name": "Spanish"},
        {"code": "de", "name": "German"},
        {"code": "it", "name": "Italian"},
        {"code": "pt", "name": "Portuguese"},
        {"code": "nl", "name": "Dutch"},
        {"code": "ja", "name": "Japanese"},
        {"code": "zh", "name": "Chinese"},
        {"code": "ru", "name": "Russian"}
    ]
    
    return jsonify({"languages": languages})


def create_requirements_file():
    """Create requirements.txt file if it doesn't exist"""
    requirements_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
    
    if not os.path.exists(requirements_path):
        with open(requirements_path, "w") as f:
            f.write("\n".join([
                "flask==2.3.3",
                "torch==2.0.1",
                "torchaudio==2.0.2",
                "pyaudio==0.2.13",
                "librosa==0.10.1",
                "soundfile==0.12.1",
                "numpy==1.24.3",
                "pyttsx3==2.90",
                "faster-whisper==0.9.0",
                "TTS==0.18.1"
            ]))
        logger.info(f"Created requirements.txt at {requirements_path}")


if __name__ == '__main__':
    # Create requirements file if needed
    create_requirements_file()
    
    # Start the Flask app
    logger.info(f"Starting JarvisAI Speech Service on {HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=False)