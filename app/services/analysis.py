import requests
import json
import os
from ..models import Meeting, db

OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://172.20.21.20:11434/api/generate')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2')

def analyze_meeting(meeting_id):
    meeting = Meeting.query.get(meeting_id)
    if not meeting or not meeting.transcript:
        print(f"Analysis skipped for ID {meeting_id}: No meeting or transcript.")
        return
    
    meeting.status = 'Analyzing'
    meeting.progress = 75
    db.session.commit()
    
    try:
        print(f"Analyzing meeting: {meeting.title}")
        
        # 1. Generate Summary
        summary_prompt = (
            f"Create professional meeting minutes from the following transcript of a City Council meeting.\n\n"
            f"Include:\n- Meeting overview\n- Key discussion points\n- Decisions made\n\n"
            f"Transcript:\n{meeting.transcript}"
        )
        meeting.summary = call_ollama(summary_prompt)
        meeting.progress = 82
        db.session.commit()
        
        # 2. Extract Action Items
        action_prompt = (
            f"Extract all action items from the following transcript.\n\n"
            f"Return ONLY valid JSON in this format: [{{'task':'', 'owner':'', 'due_date':''}}]\n"
            f"Use empty strings if info is missing.\n\n"
            f"Transcript:\n{meeting.transcript}"
        )
        meeting.action_items = call_ollama_json(action_prompt)
        meeting.progress = 89
        db.session.commit()
        
        # 3. Extract Motions
        motion_prompt = (
            f"You are a legal clerk. Extract all formal motions and votes from the following City Council transcript.\n\n"
            f"Return ONLY a JSON list of objects. Each object MUST have these keys: 'motion', 'moved_by', 'seconded_by', 'result'.\n"
            f"Example format: [{{'motion':'To approve the minutes', 'moved_by':'Councilman Smith', 'seconded_by':'Councilwoman Jones', 'result':'Passed 5-0'}}]\n\n"
            f"If NO motions are found, return an empty list [].\n"
            f"Do not include any other text or explanation.\n\n"
            f"Transcript:\n{meeting.transcript}"
        )
        motions_data = call_ollama_json(motion_prompt)
        # Ensure it's a list
        if isinstance(motions_data, dict):
            # If AI returned a single object instead of a list
            if 'motion' in motions_data:
                motions_data = [motions_data]
            else:
                motions_data = []
        elif not isinstance(motions_data, list):
            motions_data = []
            
        meeting.motions = motions_data
        meeting.progress = 96
        db.session.commit()
        
        # 4. Budget Discussion
        budget_prompt = (
            f"Summarize any budget discussions, department requests, or financial impacts mentioned in the following transcript.\n"
            f"Be specific about dollar amounts or department names if mentioned.\n\n"
            f"Transcript:\n{meeting.transcript}"
        )
        meeting.budget_notes = call_ollama(budget_prompt)
        
        meeting.status = 'Analyzed'
        meeting.progress = 100
        db.session.commit()
        print(f"Analysis complete for: {meeting.title}")
        return True
    except Exception as e:
        print(f"Analysis error for {meeting.title}: {e}")
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
        print(f"Calling Ollama for text completion...")
        response = requests.post(OLLAMA_URL, json=payload, timeout=300) # Increased timeout
        result = response.json().get('response', '')
        if not result:
            print("Warning: Ollama returned empty response.")
        return result
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
        print(f"Calling Ollama for JSON extraction...")
        response = requests.post(OLLAMA_URL, json=payload, timeout=300) # Increased timeout
        content = response.json().get('response', '[]')
        
        # Robust JSON cleaning
        content = content.strip()
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0].strip()
        elif '```' in content:
            content = content.split('```')[1].split('```')[0].strip()
            
        return json.loads(content)
    except Exception as e:
        print(f"Ollama JSON error: {e}")
        # Try one more time without the 'format: json' if it failed? No, let's just return empty.
        return []
