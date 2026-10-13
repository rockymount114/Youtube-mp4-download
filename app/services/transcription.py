import os
from faster_whisper import WhisperModel
from ..models import Meeting, db
from flask import current_app

def format_timestamp(seconds: float) -> str:
    """Format seconds into HH:MM:SS,mmm"""
    total_seconds = max(0.0, float(seconds))
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    secs = int(total_seconds % 60)
    millis = int(round((total_seconds - int(total_seconds)) * 1000))
    if millis >= 1000:
        secs += 1
        millis = 0
        if secs >= 60:
            minutes += 1
            secs = 0
            if minutes >= 60:
                hours += 1
                minutes = 0
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def transcribe_meeting(meeting_id):
    # This should be called within an app context
    meeting = Meeting.query.get(meeting_id)
    if not meeting:
        return
    
    meeting.status = 'Transcribing'
    meeting.progress = 5
    db.session.commit()
    
    try:
        audio_path = os.path.join(current_app.config['UPLOAD_FOLDER'], meeting.audio_file)
        
        # Load model (as per scribetext.py example)
        model = WhisperModel("medium", device="cpu", compute_type="int8")
        
        # Force English language to avoid misdetection (e.g., Welsh)
        segments, info = model.transcribe(audio_path, beam_size=5, language="en")
        
        duration = info.duration
        transcript_parts = []
        
        for segment in segments:
            text = segment.text.strip()
            if text:
                time_range = f"{format_timestamp(segment.start)} --> {format_timestamp(segment.end)}"
                transcript_parts.append(f"{time_range} {text}")

            # Update progress (0-70% for transcription)
            if duration > 0:
                current_progress = int((segment.end / duration) * 65) + 5
                if current_progress > meeting.progress:
                    meeting.progress = min(current_progress, 70)
                    db.session.commit()
        
        transcript = "\n\n".join(transcript_parts)
        
        meeting.transcript = transcript
        meeting.status = 'Transcribed'
        meeting.progress = 70
        db.session.commit()
        
        # Save transcript to markdown file
        base_name = os.path.splitext(meeting.audio_file)[0]
        transcript_filename = f"{base_name}.md"
        transcript_path = os.path.join(current_app.config['UPLOAD_FOLDER'], transcript_filename)
        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write(transcript)
            
        return True
    except Exception as e:
        print(f"Transcription error: {e}")
        meeting.status = 'Error'
        db.session.commit()
        return False
