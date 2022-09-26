import os
from pathlib import Path

from peewee import SqliteDatabase

from config_local import BOT_NAME, TG_TOKEN


BOT_NAME = BOT_NAME
TG_TOKEN = TG_TOKEN

DB = SqliteDatabase('%s\\adjutant_bot.db' % Path(os.getcwd()).parent)

COLOR_BARS = 'lightsteelblue'
COLOR_BARS_BORDERS = 'dimgray'
COLOR_GRID = 'lightgray'
COLORS_TRAND_LINE = 'firebrick'


