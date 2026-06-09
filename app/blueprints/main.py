import os
import subprocess
import sys
try:
    from yt_dlp import YoutubeDL
except ImportError:
    YoutubeDL = None

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required
from werkzeug.utils import secure_filename
from ..models import Meeting, db
from datetime import datetime

main = Blueprint('main', __name__)

def start_worker():
    try:
        # Get the path to worker.py in the root directory
        root_dir = os.path.abspath(os.path.join(current_app.root_path, '..'))
        worker_path = os.path.join(root_dir, 'worker.py')
        
        if os.path.exists(worker_path):
            # Start worker.py as a background process with the project root as CWD
            subprocess.Popen([sys.executable, worker_path], cwd=root_dir)
            return True
        else:
            print(f"Worker script not found at {worker_path}")
    except Exception as e:
        print(f"Failed to start worker: {e}")
    return False

@main.route('/')
@login_required
def dashboard():
    total_meetings = Meeting.query.count()
    pending = Meeting.query.filter_by(status='Pending').count()
    transcribed = Meeting.query.filter_by(status='Transcribed').count()
    analyzed = Meeting.query.filter_by(status='Analyzed').count()
    
    return render_template('dashboard.html', 
                           total_meetings=total_meetings, 
                           pending=pending, 
                           transcribed=transcribed, 
                           analyzed=analyzed)

@main.route('/start_worker_manual', methods=['POST'])
@login_required
def start_worker_manual():
    if start_worker():
        flash('Background worker started.')
    else:
        flash('Failed to start worker. Please check server logs.', 'error')
    return redirect(url_for('main.dashboard'))

@main.route('/meetings')
@login_required
def meeting_list():
    meetings = Meeting.query.order_by(Meeting.meeting_date.desc()).all()
    return render_template('meeting_list.html', meetings=meetings)

@main.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        title = request.form.get('title')
        meeting_date_str = request.form.get('meeting_date')
        youtube_url = request.form.get('youtube_url')
        audio_file = request.files.get('audio_file')
        
        if not title or not meeting_date_str:
            flash('Title and Date are required')
            return redirect(url_for('main.upload'))
            
        if not audio_file and not youtube_url:
            flash('Either an audio file or a YouTube URL is required')
            return redirect(url_for('main.upload'))
        
        meeting_date = datetime.strptime(meeting_date_str, '%Y-%m-%d').date()
        filename = None

        if youtube_url:
            if not YoutubeDL:
                flash('YouTube downloader (yt-dlp) is not installed. Please contact administrator.')
                return redirect(url_for('main.upload'))
                
            # Download YouTube audio
            try:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename_base = f"{timestamp}_youtube"
                output_template = os.path.join(current_app.config['UPLOAD_FOLDER'], f"{filename_base}.%(ext)s")
                
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                    'outtmpl': output_template,
                    'quiet': True,
                }
                
                with YoutubeDL(ydl_opts) as ydl:
                    ydl.download([youtube_url])
                
                filename = f"{filename_base}.mp3"
            except Exception as e:
                flash(f'Error downloading YouTube audio: {str(e)}')
                return redirect(url_for('main.upload'))
        else:
            filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{audio_file.filename}")
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            audio_file.save(file_path)
        
        new_meeting = Meeting(
            title=title,
            meeting_date=meeting_date,
            audio_file=filename,
            status='Pending'
        )
        db.session.add(new_meeting)
        db.session.commit()
        
        # Trigger worker
        start_worker()
        
        flash('Meeting added successfully. Processing has started.')
        return redirect(url_for('main.meeting_list'))
        
    return render_template('upload.html')

@main.route('/fetch_youtube_info', methods=['POST'])
@login_required
def fetch_youtube_info():
    url = request.json.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
        
    if not YoutubeDL:
        return jsonify({'error': 'yt-dlp not installed on server'}), 500

    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            upload_date = info.get('upload_date') # YYYYMMDD
            formatted_date = None
            if upload_date:
                formatted_date = datetime.strptime(upload_date, '%Y%m%d').strftime('%Y-%m-%d')
                
            return jsonify({
                'title': info.get('title'),
                'date': formatted_date
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main.route('/meeting/process/<int:id>', methods=['POST'])
@login_required
def process_meeting(id):
    meeting = Meeting.query.get_or_404(id)
    meeting.status = 'Pending'
    meeting.progress = 0
    db.session.commit()
    
    # Trigger worker
    if start_worker():
        flash(f'Processing started for: {meeting.title}')
    else:
        flash(f'Status reset to Pending for: {meeting.title}. Please ensure worker is running.')
        
    return redirect(url_for('main.meeting_list'))

@main.route('/meeting/status/<int:id>')
@login_required
def meeting_status(id):
    meeting = Meeting.query.get_or_404(id)
    return jsonify({
        'status': meeting.status,
        'progress': meeting.progress
    })

@main.route('/meeting/<int:id>')
@login_required
def meeting_detail(id):
    meeting = Meeting.query.get_or_404(id)
    return render_template('meeting_detail.html', meeting=meeting)

@main.route('/meeting/delete/<int:id>', methods=['POST'])
@login_required
def delete_meeting(id):
    meeting = Meeting.query.get_or_404(id)
    if meeting.audio_file:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], meeting.audio_file)
        if os.path.exists(file_path):
            os.remove(file_path)
            
    db.session.delete(meeting)
    db.session.commit()
    flash('Meeting deleted successfully')
    return redirect(url_for('main.meeting_list'))
