from telegram import ReplyKeyboardMarkup


start_menu_buttons = [
	'/logger',
	'/cancel'
	]


start_menu = ReplyKeyboardMarkup([start_menu_buttons], resize_keyboard=True)
