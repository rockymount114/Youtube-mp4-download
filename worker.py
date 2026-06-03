import time
from app import create_app, db
from app.models import Meeting
from app.services.transcription import transcribe_meeting
from app.services.analysis import analyze_meeting

app = create_app()

def worker():
    print("Worker started. Monitoring for new meetings...")
    with app.app_context():
        while True:
            # 1. Look for Pending meetings (Transcription)
            pending_meeting = Meeting.query.filter_by(status='Pending').first()
            if pending_meeting:
                print(f"Starting transcription for: {pending_meeting.title}")
                transcribe_meeting(pending_meeting.id)
                continue
            
            # 2. Look for Transcribed meetings (Analysis)
            transcribed_meeting = Meeting.query.filter_by(status='Transcribed').first()
            if transcribed_meeting:
                print(f"Starting analysis for: {transcribed_meeting.title}")
                analyze_meeting(transcribed_meeting.id)
                continue
            
            # Sleep for a bit before checking again
            time.sleep(10)

if __name__ == '__main__':
    worker()
