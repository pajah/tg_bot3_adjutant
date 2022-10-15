import os
from pathlib import Path

from peewee import SqliteDatabase

from config_local import BOT_NAME, TG_TOKEN


BOT_NAME = BOT_NAME
TG_TOKEN = TG_TOKEN

LOG_FILE = '%s%slogs/main.log' % (Path(os.getcwd()), os.sep)

DB = SqliteDatabase('%s%sfake_database_new.db' % (Path(os.getcwd()).parent, os.sep))
# DB = SqliteDatabase('sadjutant_bot2.db')  # % (Path(os.getcwd()).parent, os.sep))

COLOR_BARS = 'lightsteelblue'
COLOR_BARS_BORDERS = 'dimgray'
COLOR_GRID = 'lightgray'
COLORS_TRAND_LINE = 'firebrick'
