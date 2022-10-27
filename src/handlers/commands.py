
import logging

from telegram import Update, ReplyKeyboardRemove, Message, Chat

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
from telegram import parsemode

from markups.start_menu import start_menu

from models import Users


logger = logging.getLogger(__name__)


def display_help(upd, ctx):
    """Displays help for user."""
    reply_text = '<b>Commands:</b>\n' \
                 '/help — show this help\n' \
                 '/start — start adjutant\n' \
                 '/cancel — stop adjutant\n'

    ctx.bot.send_message(chat_id=upd.effective_chat.id, text=reply_text,
                         parse_mode=parsemode.ParseMode.HTML,
                         reply_markup=start_menu)


def start_adjutant(upd, ctx):
    logger.info('At start_adjutant: %s\n' % str(upd))

    reply_text = '<b>Commands:</b>\n' \
                 '/logger\n'

    ctx.bot.send_message(chat_id=upd.effective_chat.id, text=reply_text,
                         parse_mode=parsemode.ParseMode.HTML,
                         reply_markup=start_menu)


def start(upd, ctx):
    """
    Starts bot.
    """
    logger.info('At /start command: %s\n' % str(upd))

    # GROUP CHAT
    if upd.effective_chat.type == 'group':
        chat_id = upd.effective_chat.id
        logger.info('Group chat message received: %s\n' % str(upd))

        reply_text = 'Hi! I am for personal usage now.'
        ctx.bot.send_message(chat_id=upd.effective_chat.id, reply_to_message_id=upd.message.message_id,
                             text=reply_text)
        return ConversationHandler.END

    # # PRIVATE CHAT
    elif upd.effective_chat.type == 'private':

        # user started a bot
        user_initiator, user_is_created = Users.get_or_create(
            tg_id=upd.message.from_user.id,
            defaults={
                'username': upd.message.from_user.first_name
            })
        ctx.chat_data['user_db_id'] = user_initiator.id

        if not user_is_created:
            start_adjutant(upd, ctx)
        else:  # NEW USER
            reply_text = 'Hi, %s. Type /help to get help.\n' % upd.message.from_user.first_name
            ctx.bot.send_message(chat_id=upd.effective_chat.id, reply_to_message_id=upd.message.message_id,
                                 text=reply_text)


def cancel(upd, ctx):
    user = upd.message.from_user
    logger.warning("User %s canceled the conversation.", user.first_name)
    upd.message.reply_text('Bye! I hope we can talk again some day.',
                           reply_markup=ReplyKeyboardRemove())
    ctx.chat_data = []
    return ConversationHandler.END
