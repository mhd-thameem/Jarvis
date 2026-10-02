import os
import winsound
import pyaudio
import numpy as np
from pathlib import Path
import openwakeword
from openwakeword.model import Model
from faster_whisper import WhisperModel

from Core.brain import consult_jarvis
from Core.tts import text_to_speech

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1280

print("[+] Initializing Wake Word Engine...")
oww_model = Model(wakeword_models=["hey_jarvis"], inference_framework="onnx")
wake_key = list(oww_model.models.keys())[0]

print("[+] Initializing Whisper STT Engine...")
stt_model = WhisperModel("base.en", device="cpu", compute_type="int8")

p = pyaudio.PyAudio()

def play_audio(filepath: str):
    clean_path = str(Path(filepath).resolve()).replace("/", "\\")
    os.system(f'powershell -c (New-Object Media.SoundPlayer "{clean_path}").PlaySync()')

def record_user_speech(stream, record_seconds: int = 5) -> str:
    print("[*] Listening to your query...")
    frames = []
    for _ in range(0, int(RATE / CHUNK * record_seconds)):
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)

    # Convert raw audio bytes into normalized float32 format
    audio_int16 = np.frombuffer(b"".join(frames), dtype=np.int16)
    audio_float32 = audio_int16.astype(np.float32) / 32768.0

    # VAD filtering cuts background noise and prevents phrase repetition loops
    segments, _ = stt_model.transcribe(
        audio_float32,
        beam_size=1,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=400),
        condition_on_previous_text=False
    )
    
    transcript = " ".join([seg.text for seg in segments]).strip()
    return transcript

def main():
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK
    )

    print("\n[READY] Jarvis is actively listening for 'Hey Jarvis' on your laptop mic...")

    try:
        while True:
            audio_data = stream.read(CHUNK, exception_on_overflow=False)
            audio_array = np.frombuffer(audio_data, dtype=np.int16)

            prediction = oww_model.predict(audio_array)
            score = prediction.get(wake_key, 0.0)

            if score >= 0.15:
                print(f"\n[!] Wake word triggered! (Confidence: {score:.3f})")
                oww_model.reset()

                # Audio cue so you know exactly when to speak
                winsound.Beep(1200, 150)

                query = record_user_speech(stream, record_seconds=5)
                if not query:
                    print("[-] No speech detected.")
                    continue

                print(f"[>] You said: {query}")
                reply = consult_jarvis(query, category="laptop_mic")
                print(f"[<] Jarvis: {reply}")

                out_audio = text_to_speech(reply, filename="laptop_reply.wav")
                play_audio(out_audio)

                print("\n[READY] Listening for 'Hey Jarvis'...")

    except KeyboardInterrupt:
        print("\nExiting voice loop...")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

if __name__ == "__main__":
    main()