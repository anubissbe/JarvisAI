interface SpeechOptions {
  voice?: string;
  rate?: number;
  pitch?: number;
  volume?: number;
}

class SpeechService {
  private synth: SpeechSynthesis;
  private voices: SpeechSynthesisVoice[] = [];
  private speaking: boolean = false;

  constructor() {
    this.synth = window.speechSynthesis;
    this.loadVoices();
    
    // Chrome loads voices asynchronously
    if (window.speechSynthesis.onvoiceschanged !== undefined) {
      window.speechSynthesis.onvoiceschanged = this.loadVoices.bind(this);
    }
  }

  private loadVoices(): void {
    this.voices = this.synth.getVoices();
  }

  public getVoices(): SpeechSynthesisVoice[] {
    return this.voices;
  }

  public speak(text: string, options: SpeechOptions = {}): void {
    if (!text) return;
    
    // Cancel any ongoing speech
    this.stop();
    
    const utterance = new SpeechSynthesisUtterance(text);
    
    // Set voice
    if (options.voice) {
      const selectedVoice = this.voices.find(voice => voice.name === options.voice);
      if (selectedVoice) {
        utterance.voice = selectedVoice;
      }
    }
    
    // Set other options
    if (options.rate !== undefined) utterance.rate = options.rate;
    if (options.pitch !== undefined) utterance.pitch = options.pitch;
    if (options.volume !== undefined) utterance.volume = options.volume;
    
    // Set event handlers
    utterance.onstart = () => {
      this.speaking = true;
    };
    
    utterance.onend = () => {
      this.speaking = false;
    };
    
    utterance.onerror = (event) => {
      console.error('Speech synthesis error:', event);
      this.speaking = false;
    };
    
    // Speak
    this.synth.speak(utterance);
  }

  public stop(): void {
    if (this.synth.speaking) {
      this.synth.cancel();
      this.speaking = false;
    }
  }

  public isSpeaking(): boolean {
    return this.speaking;
  }
}

export default new SpeechService();