from .user import create_student, create_staff
from .activity import create_activity
from App.database import db


def initialize():
    db.drop_all()
    db.create_all()
    create_student('jack', 'password')
    create_student('alice', 'password')
    create_staff('smith', 'password')
    create_activity("community service")