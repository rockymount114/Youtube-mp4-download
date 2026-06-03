import os
from faster_whisper import WhisperModel
from ..models import Meeting, db
from flask import current_app

def transcribe_meeting(meeting_id):
    # This should be called within an app context
    meeting = Meeting.query.get(meeting_id)
    if not meeting:
        return
    
    meeting.status = 'Transcribing'
    db.session.commit()
    
    try:
        audio_path = os.path.join(current_app.config['UPLOAD_FOLDER'], meeting.audio_file)
        
        # Load model (as per scribetext.py example)
        model = WhisperModel("medium", device="cpu", compute_type="int8")
        
        segments, info = model.transcribe(audio_path, beam_size=5)
        transcript = " ".join([segment.text for segment in segments])
        
        meeting.transcript = transcript
        meeting.status = 'Transcribed'
        db.session.commit()
        
        # Save transcript to text file as well
        transcript_filename = f"{meeting.audio_file}.txt"
        transcript_path = os.path.join(current_app.config['UPLOAD_FOLDER'], transcript_filename)
        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write(transcript)
            
        return True
    except Exception as e:
        print(f"Transcription error: {e}")
        meeting.status = 'Error'
        db.session.commit()
        return False
