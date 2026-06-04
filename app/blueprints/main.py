import os
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
        
        flash('Meeting added successfully. Processing will begin shortly.')
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
    # Reset transcription and analysis results if they exist?
    # For now, just setting status to Pending will trigger the worker
    db.session.commit()
    flash(f'Processing restarted for: {meeting.title}')
    return redirect(url_for('main.meeting_list'))

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
