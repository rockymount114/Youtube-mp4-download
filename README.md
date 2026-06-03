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
