from peewee import Model, CharField, IntegerField, DateTimeField, BooleanField, ForeignKeyField, FloatField, \
    PrimaryKeyField, BlobField, TextField
from config import DB

from datetime import datetime


class BaseModel(Model):

    class Meta:

        database = DB


class Users(BaseModel):

    tg_id = IntegerField()
    username = CharField()
    created_at = DateTimeField(default=datetime.now)


class Events(BaseModel):

    event_type = CharField(unique=True)
    has_amount = BooleanField(default=True)
    has_description = BooleanField(default=True)


class UsersEvents(BaseModel):

    user = ForeignKeyField(Users)
    event = ForeignKeyField(Events)
    created_at = DateTimeField(default=datetime.now)
    amount = FloatField(default='1')
    description = CharField(default='')


DB.create_tables([Users, Events, UsersEvents])
Events.get_or_create(event_type='SMOCKING', has_amount=True, has_description=True)
Events.get_or_create(event_type='POTATOES', has_amount=True, has_description=False)
Events.get_or_create(event_type='WEIGHT', has_amount=True, has_description=True)
Events.get_or_create(event_type='COFFEE', has_amount=False, has_description=False)
Events.get_or_create(event_type='BEER', has_amount=True, has_description=True)
