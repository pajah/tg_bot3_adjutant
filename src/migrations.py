
from playhouse.migrate import *
from peewee import Model, CharField, IntegerField, DateTimeField, BooleanField, ForeignKeyField
from src.config import DB
from models import Users, Events

migrator = MySQLMigrator(DB)


# user = ForeignKeyField(Users, default=1, field=Users.id)

with DB.transaction():

    field = ForeignKeyField(Users, field=Users.id, null=False, on_delete='CASCADE',
                            default=1)

    migrate(
        # migrator.drop_column('events', 'user', True)
        # migrator.alter_column_type('events', 'user', user)
        migrator.add_column('Events', 'user_id', field)
    )

migrator.database.close()