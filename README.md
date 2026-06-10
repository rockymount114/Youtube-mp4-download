# Meeting Intelligence Application

A Flask-based application for transcribing and analyzing meeting recordings using Faster-Whisper and Ollama.

## Setup Instructions

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Environment Variables:**
    Copy `.env.example` to `.env` and fill in your credentials.
    ```bash
    cp .env.example .env
    ```

3.  **Database Setup:**
    Ensure you have an MSSQL server running and the `DATABASE_URL` in `.env` is correct. The application will create the tables automatically on first run.

4.  **Run the Application:**
    Open two terminals:
    
    Terminal 1 (Web Server):
    ```bash
    python run.py
    ```
    
    Terminal 2 (Background Worker):
    ```bash
    python worker.py
    ```

5.  **Access the Dashboard:**
    Open `http://127.0.0.1:5000` in your browser.
    Default login: `admin / admin123`

## Project Structure

```text
Youtube-mp4-download/
├── app/                    # Flask Application
│   ├── blueprints/         # Routes and View Logic
│   │   ├── auth.py         # Authentication (Login/Logout)
│   │   ├── main.py         # Dashboard, Uploads, Meeting Details
│   │   └── users.py        # User Management (Add, Reset, Delete)
│   ├── services/           # Business Logic & AI Integrations
│   │   ├── analysis.py     # Ollama AI Analysis (Summary, Actions, Motions)
│   │   ├── transcription.py# Faster-Whisper Speech-to-Text
│   │   └── youtube.py      # Robust YouTube Audio Downloader
│   ├── static/             # CSS, JS, and Images
│   ├── templates/          # Jinja2 HTML Templates
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── login.html
│   │   ├── manage_users.html
│   │   ├── meeting_detail.html
│   │   ├── meeting_list.html
│   │   └── upload.html
│   ├── __init__.py         # App Factory
│   └── models.py           # SQLAlchemy Database Models
├── uploads/                # Storage for audio and transcripts
├── worker.py               # Background task processor
├── run.py                  # Web server entry point
├── main.py                 # Standalone YouTube download utility
├── requirements.txt        # Python dependencies
├── ffmpeg.exe              # Audio/Video processing utility
└── GEMINI.md               # Project development notes
```

## Features

- **Audio Upload:** Supports mp3, wav, and m4a.
- **Automated Transcription:** Uses `faster-whisper` (medium model by default).
- **AI Analysis:** Uses local Ollama server to generate:
  - Professional meeting minutes
  - Action items (Task, Owner, Due Date)
  - Motions and Votes
  - Budget Discussion summaries
- **Dashboard:** Overview of meeting processing status.

## Technology Stack

- **Backend:** Flask, SQLAlchemy, MSSQL
- **AI:** Faster-Whisper, Ollama
- **Frontend:** Tailwind CSS, Jinja2
