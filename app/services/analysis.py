import requests
import json
import os
from ..models import Meeting, db

OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://172.20.21.20:11434/api/generate')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2')

def analyze_meeting(meeting_id):
    meeting = Meeting.query.get(meeting_id)
    if not meeting or not meeting.transcript:
        return
    
    meeting.status = 'Analyzing'
    db.session.commit()
    
    try:
        # 1. Generate Summary
        summary_prompt = f"Create professional meeting minutes from the transcript.\n\nInclude:\n- Meeting overview\n- Key discussion points\n- Decisions made\n\nTranscript:\n{meeting.transcript}"
        meeting.summary = call_ollama(summary_prompt)
        
        # 2. Extract Action Items
        action_prompt = f"Extract all action items from the transcript.\n\nReturn ONLY JSON in this format: [{{'task':'', 'owner':'', 'due_date':''}}]\n\nTranscript:\n{meeting.transcript}"
        meeting.action_items = call_ollama_json(action_prompt)
        
        # 3. Extract Motions
        motion_prompt = f"Extract all motions and votes from the transcript.\n\nReturn ONLY JSON in this format: [{{'motion':'', 'moved_by':'', 'seconded_by':'', 'result':''}}]\n\nTranscript:\n{meeting.transcript}"
        meeting.motions = call_ollama_json(motion_prompt)
        
        # 4. Budget Discussion
        budget_prompt = f"Summarize any budget discussions, department requests, or financial impacts mentioned in the transcript.\n\nTranscript:\n{meeting.transcript}"
        meeting.budget_notes = call_ollama(budget_prompt)
        
        meeting.status = 'Analyzed'
        db.session.commit()
        return True
    except Exception as e:
        print(f"Analysis error: {e}")
        meeting.status = 'Error'
        db.session.commit()
        return False

def call_ollama(prompt):
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        return response.json().get('response', '')
    except Exception as e:
        print(f"Ollama error: {e}")
        return f"Error calling Ollama: {e}"

def call_ollama_json(prompt):
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        content = response.json().get('response', '[]')
        return json.loads(content)
    except Exception as e:
        print(f"Ollama JSON error: {e}")
        return []
