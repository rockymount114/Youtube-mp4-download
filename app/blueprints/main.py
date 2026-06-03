import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
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
        audio_file = request.files.get('audio_file')
        
        if not title or not meeting_date_str or not audio_file:
            flash('All fields are required')
            return redirect(url_for('main.upload'))
        
        meeting_date = datetime.strptime(meeting_date_str, '%Y-%m-%d').date()
        
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
        
        flash('Meeting uploaded successfully. Processing will begin shortly.')
        return redirect(url_for('main.meeting_list'))
        
    return render_template('upload.html')

@main.route('/meeting/<int:id>')
@login_required
def meeting_detail(id):
    meeting = Meeting.query.get_or_404(id)
    return render_template('meeting_detail.html', meeting=meeting)

@main.route('/meeting/delete/<int:id>', methods=['POST'])
@login_required
def delete_meeting(id):
    meeting = Meeting.query.get_or_404(id)
    # Optional: Delete the actual file from storage
    if meeting.audio_file:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], meeting.audio_file)
        if os.path.exists(file_path):
            os.remove(file_path)
            
    db.session.delete(meeting)
    db.session.commit()
    flash('Meeting deleted successfully')
    return redirect(url_for('main.meeting_list'))
