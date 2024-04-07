from os import path
import os
from flask import Flask, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from celery import Celery
import logging
from logging.handlers import RotatingFileHandler
import yaml

db = SQLAlchemy()
DB_NAME = "database.db"

celery = Celery(__name__, broker='redis://localhost:6379/0') # инициализация celery глобально

def create_app():
    app = Flask(__name__)
    app.logger.info('Application startup.')
    with open("config.yaml", "r") as yamlfile:
        cfg = yaml.load(yamlfile, Loader=yaml.FullLoader)

    app.config['SECRET_KEY'] = 'super secret key'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    app.config['SQLALCHEMY_ECHO'] = True
    app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'  # надо установить redis
    app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
    
    celery.conf.update(app.config)
    db.init_app(app)
    setup_logging(app)

    from .views import views
    from .auth import auth
    from .api import api

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(api, url_prefix='/api')

    from .models import User, Note, News

    create_database(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app



def create_database(app):
    with app.app_context():
        if not path.exists('website/' + DB_NAME):
            db.create_all()
            app.logger.info('Created database.')



def setup_logging(app):
    #if not app.debug:
    log_file_path = os.path.join(app.root_path, 'logs', 'app.log')
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

    file_handler = RotatingFileHandler(log_file_path, maxBytes=1024 * 1024, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Logging enabled.')