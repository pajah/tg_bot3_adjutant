
import datetime
import logging

from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, Filters
from telegram import parsemode, ReplyKeyboardRemove, ReplyKeyboardMarkup

from .commands import cancel
from event_plotter import plot_week_events, plot_month_events, plot_day_events
from markups.logger_menu import logger_menu_buttons, logger_start_menu, make_categories_menu, yes_no_menu, \
    timeframe_menu, manage_cats_menu
from models import Users, Events, UsersEvents


logger = logging.getLogger(__name__)


def start_logger(upd, ctx):
    logger.info('Logger has started. \n')

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
    cats = [c for c in Events.select()]

    if upd.message.text == '/log':

        logger.warning(cats)
        ctx.chat_data['logger_mode'] = 'log'
        ctx.chat_data['user_cats'] = [c.event_type for c in cats]
        reply_text = 'Select category:'
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text=reply_text,
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=make_categories_menu(cats, include_new_cat=True))
        return LOG_EVENT

    elif upd.message.text == '/view':
        ctx.chat_data['logger_mode'] = 'view'
        ctx.chat_data['user_cats'] = [c.event_type for c in cats]
        reply_text = 'Select category:'
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text=reply_text,
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=make_categories_menu(cats))
        return CAT_VIEW_TIMEFRAME

    elif upd.message.text == '/manage_cats':
        ctx.chat_data['logger_mode'] = 'manage_cats'
        ctx.chat_data['user_cats'] = [c.event_type for c in cats]
        reply_text = 'Your current categories:\n'
        for cat in ctx.chat_data['user_cats']:
            reply_text += '<pre>%s</pre>\n' % cat
        reply_text += 'Select needed action:\n'
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text=reply_text,
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=manage_cats_menu)
        return CAT_MANAGE_MODE


def log_event(upd, ctx):
    logger.info('Log event. \n')
    logger.info('%s\n%s\n' % (upd, str(ctx.chat_data)))

    event_type = upd.message.text

    if event_type == '/add_new_cat':
        ctx.chat_data['need_log'] = True
        reply_text = 'Send new category name:'
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text=reply_text,
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=ReplyKeyboardRemove())
        return CAT_SAVE_NAME

    if event_type not in ctx.chat_data['user_cats']:
        reply_text = 'Can\'t log. Category not found: %s.\n Aborting' % event_type
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text=reply_text,
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    user_id = upd.message.from_user.id

    user, is_user_created = Users.get_or_create(tg_id=user_id)
    event = Events.get(event_type=event_type)

    if event.has_amount:
        ctx.chat_data['need_amount'] = True
    if event.has_description:
        ctx.chat_data['need_description'] = True

    reply_text = ''
    if 'user_cats' in ctx.chat_data:
        if event_type in ctx.chat_data['user_cats']:
            logger.info('Create user event.')
            user_event = UsersEvents.create(user=user.id, event=event.id)
            if user_event:
                ctx.chat_data['last_event_id'] = user_event.id
                reply_text = 'Event for %s saved correctly!\n' % event_type

        if ctx.chat_data.get('need_amount', False):
            reply_text += 'Please set amount (default=1):\n'
            ctx.bot.send_message(
                chat_id=upd.effective_chat.id,
                text=reply_text,
                parse_mode=parsemode.ParseMode.HTML,
                reply_markup=ReplyKeyboardMarkup([['0.5'], ['1'], ['/skip']]))
            return ADD_AMOUNT

        if ctx.chat_data.get('need_description', False):
            reply_text += 'Please set description (default=''):\n'
            ctx.bot.send_message(
                chat_id=upd.effective_chat.id,
                text=reply_text,
                parse_mode=parsemode.ParseMode.HTML,
                reply_markup=ReplyKeyboardMarkup([['/skip']]))
            return ADD_DESCR

        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text=reply_text,
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END


def add_amount(upd, ctx):

    provided_amount = upd.message.text

    last_event_id = ctx.chat_data['last_event_id']
    event = UsersEvents.get(UsersEvents.id == last_event_id)

    reply_text = ''
    if provided_amount == '/skip':
        reply_text = 'Default amount has saved.\n'
        ctx.chat_data['need_amount'] = False
    else:
        try:
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
                reply_markup=ReplyKeyboardMarkup([['/skip']]))
            return ADD_DESCR
        else:
            ctx.bot.send_message(
                chat_id=upd.effective_chat.id,
                text=reply_text,
                parse_mode=parsemode.ParseMode.HTML,
                reply_markup=ReplyKeyboardRemove())
            return ConversationHandler.END


def add_description(upd, ctx):

    provided_description = upd.message.text

    if provided_description == '/skip':
        reply_text = 'Default description has saved.\n'
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text=reply_text,
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=ReplyKeyboardRemove())
        ctx.chat_data['need_description'] = False
        return ConversationHandler.END

    last_event_id = ctx.chat_data['last_event_id']
    event = UsersEvents.get(UsersEvents.id == last_event_id)

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

    if upd.message.text == '/add_cat':
        reply_text = 'Send new category name:'
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text=reply_text,
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=ReplyKeyboardRemove())
        return CAT_SAVE_NAME

    elif upd.message.text == '/del_cat':

        cats = [c for c in Events.select()]
        ctx.chat_data['user_cats'] = [c.event_type for c in cats]

        reply_text = 'Select category to delete:'
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text=reply_text,
            parse_mode=parsemode.ParseMode.HTML,
            reply_markup=make_categories_menu(cats, include_back_button=True))

        return CAT_DEL_SELECT

    elif upd.message.text == '/back':

        return start_logger(upd, ctx)


def save_new_category_name(upd, ctx):

    logger.info('Setting new category name:  %s \n' % upd.message.text)

    provided_new_cat_name = upd.message.text.strip()

    if provided_new_cat_name in ctx.chat_data['user_cats']:
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text='Category %s already exist. Select another name:\n' % provided_new_cat_name,
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
            reply_markup=ReplyKeyboardMarkup([['/yes', '/no']]))
        return CAT_SAVE_AMOUNT

    if 'new_cat' in ctx.chat_data:
        if all(_ in ctx.chat_data['new_cat'] for _ in ['name', 'has_description', 'has_amount']):
            logger.info('Try to save new cat do DB.')
            new_event = Events.create(event_type=ctx.chat_data['new_cat']['name'],
                                      has_amount=ctx.chat_data['new_cat']['has_amount'],
                                      has_description=ctx.chat_data['new_cat']['has_description'])
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
                    cats = [c for c in Events.select()]
                    reply_text += 'Select category for new event:\n'
                    ctx.bot.send_message(
                        chat_id=upd.effective_chat.id,
                        text=reply_text,
                        parse_mode=parsemode.ParseMode.HTML,
                        reply_markup=make_categories_menu(cats, include_new_cat=True))
                    return LOG_EVENT
                ctx.chat_data.pop('user_cats')
                return ConversationHandler.END
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
    event = Events.get(event_type=requested_event_type)
    user_events = UsersEvents.select(UsersEvents.id, UsersEvents.created_at).where(
        UsersEvents.user_id == user.id, UsersEvents.event_id == event.id).order_by(UsersEvents.created_at)

    ctx.chat_data['del_cat'] = dict()
    ctx.chat_data['del_cat']['user_id_db'] = user.id

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
                    reply_text += 'Category has been deleted: %s\n' % ctx.chat_data['del_cat']['cat_name']
            if 'user_event_ids' in ctx.chat_data['del_cat']:
                logger.info('Try to delete user events from DB.')
                delete_events = UsersEvents.delete().where(
                    (UsersEvents.user_id == ctx.chat_data['del_cat']['user_id_db']) &
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
                reply_markup=ReplyKeyboardRemove())
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


def select_vew_timeframe(upd, ctx):

    logger.info('Selecting view timeframe for cat:  %s \n' % upd.message.text)
    logger.info('%s\n%s\n' % (upd, str(ctx.chat_data)))

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
    requested_event = Events.get(Events.event_type == requested_event_type)
    ctx.chat_data['view_cat_id'] = requested_event.id

    user, _ = Users.get_or_create(tg_id=upd.message.from_user.id)
    ctx.chat_data['user_id'] = user.id  # move to general

    reply_text = 'Select time frame:'
    ctx.bot.send_message(
        chat_id=upd.effective_chat.id,
        text=reply_text,
        parse_mode=parsemode.ParseMode.HTML,
        reply_markup=timeframe_menu)
    return CAT_VIEW_RENDER


def render_view_timeframe(upd, ctx):

    logger.info('Render view timeframe: %s for cat %s \n' % (upd.message.text, ctx.chat_data['view_cat_name']))
    logger.info('%s\n%s\n' % (upd, str(ctx.chat_data)))

    requested_cat_name = ctx.chat_data['view_cat_name']

    requested_time_frame = upd.message.text.strip()

    if requested_time_frame == '/week':
        week_ago = datetime.date.today() - datetime.timedelta(days=7 + 1)  # for today
        week_events = UsersEvents \
            .select(UsersEvents.id, UsersEvents.created_at, UsersEvents.amount, UsersEvents.description) \
            .where(
                (UsersEvents.user_id == ctx.chat_data['user_id']) &
                (UsersEvents.event_id == ctx.chat_data['view_cat_id']) &
                (UsersEvents.created_at >= week_ago)
             )
        logger.warning('Weekly events:\n')
        logger.warning(len(week_events))
        logger.warning(str(week_events))

        plot_week_events(requested_cat_name, week_events)

        ctx.bot.send_photo(
            chat_id=upd.effective_chat.id,
            photo=open('temp.png', 'rb'),
            reply_markup=timeframe_menu)
        return start_logger(upd, ctx)

    elif requested_time_frame == '/month':
        month_ago = datetime.date.today() - datetime.timedelta(days=31 + 1)  # for today
        month_events = UsersEvents \
            .select(UsersEvents.id, UsersEvents.created_at, UsersEvents.amount, UsersEvents.description) \
            .where(
                (UsersEvents.user_id == ctx.chat_data['user_id']) &
                (UsersEvents.event_id == ctx.chat_data['view_cat_id']) &
                (UsersEvents.created_at >= month_ago)
             )
        logger.warning('Month events:\n')
        logger.warning(len(month_events))
        logger.warning(str(month_events))

        plot_month_events(requested_cat_name, month_events)

        ctx.bot.send_photo(
            chat_id=upd.effective_chat.id,
            photo=open('temp.png', 'rb'),
            reply_markup=timeframe_menu)
        return start_logger(upd, ctx)

    # DAY
    elif requested_time_frame == '/day':
        day_ago = datetime.date.today() - datetime.timedelta(days=1 + 1)  # for today
        day_events = UsersEvents \
            .select(UsersEvents.id, UsersEvents.created_at, UsersEvents.amount, UsersEvents.description) \
            .where(
                (UsersEvents.user_id == ctx.chat_data['user_id']) &
                (UsersEvents.event_id == ctx.chat_data['view_cat_id']) &
                (UsersEvents.created_at >= day_ago)
             )\
            .order_by(UsersEvents.created_at)
        logger.warning('Day events:\n')
        logger.warning(len(day_events))
        logger.warning(str(day_events))

        plot_day_events(requested_cat_name, day_events)

        ctx.bot.send_photo(
            chat_id=upd.effective_chat.id,
            photo=open('temp.png', 'rb'),
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


LOGGER_MODE, CAT_LIST, \
    LOG_EVENT, ADD_AMOUNT, ADD_DESCR, \
    CAT_MANAGE_MODE, CAT_SAVE_NAME, CAT_SAVE_AMOUNT, CAT_SAVE_DESCR, \
    CAT_DEL_SELECT, CAT_DEL_ACCEPT, \
    CAT_VIEW_TIMEFRAME, CAT_VIEW_RENDER = map(chr, range(13))


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

        CAT_VIEW_TIMEFRAME: [MessageHandler(Filters.text, select_vew_timeframe)],
        CAT_VIEW_RENDER: [MessageHandler(Filters.text, render_view_timeframe)],
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)
