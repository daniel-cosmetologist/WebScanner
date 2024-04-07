from flask import Blueprint, request, jsonify, current_app, render_template, redirect, url_for
from werkzeug.utils import secure_filename
import os
import csv
import zipfile
from .models import WebResource
from urllib.parse import urlparse, parse_qs
from .models import WebResource, User, News
from . import db, celery
from flask_login import current_user, login_required



api = Blueprint('api', __name__)



@api.route('/add_resource', methods=['POST'])
def add_resource():
    current_app.logger.info('API request: /add_resource')
    data = request.get_json()
    current_app.logger.info(f'/add_resourse data: {data}')
    url = data.get('url')
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    parsed_url = urlparse(url)
    protocol = parsed_url.scheme
    domain_parts = parsed_url.netloc.split('.')
    domain = '.'.join(domain_parts[-2:])  # вытаскиваем домен
    domain_zone = domain_parts[-1] if len(domain_parts) > 1 else ''
    path = parsed_url.path
    query_parameters = parse_qs(parsed_url.query)

    new_resource = WebResource(
        url=url,
        protocol=protocol,
        domain=domain,
        domain_zone=domain_zone,
        path=path,
        query_parameters=query_parameters
    )

    db.session.add(new_resource)
    try:
        db.session.commit()
        current_app.logger.info('New record to the DB')
        return jsonify({"status": "success", "data": {
            "url": url,
            "protocol": protocol,
            "domain": domain,
            "domain_zone": domain_zone,
            "path": path,
            "query_parameters": query_parameters
        }}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Could not save the resource", "message": str(e)}), 500



@celery.task(bind=True)
def process_resource_csv(self, csv_path):     # асинхронная задача Celery
    with current_app.app_context(): 
        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            csv_reader = csv.reader(csvfile)
            for row in csv_reader:
                if row:
                    url = row[0]
                    parsed_url = urlparse(url)
                    protocol = parsed_url.scheme
                    domain_parts = parsed_url.netloc.split('.')
                    domain = '.'.join(domain_parts[-2:])  # вытаскиваем домен
                    domain_zone = domain_parts[-1] if len(domain_parts) > 1 else ''
                    path = parsed_url.path
                    query_parameters = parse_qs(parsed_url.query)

                    new_resource = WebResource(
                        url=url,
                        protocol=protocol,
                        domain=domain,
                        domain_zone=domain_zone,
                        path=path,
                        query_parameters=query_parameters
                    )

                    db.session.add(new_resource)
            try:
                db.session.commit() 
                current_app.logger.info('New record to the DB')
            except Exception as e:
                db.session.rollback()  # Откат изменений в случае ошибки
                raise self.retry(exc=e)  # Повторная попытка выполнения задачи, если это предусмотрено конфигурацией

    os.remove(csv_path)
    os.remove(os.path.join(os.path.dirname(csv_path), os.path.basename(csv_path).replace('.csv', '.zip')))



@api.route('/bulk_add_resources', methods=['POST'])
def bulk_add_resources():
    current_app.logger.info('API request: /bulk_add_resources')
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and zipfile.is_zipfile(file): # проверим что файл является ZIP-архивом
        filename = secure_filename(file.filename) # временная директория
        temp_dir = os.path.join(current_app.root_path, 'tmp')
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        file_path = os.path.join(temp_dir, filename)
        file.save(file_path)


        with zipfile.ZipFile(file_path, 'r') as zip_ref:    # Распаковываем ZIP и читаем CSV
            zip_ref.extractall(temp_dir)
            csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv')]
            if not csv_files:
                return jsonify({"error": "No CSV file in ZIP archive"}), 400
            csv_path = os.path.join(temp_dir, csv_files[0])
            process_resource_csv.delay(csv_path)  # .delay() для асинхронного вызова задачи


        with open(csv_path, newline='', encoding='utf-8') as csvfile: # Обработка каждой строки csv
            csv_reader = csv.reader(csvfile)
            for row in csv_reader:
                if row:  # в каждой строке только один URL
                    url = row[0]
                    parsed_url = urlparse(url)
                    protocol = parsed_url.scheme
                    domain = parsed_url.netloc
                    path = parsed_url.path
                    query_parameters = parse_qs(parsed_url.query)

                    new_resource = WebResource( # создаем и добавляем новый ресурс
                        url=url,
                        protocol=protocol,
                        domain=domain,
                        path=path,
                        query_parameters=query_parameters
                    )
                    db.session.add(new_resource)
            db.session.commit()  # коммитим изменения после обработки всех URL
            current_app.logger.info('New record to the DB')

        os.remove(file_path) # удаляем временные файлы
        os.remove(csv_path)

        return jsonify({"status": "success", "message": "Resources added successfully"}), 201
    else:
        return jsonify({"error": "Uploaded file is not a valid zip file"}), 400
    
    



@api.route('/delete_resource/<resource_id>', methods=['DELETE'])
def delete_resource(resource_id):
    try:
        resource = WebResource.query.get(resource_id)
        if resource:
            db.session.delete(resource)
            db.session.commit()
            return jsonify({'message': 'Resource deleted successfully'}), 200
        else:
            return jsonify({'error': 'Resource not found'}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete the resource', 'message': str(e)}), 500



@api.route('/add_screenshot/<uuid>', methods=['POST'])
def add_screenshot(uuid):
    current_app.logger.info('API request: /add_screenshot')
    resource = WebResource.query.filter_by(id=uuid).first()
    if resource is None:
        return jsonify({"error": "Resource not found"}), 404

    if 'screenshot' not in request.files:
        return jsonify({"error": "No screenshot file provided"}), 400

    screenshot = request.files['screenshot']
    if screenshot.filename == '':
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(screenshot.filename)
    screenshot_path = os.path.join(current_app.root_path, 'static', 'screenshots', filename)
    try:
        os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
        screenshot.save(screenshot_path)
        resource.screenshot_path = screenshot_path
        db.session.commit()
        current_app.logger.info('New record to the DB')
        return jsonify({"status": "success", "message": "Screenshot added successfully"}), 200
    except Exception as e:
        return jsonify({"error": "Failed to save screenshot", "message": str(e)}), 500



@api.route('/resources', methods=['GET'])
def list_resources():
    current_app.logger.info('API request: /resources')
    page = request.args.get('page', 1, type=int)
    domain_zone_filter = request.args.get('domain_zone', type=str)
    status_filter = request.args.get('status', type=str)  # предполагает наличие поля status в модели
    
    query = WebResource.query
    
    if domain_zone_filter:
        query = query.filter_by(domain_zone=domain_zone_filter)
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    resources = query.paginate(page=page, per_page=10, error_out=False)
    
    data = []
    for resource in resources.items:
        data.append({
            "id": resource.id,
            "url": resource.url,
            "protocol": resource.protocol,
            "domain": resource.domain,
            "domain_zone": resource.domain_zone,
            "path": resource.path,
            "query_parameters": resource.query_parameters,
            "screenshot_path": resource.screenshot_path,
            "status": getattr(resource, 'status', 'unknown')  # если у вас есть поле статуса
        })
    
    return jsonify({
        "page": page,
        "pages": resources.pages,
        "total": resources.total,
        "resources": data
    }), 200



@api.route('/logs', methods=['GET'])
def view_logs():
    current_app.logger.info('API request: /logs')
    log_file_path = os.path.join(current_app.root_path, 'logs', 'app.log')
    try:
        with open(log_file_path, "r") as log_file:
            log_lines = log_file.readlines()[-20:]      # последние 20 строк из файла лога
        return jsonify({"logs": log_lines}), 200
    except FileNotFoundError:
        return jsonify({"error": "Log file not found"}), 404
    


@api.route('/news_by_resource/<resource_id>', methods=['GET'])
def get_news_by_resource(resource_id):
    try:
        resource_news = News.query.filter_by(resource_id=resource_id).all()

        news_data = [{
            'title': news.title,
            'content': news.content
        } for news in resource_news]

        return jsonify({'news': news_data}), 200
    
    except Exception as e:
        return jsonify({'error': 'Failed to fetch news for the resource', 'message': str(e)}), 500

