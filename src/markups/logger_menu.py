from telegram import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

logger_menu_buttons = [['/log'], ['/view'], ['/manage_cats'], ['/cancel']]
yes_no_buttons = [['/yes'], ['/no']]
manage_cats_buttons = [['/add_cat'], ['/edit_cat'], ['/del_cat'], ['/back']]
timeframe_buttons = [['/day'], ['/week'], ['/month'], ['/back']]
default_amount_buttons = [['0.5'], ['1'], ['2']]


def make_categories_menu(categories, include_new_cat=False, include_back_button=False):

    buttons = []
    for cat in categories:
        buttons.append([cat if isinstance(cat, str) else cat.event_type])
    if include_new_cat:
        buttons.append(['/add_new_cat'])
    if include_back_button:
        buttons.append(['/back'])
    return ReplyKeyboardMarkup(buttons)


def make_custom_cat_amount_menu(cat_name, **kwargs):
    if cat_name == 'POTATOES':
        buttons = [['1'], ['2']]
        return ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    elif cat_name == 'SMOCKING':
        buttons = [['0.5'], ['1']]
        return ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    elif cat_name == 'WEIGHT':
        return ReplyKeyboardRemove()


logger_start_menu = ReplyKeyboardMarkup(logger_menu_buttons, resize_keyboard=True)
manage_cats_menu = ReplyKeyboardMarkup(manage_cats_buttons, resize_keyboard=True)
yes_no_menu = ReplyKeyboardMarkup(yes_no_buttons, resize_keyboard=True)
timeframe_menu = ReplyKeyboardMarkup(timeframe_buttons, resize_keyboard=True)
default_amount_menu = ReplyKeyboardMarkup(default_amount_buttons, resize_keyboard=True)