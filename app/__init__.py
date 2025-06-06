#import 
from flask import Flask
from instance.models import db, migrate
from flask_session import Session

def create_app():
    from .app import create_app as _create_app
    return _create_app() 
