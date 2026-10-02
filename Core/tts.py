import wave
from pathlib import Path
from piper import PiperVoice

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "storage" / "models" / "voice.onnx"
CONFIG_PATH = BASE_DIR / "storage" / "models" / "voice.onnx.json"
OUTPUT_DIR = BASE_DIR / "storage" / "cache"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load the local ONNX voice model into memory
voice = PiperVoice.load(str(MODEL_PATH), config_path=str(CONFIG_PATH))

def text_to_speech(text: str, filename: str = "output.wav") -> str:
    """Synthesizes text into a valid WAV audio file with correct headers."""
    dest_path = OUTPUT_DIR / filename
    
    # Strip markdown symbols that confuse TTS speech
    clean_text = text.replace("*", "").replace("#", "").replace("`", "").strip()

    with wave.open(str(dest_path), "wb") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(voice.config.sample_rate)
        
        # In current piper-tts, synthesize() yields audio chunks
        for frame in voice.synthesize(clean_text):
            if hasattr(frame, "audio_int16_bytes"):
                wav_file.writeframes(frame.audio_int16_bytes)
            elif isinstance(frame, bytes):
                wav_file.writeframes(frame)

    return str(dest_path)