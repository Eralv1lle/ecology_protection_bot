import os
from peewee import SqliteDatabase
from dotenv import load_dotenv

load_dotenv()

DATABASE_PATH = os.getenv('DATABASE_PATH', 'eco_monitoring.db')

db = SqliteDatabase(DATABASE_PATH)

def initialize_db():
    from .models import User, Report, ReportHistory, Admin, Review
    db.connect()
    db.create_tables([User, Report, ReportHistory, Admin, Review])
    db.close()
