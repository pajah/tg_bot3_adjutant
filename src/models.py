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
    user_id = ForeignKeyField(Users, default=1, on_update='cascade')
    is_custom = BooleanField(default=False)


class UsersEvents(BaseModel):

    user_id = ForeignKeyField(Users)
    event_id = ForeignKeyField(Events)
    created_at = DateTimeField(default=datetime.now)
    amount = FloatField(default='1')
    description = CharField(default='')


DB.create_tables([Users, Events, UsersEvents])
Users.get_or_create(tg_id=515519873, username="Pashok", created_at="2022-09-23 19:48:00.692717")
# Events.get_or_create(event_type='SMOCKING', has_amount=True, has_description=True)
# Events.get_or_create(event_type='POTATOES', has_amount=True, has_description=False)
# Events.get_or_create(event_type='WEIGHT', has_amount=True, has_description=True)
# Events.get_or_create(event_type='COFFEE', has_amount=False, has_description=False)
# Events.get_or_create(event_type='BEER', has_amount=True, has_description=True)
