from telegram import ReplyKeyboardMarkup, KeyboardButton

logger_menu_buttons = [['/log'], ['/view'], ['/manage_cats']]
yes_no_buttons = [['/yes'], ['/no']]
manage_cats_buttons = [['/add_cat'], ['/edit_cat'], ['/del_cat'], ['/back']]
timeframe_buttons = [['/day'], ['/week'], ['/month']]


def make_categories_menu(categories, include_new_cat=False, include_back_button=False):

    buttons = []
    for cat in categories:
        buttons.append([cat.event_type])
    if include_new_cat:
        buttons.append(['/add_new_cat'])
    if include_back_button:
        buttons.append(['/back'])
    return ReplyKeyboardMarkup(buttons)


logger_start_menu = ReplyKeyboardMarkup(logger_menu_buttons)
manage_cats_menu = ReplyKeyboardMarkup(manage_cats_buttons)
yes_no_menu = ReplyKeyboardMarkup(yes_no_buttons, resize_keyboard=True)
timeframe_menu = ReplyKeyboardMarkup(timeframe_buttons)
