from peewee import Model, IntegerField, CharField, TextField, FloatField, DateTimeField, ForeignKeyField, BooleanField
from datetime import datetime
from .db import db

class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel):
    telegram_id = IntegerField(unique=True)
    username = CharField(null=True)
    first_name = CharField(null=True)
    reports_count = IntegerField(default=0)
    rating = IntegerField(default=0)
    created_at = DateTimeField(default=datetime.now)

class Report(BaseModel):
    user = ForeignKeyField(User, backref='reports')
    photo_path = CharField()
    latitude = FloatField()
    longitude = FloatField()
    address = CharField(null=True)
    description = TextField()
    waste_type = CharField()
    danger_level = CharField()
    status = CharField(default='new')
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

class ReportHistory(BaseModel):
    report = ForeignKeyField(Report, backref='history')
    old_status = CharField()
    new_status = CharField()
    changed_by = IntegerField()
    comment = TextField(null=True)
    created_at = DateTimeField(default=datetime.now)

class Admin(BaseModel):
    telegram_id = IntegerField(unique=True)
    username = CharField(null=True)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.now)


class Review(BaseModel):
    user = ForeignKeyField(User, backref='reviews')
    text = TextField()
    rating = IntegerField(default=5)
    is_approved = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = 'reviews'