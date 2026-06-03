# GEMINI.md

## Project Overview

Build a Flask-based Meeting Intelligence application that allows staff to upload meeting audio recordings, automatically generate transcripts using Faster-Whisper, and create AI-generated meeting summaries using a local Ollama server.

Target users:

* City staff
* Department directors
* City council members
* Administrative assistants

Primary use case:

* Upload City Council meeting recordings
* Generate transcripts
* Generate meeting minutes
* Extract action items
* Identify motions and votes
* Store results for future search

---

## Technology Stack

### Backend

* Flask
* SQLAlchemy
* MSSQL
* Flask-Login
* Faster-Whisper
* Ollama API

### Frontend

* Tailwind CSS
* Jinja2 Templates
* HTMX (optional)

### AI Services

#### Speech-to-Text

* Faster-Whisper
* Model: medium (default)
* Model: large-v3 (optional for GPU)

#### LLM

* Ollama
* Endpoint:
  http://172.20.21.20:11434

Preferred models:

* llama3.2
* qwen3
* gemma3

---

## Application Workflow

### Step 1 - Upload Audio

User uploads:

* mp3
* wav
* m4a

Store file in:

uploads/audio/

Create Meeting record in database.

Status:

Pending

---

### Step 2 - Transcription

Background task:

* Load Faster-Whisper
* Generate transcript
* Save transcript to database
* Save transcript text file

Status:

Transcribed

---

### Step 3 - AI Analysis

Send transcript to Ollama.

Generate:

#### Meeting Summary

Brief executive summary.

#### Action Items

List:

* Task
* Owner
* Due Date (if available)

#### Motions

Extract:

* Motion
* Moved By
* Seconded By
* Vote Result

#### Budget Discussion

Summarize:

* Budget changes
* Department requests
* Financial impacts

Status:

Analyzed

---

## Database Design

### meetings

| Field        |
| ------------ |
| id           |
| title        |
| meeting_date |
| audio_file   |
| transcript   |
| summary      |
| action_items |
| motions      |
| budget_notes |
| status       |
| created_at   |

---

## UI Requirements

### Dashboard

Display:

* Total Meetings
* Pending
* Transcribed
* Analyzed

Cards only.

Keep simple.

---

### Meeting List

Table:

* Title
* Date
* Status
* Actions

Actions:

* View
* Reprocess
* Delete

---

### Upload Page

Single card.

Fields:

* Meeting Title
* Meeting Date
* Audio File

Large upload button.

---

### Meeting Detail Page

Tabs:

1. Transcript
2. Summary
3. Action Items
4. Motions
5. Budget Notes

---

## Tailwind Design Guidelines

Use:

* Clean government-style layout
* White background
* Gray borders
* Blue accents

Container:

max-w-7xl mx-auto

Cards:

rounded-lg
shadow-sm
border
bg-white

Buttons:

bg-blue-600
hover:bg-blue-700
text-white

Avoid excessive animations.

Focus on readability.

---

## Ollama Prompt Standards

### Summary Prompt

Create professional meeting minutes from the transcript.

Include:

* Meeting overview
* Key discussion points
* Decisions made

---

### Action Item Prompt

Extract all action items.

Return JSON:

[
{
"task":"",
"owner":"",
"due_date":""
}
]

---

### Motion Prompt

Extract all motions and votes.

Return JSON:

[
{
"motion":"",
"moved_by":"",
"seconded_by":"",
"result":""
}
]

---

## Development Principles

* Keep architecture simple.
* Favor server-rendered pages.
* Avoid unnecessary JavaScript.
* Use Flask Blueprints.
* Use environment variables for configuration.
* All AI services run locally.
* No external APIs required.
* Optimize for maintainability and long meeting recordings.

---

## Future Enhancements

* Speaker identification
* Full-text transcript search
* PDF meeting packet upload
* Agenda matching
* Video upload support
* Email summaries
* Public meeting portal
* Department-specific reporting
