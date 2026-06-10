import sys
from pathlib import Path

try:
    from faster_whisper import WhisperModel
except ImportError as e:
    print("ERROR: 'faster-whisper' is not installed.")
    print("Run:  pip install faster-whisper")
    sys.exit(1)

audio_file = "./Rocky Mount City Council Budget Meeting 6.3.2026 10 AM.mp3"

if not Path(audio_file).exists():
    print(f"ERROR: Audio file not found: {audio_file}")
    sys.exit(1)

print("Loading model...")

# for long audio files, consider using a larger model (e.g. "medium" or "large") for better accuracy, but it will require more memory and processing time.
model = WhisperModel("base", 
                     device="cpu", 
                     compute_type="int8")

print(f"Transcribing {audio_file}...")
# Force language='en' to avoid misdetection as Welsh
segments, info = model.transcribe(audio_file, beam_size=5, language='en')

print(f"Detected language: {info.language} (probability: {info.language_probability:.2f})")

transcript = " ".join([segment.text for segment in segments])

with open("transcript.txt", "w", encoding="utf-8") as f:
    f.write(transcript)

print("Done. Transcript saved to transcript.txt")
print(f"Length: {len(transcript)} characters")
