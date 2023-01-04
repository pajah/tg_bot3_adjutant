
import datetime
import logging

from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, Filters
from telegram import parsemode, ReplyKeyboardRemove, ReplyKeyboardMarkup

from .commands import cancel
from handlers.commands import start
from event_plotter import plot_week_events, plot_month_events, plot_day_events, \
    plot_week_events_custom, plot_month_events_custom
from markups.logger_menu import logger_menu_buttons, logger_start_menu, make_categories_menu, yes_no_menu, \
    timeframe_menu, manage_cats_menu, default_amount_menu, make_custom_cat_amount_menu, utils_menu
from models import Users, Events, UsersEvents


logger = logging.getLogger(__name__)


def start_logger(upd, ctx):
    """/loggger called"""
    logger.info('Logger has started. \n')

    tg_user_id = upd.message.from_user.id

    user, is_user_created = Users.get_or_create(tg_id=tg_user_id)
    ctx.chat_data['user_db_id'] = user.id

    reply_text = 'What can I do for you?\n'
    for option in logger_menu_buttons:
        reply_text += '%s\n' % option[0]

    ctx.bot.send_message(
        chat_id=upd.effective_chat.id,
        text=reply_text,
        parse_mode=parsemode.ParseMode.HTML,
        reply_markup=logger_start_menu)

    return LOGGER_MODE


def select_logger_mode(upd, ctx):

    logger.info('Selecting mode:  %s \n' % upd.message.text)
    db_user_id = ctx.chat_data['user_db_id']
    cats = [c for c in Events.select().where(Events.user_id == db_user_id)]
    ctx.chat_data['user_cats'] = [c.event_type for c in cats]
    ctx.chat_data['user_custom_cats'] = [c.event_type for c in cats if c.is_custom]

    if upd.message.text == '/back':
        return start_logger(upd, ctx)

    if upd.message.text == '/logger':
        reply_text = 'What can I do for you?\n'
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text=reply_text,
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=logger_start_menu)
        for option in logger_menu_buttons:
            reply_text += '%s\n' % option[0]
        return LOGGER_MODE

    if upd.message.text == '/log':
        ctx.chat_data['logger_mode'] = 'log'

        reply_text = 'Select category:'
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text=reply_text,
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=make_categories_menu(cats, include_new_cat=True, include_back_button=True))
        return LOG_EVENT

    elif upd.message.text == '/view':
        ctx.chat_data['logger_mode'] = 'view'
        reply_text = 'Select category:'
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text=reply_text,
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=make_categories_menu(cats, include_back_button=True))
        return CAT_VIEW_TIMEFRAME

    elif upd.message.text == '/manage_cats':
        ctx.chat_data['logger_mode'] = 'manage_cats'
        reply_text = 'Your current categories:\n'
        for cat in ctx.chat_data['user_cats']:
            reply_text += '<pre>%s</pre>\n' % cat
        reply_text += 'Select needed action:\n' \
                      '/add_cat \n/edit_cat\n/del_cat\n/back\n'
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text=reply_text,
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=manage_cats_menu,
            )
        return CAT_MANAGE_MODE

    elif upd.message.text == '/utils':
        ctx.chat_data['logger_mode'] = 'utils'
        reply_text = 'Select an option:\n'
        # for cat in ctx.chat_data['user_cats']:
        #     reply_text += '<pre>%s</pre>\n' % cat
        # reply_text += 'Select needed action:\n' \
        #               '/add_cat \n/edit_cat\n/del_cat\n/back\n'
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text=reply_text,
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=utils_menu,
            )
        return UTILS_MODE


def log_event(upd, ctx):
    logger.info('Log event. \n')
    logger.info('%s\n%s\n' % (upd, str(ctx.chat_data)))

    db_user_id = ctx.chat_data['user_db_id']
    cats = [c for c in Events.select().where(Events.user_id == db_user_id)]
    ctx.chat_data['user_cats'] = [c.event_type for c in cats]
    ctx.chat_data['user_custom_cats'] = [c.event_type for c in cats if c.is_custom]

    event_type = upd.message.text

    if event_type == '/add_new_cat':
        ctx.chat_data['need_log'] = True
        reply_text = 'Send new category name:\n or type /back\n'
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text=reply_text,
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=ReplyKeyboardRemove())
        return CAT_SAVE_NAME

    if upd.message.text == '/back':
        return start_logger(upd, ctx)

    if event_type not in ctx.chat_data['user_cats']:
        reply_text = 'Can\'t log. Category not found: %s.\n Aborting' % event_type
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text=reply_text,
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    tg_user_id = upd.message.from_user.id

    user, is_user_created = Users.get_or_create(tg_id=tg_user_id)
    event = Events.get(event_type=event_type, user_id=db_user_id)

    if event.has_amount:
        ctx.chat_data['need_amount'] = True
    if event.has_description:
        ctx.chat_data['need_description'] = True

    reply_text = ''
    if 'user_cats' in ctx.chat_data:
        if event_type in ctx.chat_data['user_cats']:
            logger.info('Create user event.')
            user_event = UsersEvents.create(user_id=user.id, event_id=event.id)
            if user_event:
                ctx.chat_data['last_event_id'] = user_event.id
                reply_text = 'Event for %s saved correctly!\n' % event_type

        if ctx.chat_data.get('need_amount', False):
            reply_text += 'Please set amount (default=1):\n'

            markup = make_custom_cat_amount_menu(event_type) if \
                event_type in ctx.chat_data['user_custom_cats'] else default_amount_menu

            ctx.bot.send_message(
                chat_id=upd.effective_chat.id,
                text=reply_text,
                parse_mode=parsemode.ParseMode.HTML,
                reply_markup=markup)
            return ADD_AMOUNT

        if ctx.chat_data.get('need_description', False):
            reply_text += 'Please set description (default=''):\n'
            ctx.bot.send_message(
                chat_id=upd.effective_chat.id,
                text=reply_text,
                parse_mode=parsemode.ParseMode.HTML,
                reply_markup=ReplyKeyboardMarkup([['/skip']], resize_keyboard=True))
            return ADD_DESCR

        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text=reply_text,
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=logger_start_menu)
        return start_logger(upd, ctx)


def add_amount(upd, ctx):

    provided_amount = upd.message.text
    db_user_id = ctx.chat_data['user_db_id']

    last_event_id = ctx.chat_data['last_event_id']
    event = UsersEvents.get(UsersEvents.id == last_event_id,
                            UsersEvents.user_id == db_user_id)

    reply_text = ''
    if provided_amount == '/skip':
        reply_text = 'Default amount has saved.\n'
        ctx.chat_data['need_amount'] = False
    else:
        try:
            if ',' in provided_amount:
                provided_amount = provided_amount.replace(',', '.')
            provided_amount = float(provided_amount)
        except ValueError as e:
            logger.warning(e)
            ctx.bot.send_message(
                chat_id=upd.effective_chat.id,
                text='Wrong format, please provide amount number again:',
                parse_mode=parsemode.ParseMode.HTML,
                reply_markup=ReplyKeyboardRemove())
            return ADD_AMOUNT

    if event:
        if ctx.chat_data['need_amount']:
            event.amount = provided_amount
            is_saved = event.save()
            logger.info('Is saved: %s\n' % is_saved)
            reply_text = 'Amount has saved.\n'
            ctx.chat_data['need_amount'] = False

        if ctx.chat_data.get('need_description', False):
            reply_text += 'Please set description (default=''):\n'
            ctx.bot.send_message(
                chat_id=upd.effective_chat.id,
                text=reply_text,
                parse_mode=parsemode.ParseMode.HTML,
                reply_markup=ReplyKeyboardMarkup([['/skip']], resize_keyboard=True))
            return ADD_DESCR
        else:
            ctx.bot.send_message(
                chat_id=upd.effective_chat.id,
                text=reply_text,
                parse_mode=parsemode.ParseMode.HTML,
                reply_markup=logger_start_menu)
            return start_logger(upd, ctx)


def add_description(upd, ctx):

    provided_description = upd.message.text

    if provided_description == '/skip':
        reply_text = 'Default description has saved.\n'
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text=reply_text,
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=logger_start_menu)
        ctx.chat_data['need_description'] = False
        return start_logger(upd, ctx)

    if provided_description[0] == '/':
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text='Can not set command as description. Retry:\n or /skip to leave current',
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=ReplyKeyboardMarkup([['/skip']], resize_keyboard=True))
        return ADD_DESCR

    last_event_id = ctx.chat_data['last_event_id']
    event = UsersEvents.get(UsersEvents.id == last_event_id,
                            UsersEvents.user_id == ctx.chat_data['user_db_id'])

    if event:
        event.description = provided_description
        is_saved = event.save()
        logger.info('Is saved: %s\n' % is_saved)
        reply_text = 'Description has saved.\n'
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text=reply_text,
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=ReplyKeyboardRemove())
        ctx.chat_data['need_description'] = False
        return ConversationHandler.END


def select_manage_category_mode(upd, ctx):

    logger.info('Selecting manage category mode:  %s \n' % upd.message.text)

    db_user_id = ctx.chat_data['user_db_id']
    cats = [c for c in Events.select().where(Events.user_id == db_user_id)]
    ctx.chat_data['user_cats'] = [c.event_type for c in cats]

    if upd.message.text == '/add_cat':
        reply_text = 'Send new category name:\n or type /back\n'
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text=reply_text,
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=ReplyKeyboardRemove())
        return CAT_SAVE_NAME

    elif upd.message.text == '/del_cat':
        reply_text = 'Select category to delete:'
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text=reply_text,
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=make_categories_menu(cats, include_back_button=True))
        return CAT_DEL_SELECT

    elif upd.message.text == '/edit_cat':
        reply_text = 'Select category to edit:'
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text=reply_text,
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=make_categories_menu(cats, include_back_button=True))
        return CAT_EDIT_SELECT

    elif upd.message.text == '/back':
        return start_logger(upd, ctx)

    else:
        reply_text = 'Select needed action:\n' \
                     '/add_cat \n/edit_cat\n/del_cat\n/back\n'
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text=reply_text,
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=manage_cats_menu)
        return CAT_MANAGE_MODE


def save_new_category_name(upd, ctx):

    logger.info('Setting new category name:  %s \n' % upd.message.text)

    provided_new_cat_name = upd.message.text.strip()

    if provided_new_cat_name == '/back':
        reply_text = 'Cant find needed cat for edit. Retry:\n'
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text=reply_text,
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=manage_cats_menu)
        return CAT_MANAGE_MODE

    if provided_new_cat_name in ctx.chat_data['user_cats']:
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text='Category %s already exist. Select another name:\n' % provided_new_cat_name,
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=ReplyKeyboardRemove())
        return CAT_SAVE_NAME

    if provided_new_cat_name[0] == '/':
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text='Can not set command as category name. Retry:\n',
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=ReplyKeyboardRemove())
        return CAT_SAVE_NAME

    try:
        provided_new_cat_name = str(provided_new_cat_name)
        assert len(provided_new_cat_name) < 20
        ctx.chat_data['new_cat'] = dict()
        ctx.chat_data['new_cat']['name'] = provided_new_cat_name
    except Exception as e:
        logger.warning(e)
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text='Wrong format, please provide less 20 chars',
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=ReplyKeyboardRemove())
        return CAT_SAVE_NAME

    if 'new_cat' in ctx.chat_data and 'name' in ctx.chat_data['new_cat']:
        reply_text = 'Allow amount for this category?'
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text=reply_text,
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=yes_no_menu)
        return CAT_SAVE_AMOUNT


def edit_category_name(upd, ctx):

    logger.info('Edit category name:  %s \n' % upd.message.text)

    provided_new_cat_name_for_edit = upd.message.text.strip()

    if provided_new_cat_name_for_edit in ctx.chat_data['user_cats']:
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text='Category %s already exist. Select another name:\n' % provided_new_cat_name_for_edit,
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=ReplyKeyboardRemove())
        return CAT_EDIT_NAME

    if provided_new_cat_name_for_edit == '/skip':
        reply_text = 'Old name kept.\n' \
                     'Allow amount for this category?'
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text=reply_text,
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=yes_no_menu)
        return CAT_EDIT_AMOUNT

    if provided_new_cat_name_for_edit[0] == '/':
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text='Can\'t set command as name. Select another name:\n' % provided_new_cat_name_for_edit,
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=ReplyKeyboardRemove())
        return CAT_EDIT_NAME

    try:
        cat_name_for_edit = str(provided_new_cat_name_for_edit)
        assert len(cat_name_for_edit) < 20
        ctx.chat_data['edit_cat']['new_name'] = cat_name_for_edit
    except Exception as e:
        logger.warning(e)
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text='Wrong format, please provide less 20 chars',
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=ReplyKeyboardRemove())
        return CAT_EDIT_NAME

    if 'edit_cat' in ctx.chat_data and 'new_name' in ctx.chat_data['edit_cat']:
        reply_text = 'Allow amount for this category?'
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text=reply_text,
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=yes_no_menu)
        return CAT_EDIT_AMOUNT


def save_new_category_amount(upd, ctx):

    logger.info('Setting new category amount:  %s \n' % upd.message.text)

    if upd.message.text == '/yes':
        ctx.chat_data['new_cat']['has_amount'] = True
    elif upd.message.text == '/no':
        ctx.chat_data['new_cat']['has_amount'] = False
    else:
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text='Wrong answer.\nAllow amount for this category?',
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=yes_no_menu)
        return CAT_SAVE_AMOUNT

    reply_text = 'Allow description for this category?'
    ctx.bot.send_message(
        chat_id=upd.effective_chat.id,
        text=reply_text,
        parse_mode=parsemode.ParseMode.HTML,
        reply_markup=yes_no_menu)
    return CAT_SAVE_DESCR


def edit_category_amount(upd, ctx):

    logger.info('Edit category amount:  %s \n' % upd.message.text)

    if upd.message.text == '/yes':
        ctx.chat_data['edit_cat']['has_amount'] = True
    elif upd.message.text == '/no':
        ctx.chat_data['edit_cat']['has_amount'] = False
    else:
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text='Wrong answer.\nAllow amount for this category?',
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=yes_no_menu)
        return CAT_EDIT_AMOUNT

    reply_text = 'Allow description for this category?'
    ctx.bot.send_message(
        chat_id=upd.effective_chat.id,
        text=reply_text,
        parse_mode=parsemode.ParseMode.HTML,
        reply_markup=yes_no_menu)
    return CAT_EDIT_DESCR


def save_new_category_description(upd, ctx):

    logger.info('Setting new category description:  %s \n' % upd.message.text)

    if upd.message.text == '/yes':
        ctx.chat_data['new_cat']['has_description'] = True
    elif upd.message.text == '/no':
        ctx.chat_data['new_cat']['has_description'] = False
    else:
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text='Wrong answer.\nAllow description for this category?',
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=ReplyKeyboardMarkup([['/yes', '/no']], resize_keyboard=True))
        return CAT_SAVE_AMOUNT

    db_user_id = ctx.chat_data['user_db_id']

    if 'new_cat' in ctx.chat_data:
        if all(_ in ctx.chat_data['new_cat'] for _ in ['name', 'has_description', 'has_amount']):
            logger.info('Try to save new cat do DB.')
            new_event = Events.create(event_type=ctx.chat_data['new_cat']['name'],
                                      has_amount=ctx.chat_data['new_cat']['has_amount'],
                                      has_description=ctx.chat_data['new_cat']['has_description'],
                                      user_id=db_user_id)
            if new_event:
                reply_text = 'New category has been saved:\n'\
                             '%s: has_amount (%s), has_description (%s).\n' % (new_event.event_type,
                                                                               new_event.has_amount,
                                                                               new_event.has_description)
                ctx.chat_data['user_cats'].append(ctx.chat_data['new_cat']['name'])
                ctx.bot.send_message(
                    chat_id=upd.effective_chat.id,
                    text=reply_text,
                    parse_mode=parsemode.ParseMode.HTML,
                    reply_markup=ReplyKeyboardRemove())
                ctx.chat_data.pop('new_cat')
                ctx.chat_data.pop('logger_mode')

                if ctx.chat_data.get('need_log', False):
                    cats = [c for c in Events.select().where(Events.user_id == db_user_id)]
                    reply_text += 'Select category for new event:\n'
                    ctx.bot.send_message(
                        chat_id=upd.effective_chat.id,
                        text=reply_text,
                        parse_mode=parsemode.ParseMode.HTML,
                        reply_markup=make_categories_menu(cats, include_new_cat=True))
                    return LOG_EVENT

                if ctx.chat_data.get('need_log_forgotten', False):
                    cats = [c for c in Events.select().where(Events.user_id == db_user_id)]
                    reply_text += 'Select category for new forgotten event:\n'
                    ctx.bot.send_message(
                        chat_id=upd.effective_chat.id,
                        text=reply_text,
                        parse_mode=parsemode.ParseMode.HTML,
                        reply_markup=make_categories_menu(cats, include_new_cat=True))
                    return LOG_FORGOTTEN_EVENT

                ctx.chat_data.pop('user_cats')
                return start_logger(upd, ctx)
    else:
        logger.critical(str(upd))
        logger.critical(str(ctx.chat_data))


def edit_category_description(upd, ctx):

    logger.info('Edit category description:  %s \n' % upd.message.text)

    if upd.message.text == '/yes':
        ctx.chat_data['edit_cat']['has_description'] = True
    elif upd.message.text == '/no':
        ctx.chat_data['edit_cat']['has_description'] = False
    else:
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text='Wrong answer.\nAllow description for this category?',
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=yes_no_menu, resize_keyboard=True)
        return CAT_EDIT_DESCR

    db_user_id = ctx.chat_data['user_db_id']

    if 'edit_cat' in ctx.chat_data:

        if all(_ in ctx.chat_data['edit_cat'] for _ in ['old_name', 'has_description', 'has_amount']):
            logger.info('Try to update cat in DB.')
            cat_name = ctx.chat_data['edit_cat'].get('new_name', ctx.chat_data['edit_cat']['old_name'])
            event_cat = Events.get(event_type=ctx.chat_data['edit_cat']['old_name'], user_id=db_user_id)
            event_cat.event_type = cat_name
            event_cat.has_amount = ctx.chat_data['edit_cat']['has_amount']
            event_cat.has_description = ctx.chat_data['edit_cat']['has_description']
            save_status = event_cat.save()

            if save_status:
                reply_text = 'Category has been edited:\n'\
                             '<b>%s</b>: has_amount (<i>%s</i>), ' \
                             'has_description (<i>%s</i>).\n' % (cat_name,
                                                                 event_cat.has_amount,
                                                                 event_cat.has_description)
                ctx.chat_data['user_cats'].append(cat_name)
                ctx.bot.send_message(
                    chat_id=upd.effective_chat.id,
                    text=reply_text,
                    parse_mode=parsemode.ParseMode.HTML,
                    reply_markup=logger_start_menu)
                ctx.chat_data.pop('edit_cat')
                ctx.chat_data.pop('logger_mode')
                return start_logger(upd, ctx)
    else:
        logger.critical(str(upd))
        logger.critical(str(ctx.chat_data))


def select_category_for_delete(upd, ctx):

    logger.info('Selecting cat to delete:  %s \n' % upd.message.text)
    logger.info('%s\n%s\n' % (upd, str(ctx.chat_data)))

    if upd.message.text == '/back':
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text='Aborting.',
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=manage_cats_menu)
        upd.message.text = '/manage_cats'
        return select_logger_mode(upd, ctx)

    requested_event_type = upd.message.text.strip()
    if requested_event_type not in ctx.chat_data['user_cats']:
        reply_text = 'Cant find needed cat for delete. Retry:\n'
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text=reply_text,
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=manage_cats_menu)
        return CAT_MANAGE_MODE

    user_id = upd.message.from_user.id

    user, is_user_created = Users.get_or_create(tg_id=user_id)
    ctx.chat_data['user_db_id'] = user.id
    event = Events.get(event_type=requested_event_type, user_id=ctx.chat_data['user_db_id'])
    user_events = UsersEvents.select(UsersEvents.id, UsersEvents.created_at).where(
        UsersEvents.user_id == user.id, UsersEvents.event_id == event.id).order_by(UsersEvents.created_at)

    ctx.chat_data['del_cat'] = dict()

    reply_text = ''
    if event:
        reply_text += 'Are you sure to delete %s category?\n' % requested_event_type
        ctx.chat_data['del_cat']['cat_name'] = event.event_type
    if user_events:
        reply_text += 'It contains %d saved events.\n' % len(user_events)
        reply_text += 'The oldest: %s\n' % str(user_events[0].created_at)[:16]
        reply_text += 'The newest: %s\n' % str(user_events[-1].created_at)[:16]
        ctx.chat_data['del_cat']['user_event_ids'] = [e.id for e in user_events]
    else:
        reply_text += 'There are no saved events in this category.'

    ctx.bot.send_message(
        chat_id=upd.effective_chat.id,
        text=reply_text,
        parse_mode=parsemode.ParseMode.HTML,
        reply_markup=yes_no_menu)
    return CAT_DEL_ACCEPT


def select_category_for_edit(upd, ctx):

    logger.info('Selecting cat to edit:  %s \n' % upd.message.text)
    logger.info('%s\n%s\n' % (upd, str(ctx.chat_data)))

    if upd.message.text == '/back':
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text='Aborting.',
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=manage_cats_menu)
        upd.message.text = '/manage_cats'
        return select_logger_mode(upd, ctx)

    cat_for_edit = upd.message.text.strip()

    if cat_for_edit not in ctx.chat_data['user_cats']:
        reply_text = 'Cant find needed cat for edit. Retry:\n'
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text=reply_text,
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=manage_cats_menu)
        return CAT_MANAGE_MODE

    user_id = upd.message.from_user.id

    user, is_user_created = Users.get_or_create(tg_id=user_id)
    ctx.chat_data['user_db_id'] = user.id
    event = Events.get(event_type=cat_for_edit, user_id=ctx.chat_data['user_db_id'])
    user_events = UsersEvents.select(UsersEvents.id, UsersEvents.created_at).where(
        UsersEvents.user_id == user.id, UsersEvents.event_id == event.id).order_by(UsersEvents.created_at)

    ctx.chat_data['edit_cat'] = dict()
    ctx.chat_data['edit_cat']['old_name'] = cat_for_edit

    reply_text = ''
    if event:
        reply_text += 'Set new name for selected category. Current name: <pre>%s</pre>\n' \
                      '/skip for keep current name.\n\n' % cat_for_edit
        reply_text += '<b>Current category settings:</b>\n' \
                      'Has amount: <i>%s</i>\n' \
                      'Has description: <i>%s</i>\n' % (event.has_amount, event.has_description)
        ctx.chat_data['edit_cat']['cat_name'] = event.event_type
    if user_events:
        reply_text += 'It contains %d saved events.\n' % len(user_events)
        reply_text += 'The oldest: %s\n' % str(user_events[0].created_at)[:16]
        reply_text += 'The newest: %s\n' % str(user_events[-1].created_at)[:16]
        ctx.chat_data['edit_cat']['user_event_ids'] = [e.id for e in user_events]
    else:
        reply_text += 'There are no saved events in this category.\n'

    ctx.bot.send_message(
        chat_id=upd.effective_chat.id,
        text=reply_text,
        parse_mode=parsemode.ParseMode.HTML,
        reply_markup=ReplyKeyboardMarkup([['/skip']]))
    return CAT_EDIT_NAME


def accept_cat_deletion(upd, ctx):

    logger.info('Accepted deletion of category:  %s \n' % upd.message.text)

    reply_text = ''
    if upd.message.text == '/yes':
        if 'del_cat' in ctx.chat_data:
            if 'cat_name' in ctx.chat_data['del_cat']:
                logger.info('Try to delete cat from DB.')
                delete_cat = Events.delete().where(Events.event_type == ctx.chat_data['del_cat']['cat_name']).execute()
                logger.warning('Deletion category result: %s' % delete_cat)
                if delete_cat:
                    reply_text += 'Category has been deleted: <pre>%s</pre>\n' % ctx.chat_data['del_cat']['cat_name']
            if 'user_event_ids' in ctx.chat_data['del_cat']:
                logger.info('Try to delete user events from DB.')
                delete_events = UsersEvents.delete().where(
                    (UsersEvents.user_id == ctx.chat_data['user_db_id']) &
                    (UsersEvents.id.in_(ctx.chat_data['del_cat']['user_event_ids']))).execute()

                logger.warning('Deletion events result: %s' % delete_events)
                if delete_events:
                    reply_text += 'Amount of deleted related events: %s\n' % delete_events
                    if 'last_event_id' in ctx.chat_data:
                        ctx.chat_data.pop('last_event_id')

            ctx.bot.send_message(
                chat_id=upd.effective_chat.id,
                text=reply_text,
                parse_mode=parsemode.ParseMode.HTML,
                reply_markup=logger_start_menu)
            ctx.chat_data.pop('del_cat')
            ctx.chat_data.pop('logger_mode')
            ctx.chat_data.pop('user_cats')

            return start_logger(upd, ctx)

    elif upd.message.text == '/no':
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text='Aborted.',
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=ReplyKeyboardRemove())
        ctx.chat_data.pop('del_cat')
        ctx.chat_data.pop('logger_mode')
        ctx.chat_data.pop('user_cats')
        return ConversationHandler.END
    else:
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text='Wrong answer.\nStill need to delete?',
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=yes_no_menu)
        return CAT_DEL_ACCEPT


def select_view_timeframe(upd, ctx):

    logger.info('Selecting view timeframe for cat:  %s \n' % upd.message.text)
    logger.info('%s\n%s\n' % (upd, str(ctx.chat_data)))

    if upd.message.text == '/back':
        return start_logger(upd, ctx)

    requested_event_type = upd.message.text.strip()
    if requested_event_type not in ctx.chat_data['user_cats']:
        reply_text = 'Cant find needed cat for display. Aborting.\n'
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text=reply_text,
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    ctx.chat_data['view_cat_name'] = requested_event_type

    requested_event = Events.get(Events.event_type == requested_event_type,
                                 user_id=ctx.chat_data['user_db_id'])
    ctx.chat_data['view_cat_id'] = requested_event.id

    reply_text = 'Select time frame:'
    ctx.bot.send_message(
        chat_id=upd.effective_chat.id,
        text=reply_text,
        parse_mode=parsemode.ParseMode.HTML,
        reply_markup=timeframe_menu)
    return CAT_VIEW_RENDER


def render_view_timeframe(upd, ctx):

    user_db_id = ctx.chat_data['user_db_id']

    logger.info('Render view timeframe: %s for cat %s \n' % (upd.message.text, ctx.chat_data['view_cat_name']))
    logger.info('%s\n%s\n' % (upd, str(ctx.chat_data)))

    requested_cat_name = ctx.chat_data['view_cat_name']

    requested_time_frame = upd.message.text.strip()

    if requested_time_frame == '/back':
        reply_text = 'Select category:'
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text=reply_text,
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=make_categories_menu(ctx.chat_data['user_cats'], include_back_button=True))
        return CAT_VIEW_TIMEFRAME

    if requested_time_frame == '/week':
        week_ago = datetime.date.today() - datetime.timedelta(days=7 + 1)  # for today
        week_events = UsersEvents \
            .select(UsersEvents.id, UsersEvents.created_at, UsersEvents.amount, UsersEvents.description) \
            .where(
                (UsersEvents.user_id == user_db_id) &
                (UsersEvents.event_id == ctx.chat_data['view_cat_id']) &
                (UsersEvents.created_at >= week_ago)
             )
        logger.warning('Weekly events:\n')
        logger.warning(len(week_events))
        logger.warning(str(week_events))

        if not week_events:
            reply_text = 'Seems there are no records for chosen period.\n' \
                         'Select another time frame:'
            ctx.bot.send_message(
                chat_id=upd.effective_chat.id,
                text=reply_text,
                parse_mode=parsemode.ParseMode.HTML,
                reply_markup=timeframe_menu)
            return CAT_VIEW_RENDER

        if requested_cat_name in ctx.chat_data['user_custom_cats']:
            plot_week_events_custom(user_db_id, requested_cat_name, week_events)
        else:
            plot_week_events(user_db_id, requested_cat_name, week_events)

        ctx.bot.send_photo(
            chat_id=upd.effective_chat.id,
            photo=open('temp_%s.png' % user_db_id, 'rb'),
            reply_markup=logger_start_menu)
        return start_logger(upd, ctx)

    elif requested_time_frame == '/month':
        month_ago = datetime.date.today() - datetime.timedelta(days=31 + 1)  # for today
        month_events = UsersEvents \
            .select(UsersEvents.id, UsersEvents.created_at, UsersEvents.amount, UsersEvents.description) \
            .where(
                (UsersEvents.user_id == user_db_id) &
                (UsersEvents.event_id == ctx.chat_data['view_cat_id']) &
                (UsersEvents.created_at >= month_ago)
             )
        logger.warning('Month events:\n')
        logger.warning(len(month_events))
        logger.warning(str(month_events))

        if not month_events:
            reply_text = 'Seems there are no records for chosen period.\n' \
                         'Select another time frame:'
            ctx.bot.send_message(
                chat_id=upd.effective_chat.id,
                text=reply_text,
                parse_mode=parsemode.ParseMode.HTML,
                reply_markup=timeframe_menu)
            return CAT_VIEW_RENDER

        if requested_cat_name in ctx.chat_data['user_custom_cats']:
            plot_month_events_custom(user_db_id, requested_cat_name, month_events)
        else:
            plot_month_events(user_db_id, requested_cat_name, month_events)

        ctx.bot.send_photo(
            chat_id=upd.effective_chat.id,
            photo=open('temp_%s.png' % user_db_id, 'rb'),
            reply_markup=logger_start_menu)
        return start_logger(upd, ctx)

    # 24H
    elif requested_time_frame == '/24h' or '/day':
        day_ago = datetime.date.today() - datetime.timedelta(days=1 + 1)  # for today
        day_events = UsersEvents \
            .select(UsersEvents.id, UsersEvents.created_at, UsersEvents.amount, UsersEvents.description) \
            .where(
                (UsersEvents.user_id == ctx.chat_data['user_db_id']) &
                (UsersEvents.event_id == ctx.chat_data['view_cat_id']) &
                (UsersEvents.created_at >= day_ago)
             )\
            .order_by(UsersEvents.created_at)
        logger.warning('Day events:\n')
        logger.warning(len(day_events))
        logger.warning(str(day_events))

        if not day_events:
            reply_text = 'Seems there are no records for chosen period.\n' \
                         'Select another time frame:'
            ctx.bot.send_message(
                chat_id=upd.effective_chat.id,
                text=reply_text,
                parse_mode=parsemode.ParseMode.HTML,
                reply_markup=timeframe_menu)
            return CAT_VIEW_RENDER

        plot_day_events(user_db_id, requested_cat_name, day_events)

        ctx.bot.send_photo(
            chat_id=upd.effective_chat.id,
            photo=open('temp_%s.png' % user_db_id, 'rb'),
            reply_markup=timeframe_menu)
        return start_logger(upd, ctx)
    else:
        reply_text = 'Wrong timeframe. Repeat.\n'
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text=reply_text,
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=timeframe_menu)

        return CAT_VIEW_RENDER


def select_utils_mode(upd, ctx):

    logger.info('Selecting utils mode:  %s \n' % upd.message.text)
    db_user_id = ctx.chat_data['user_db_id']
    cats = [c for c in Events.select().where(Events.user_id == db_user_id)]
    ctx.chat_data['user_cats'] = [c.event_type for c in cats]
    ctx.chat_data['user_custom_cats'] = [c.event_type for c in cats if c.is_custom]

    if upd.message.text == '/back':
        return start_logger(upd, ctx)

    if upd.message.text == '/delete_record':
        # reply_text = 'What can I do for you?\n'
        # ctx.bot.send_message(
        #     chat_id=upd.effective_chat.id,
        #     text=reply_text,
        #     parse_mode=parsemode.ParseMode.HTML,
        #     reply_markup=logger_start_menu)
        # for option in logger_menu_buttons:
        #     reply_text += '%s\n' % option[0]
        # return LOGGER_MODE
        # TBD
        pass

    if upd.message.text == '/log_forgotten':
        ctx.chat_data['logger_mode'] = 'log_forgotten'

        reply_text = 'Select category:'
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text=reply_text,
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=make_categories_menu(cats, include_new_cat=True, include_back_button=True))
        return LOG_FORGOTTEN_EVENT


def log_forgotten_event(upd, ctx):
    logger.info('Log forgotten event. \n')
    logger.info('%s\n%s\n' % (upd, str(ctx.chat_data)))

    db_user_id = ctx.chat_data['user_db_id']

    event_type = upd.message.text

    if event_type == '/add_new_cat':
        ctx.chat_data['need_log_forgotten'] = True
        reply_text = 'Send new category name:\n or type /back\n'
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text=reply_text,
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=ReplyKeyboardRemove())
        return CAT_SAVE_NAME

    if upd.message.text == '/back':
        return start_logger(upd, ctx)

    if event_type not in ctx.chat_data['user_cats']:
        reply_text = 'Can\'t log. Category not found: %s.\n Aborting' % event_type
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text=reply_text,
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    tg_user_id = upd.message.from_user.id

    user, is_user_created = Users.get_or_create(tg_id=tg_user_id)
    event = Events.get(event_type=event_type, user_id=db_user_id)

    # selected cat is ok
    if event.has_amount:
        ctx.chat_data['need_amount'] = True
    if event.has_description:
        ctx.chat_data['need_description'] = True

    reply_text = ''
    if 'user_cats' in ctx.chat_data:
        if event_type in ctx.chat_data['user_cats']:
            logger.info('Create forgotten user event.')
            reply_text += 'When the event took place?\n' \
                          'ex: ' \
                          '<pre>2022-12-31 14:15:16</pre>\n' \
                          '<pre>2022-12-31</pre>\n' \
                          '<pre>2w 7d 21h 55m 10s ago</pre>\n' \
                          '<pre>3m ago</pre>\n'
            ctx.bot.send_message(
                chat_id=upd.effective_chat.id,
                text=reply_text,
                parse_mode=parsemode.ParseMode.HTML,
                reply_markup=ReplyKeyboardRemove())
            return SET_FORGOTTEN_TIME

        #     user_event = UsersEvents.create(user_id=user.id, event_id=event.id)
        #     if user_event:
        #         ctx.chat_data['last_event_id'] = user_event.id
        #         reply_text = 'Event for %s saved correctly!\n' % event_type
        #
        # if ctx.chat_data.get('need_amount', False):
        #     reply_text += 'Please set amount (default=1):\n'
        #
        #     markup = make_custom_cat_amount_menu(event_type) if \
        #         event_type in ctx.chat_data['user_custom_cats'] else default_amount_menu
        #
        #     ctx.bot.send_message(
        #         chat_id=upd.effective_chat.id,
        #         text=reply_text,
        #         parse_mode=parsemode.ParseMode.HTML,
        #         reply_markup=markup)
        #     return ADD_AMOUNT
        #
        # if ctx.chat_data.get('need_description', False):
        #     reply_text += 'Please set description (default=''):\n'
        #     ctx.bot.send_message(
        #         chat_id=upd.effective_chat.id,
        #         text=reply_text,
        #         parse_mode=parsemode.ParseMode.HTML,
        #         reply_markup=ReplyKeyboardMarkup([['/skip']], resize_keyboard=True))
        #     return ADD_DESCR
        #
        # ctx.bot.send_message(
        #     chat_id=upd.effective_chat.id,
        #     text=reply_text,
        #     parse_mode=parsemode.ParseMode.HTML,
        #     reply_markup=logger_start_menu)
        # return start_logger(upd, ctx)


def set_forgotten_time(upd, ctx):
    logger.info("Setting time for forgotten event")


LOGGER_MODE, CAT_LIST, \
    LOG_EVENT, ADD_AMOUNT, ADD_DESCR, \
    CAT_MANAGE_MODE, CAT_SAVE_NAME, CAT_SAVE_AMOUNT, CAT_SAVE_DESCR, \
    CAT_DEL_SELECT, CAT_DEL_ACCEPT, \
    CAT_EDIT_SELECT, CAT_EDIT_NAME, CAT_EDIT_AMOUNT, CAT_EDIT_DESCR, \
    UTILS_MODE, LOG_FORGOTTEN_EVENT, SET_FORGOTTEN_TIME, \
    CAT_VIEW_TIMEFRAME, CAT_VIEW_RENDER = map(chr, range(20))


logger_handler = ConversationHandler(
    entry_points=[CommandHandler('logger', start_logger)],

    states={
        LOGGER_MODE: [MessageHandler(Filters.text, select_logger_mode)],
        LOG_EVENT: [MessageHandler(Filters.text, log_event)],
        ADD_AMOUNT: [MessageHandler(Filters.text, add_amount)],
        ADD_DESCR: [MessageHandler(Filters.text, add_description)],

        CAT_MANAGE_MODE: [MessageHandler(Filters.text, select_manage_category_mode)],
        CAT_SAVE_NAME: [MessageHandler(Filters.text, save_new_category_name)],
        CAT_SAVE_AMOUNT: [MessageHandler(Filters.text, save_new_category_amount)],
        CAT_SAVE_DESCR: [MessageHandler(Filters.text, save_new_category_description)],

        CAT_DEL_SELECT: [MessageHandler(Filters.text, select_category_for_delete)],
        CAT_DEL_ACCEPT: [MessageHandler(Filters.text, accept_cat_deletion)],

        CAT_EDIT_SELECT: [MessageHandler(Filters.text, select_category_for_edit)],
        CAT_EDIT_NAME: [MessageHandler(Filters.text, edit_category_name)],
        CAT_EDIT_AMOUNT: [MessageHandler(Filters.text, edit_category_amount)],
        CAT_EDIT_DESCR: [MessageHandler(Filters.text, edit_category_description)],

        UTILS_MODE: [MessageHandler(Filters.text, select_utils_mode)],
        LOG_FORGOTTEN_EVENT: [MessageHandler(Filters.text, log_forgotten_event)],
        SET_FORGOTTEN_TIME: [MessageHandler(Filters.text, set_forgotten_time)],

        CAT_VIEW_TIMEFRAME: [MessageHandler(Filters.text, select_view_timeframe)],
        CAT_VIEW_RENDER: [MessageHandler(Filters.text, render_view_timeframe)],
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)
