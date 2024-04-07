from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from .models import Note, WebResource, News
from . import db
import json
import requests

views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        note = request.form.get('note')

        if len(note) < 1:
            flash('Note is too short!', category='error')
        else:
            new_note = Note(data=note, user_id=current_user.id)
            db.session.add(new_note)
            db.session.commit()
            flash('Note added!', category='success')

    return render_template("home.html", user=current_user)



@views.route('/delete-note', methods=['POST'])
@login_required
def delete_note():
    note = json.loads(request.data)
    noteId = note['noteId']
    note = Note.query.get(noteId)
    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()
            return jsonify({})



@views.route('/add-resource', methods=['GET', 'POST'])
@login_required
def add_resource():
    if request.method == 'POST':
        if 'url' in request.form:
            # Handle single URL submission
            url = request.form['url']
            response = requests.post(
                f"{request.host_url}api/add_resource",
                json={'url': url},
                headers={'Content-Type': 'application/json'}
            )
        elif 'file' in request.files:
            # Handle file upload
            file = request.files['file']
            response = requests.post(
                f"{request.host_url}api/bulk_add_resources",
                files={'file': (file.filename, file, 'text/csv')},
            )
        else:
            flash('No URL or file provided', 'danger')
            return redirect(url_for('add_resource'))

        if response.status_code == 201:
            flash('Resource added successfully', 'success')
        else:
            flash(f"Error adding resource: {response.json().get('error')}", 'danger')
        
        return redirect(url_for('add_resource'))
    
    return render_template('add_resource.html', user=current_user)



@views.route('/resource-list')
@login_required
def resource_list():
    page = request.args.get('page', 1, type=int)
    domain_zone_filter = request.args.get('domain_zone', type=str)
    status_filter = request.args.get('status', type=str)

    query = WebResource.query
    if domain_zone_filter:
        query = query.filter_by(domain_zone=domain_zone_filter)
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    resources = query.paginate(page=page, per_page=10, error_out=False)
    return render_template('resource_list.html', user=current_user)



@views.route('/view_logs')
@login_required
def view_logs_page():
    try:
        response = requests.get('http://localhost:5000/api/logs')
        if response.status_code == 200:
            logs = response.json().get('logs', [])
            return render_template('view_logs.html', logs=logs, user=current_user)
        else:
            flash('Failed to retrieve logs from the API', 'error')
            return render_template('view_logs.html', logs=[], user=current_user)
    except requests.exceptions.RequestException as e:
        flash('An error occurred while connecting to the API', 'error')
        return render_template('view_logs.html', logs=[], user=current_user)
    


@views.route('/news_feed')
@login_required
def news_feed():
    return render_template('news_feed.html', user=current_user)



@views.route('/resource/<int:resource_id>')
@login_required
def resource_detail(resource_id):
    resource = WebResource.query.get_or_404(resource_id)
    news = News.query.filter_by(resource_id=resource.id).all()
    return render_template('resource_detail.html', resource=resource, news=news, user=current_user)