
from bot import bot
import logging

# from jobs.sample import broadcast_job
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, InlineQueryHandler

from handlers.commands import start, display_help, cancel
from handlers.event_logger import logger_handler

logger = logging.getLogger(__name__)


def debug(upd, ctx):
    msg = '%s\n%s' % (str(upd), str(ctx.chat_data))
    ctx.bot.send_message(upd.effective_chat.id, msg)


def bot_run():
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)

    updater = Updater(bot=bot, workers=4, use_context=True)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler(command='start', callback=start))
    dp.add_handler(CommandHandler(command='help', callback=display_help))
    dp.add_handler(CommandHandler(command='cancel', callback=cancel))
    dp.add_handler(CommandHandler(command='debug', callback=debug))
    dp.add_handler(logger_handler)

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    bot_run()
