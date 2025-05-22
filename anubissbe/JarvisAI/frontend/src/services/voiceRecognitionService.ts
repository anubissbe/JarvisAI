class VoiceRecognitionService {
  private recognition: SpeechRecognition | null = null;
  private isListening: boolean = false;
  private onResultCallback: ((text: string) => void) | null = null;
  private onEndCallback: (() => void) | null = null;
  private continuous: boolean = false;

  constructor() {
    this.initRecognition();
  }

  private initRecognition(): void {
    if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {
      // Browser supports speech recognition
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      this.recognition = new SpeechRecognition();
      
      // Configure recognition
      this.recognition.lang = 'en-US';
      this.recognition.interimResults = false;
      this.recognition.maxAlternatives = 1;
      
      // Set up event handlers
      this.recognition.onresult = this.handleResult.bind(this);
      this.recognition.onend = this.handleEnd.bind(this);
      this.recognition.onerror = this.handleError.bind(this);
    } else {
      console.error('Speech recognition not supported in this browser');
    }
  }

  private handleResult(event: SpeechRecognitionEvent): void {
    const transcript = event.results[0][0].transcript;
    if (this.onResultCallback) {
      this.onResultCallback(transcript);
    }
  }

  private handleEnd(): void {
    this.isListening = false;
    
    if (this.continuous && this.recognition) {
      this.recognition.start();
      this.isListening = true;
    } else if (this.onEndCallback) {
      this.onEndCallback();
    }
  }

  private handleError(event: SpeechRecognitionErrorEvent): void {
    console.error('Speech recognition error:', event.error);
    this.isListening = false;
    
    if (this.onEndCallback) {
      this.onEndCallback();
    }
  }

  public start(continuous: boolean = false): boolean {
    if (!this.recognition) {
      console.error('Speech recognition not supported');
      return false;
    }
    
    if (this.isListening) {
      return true;
    }
    
    try {
      this.continuous = continuous;
      this.recognition.continuous = continuous;
      this.recognition.start();
      this.isListening = true;
      return true;
    } catch (error) {
      console.error('Error starting speech recognition:', error);
      return false;
    }
  }

  public stop(): void {
    if (this.recognition && this.isListening) {
      this.continuous = false;
      this.recognition.stop();
      this.isListening = false;
    }
  }

  public onResult(callback: (text: string) => void): void {
    this.onResultCallback = callback;
  }

  public onEnd(callback: () => void): void {
    this.onEndCallback = callback;
  }

  public isSupported(): boolean {
    return !!this.recognition;
  }

  public getListeningState(): boolean {
    return this.isListening;
  }
}

export default new VoiceRecognitionService();