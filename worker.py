import time
import os
from app import create_app, db
from app.models import Meeting
from app.services.transcription import transcribe_meeting
from app.services.analysis import analyze_meeting

app = create_app()

def worker():
    print("Worker started. Checking for meetings to process...")
    
    with app.app_context():
        # Simple processing loop - process until nothing is left
        while True:
            # 1. Look for Pending meetings (Transcription)
            pending_meeting = Meeting.query.filter_by(status='Pending').first()
            if pending_meeting:
                print(f"Starting transcription for: {pending_meeting.title}")
                try:
                    transcribe_meeting(pending_meeting.id)
                except Exception as e:
                    print(f"Error transcribing {pending_meeting.title}: {e}")
                continue
            
            # 2. Look for Transcribed meetings (Analysis)
            transcribed_meeting = Meeting.query.filter_by(status='Transcribed').first()
            if transcribed_meeting:
                print(f"Starting analysis for: {transcribed_meeting.title}")
                try:
                    analyze_meeting(transcribed_meeting.id)
                except Exception as e:
                    print(f"Error analyzing {transcribed_meeting.title}: {e}")
                continue
            
            # No more work found
            break
            
    print("Worker finished. All pending tasks complete.")

if __name__ == '__main__':
    worker()
