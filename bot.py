import logging, anilist_to_mal, html, json, traceback, os

from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    update.message.reply_text('Send me your AniList username, MediaType and title language in following format\n\n'
                              'username\n(ANIME | MANGA)\n(english | romaji | native)\n\n'
                              'See /help for example')


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('Example:\n\nPROxZIMA\nANIME\nenglish\n\n'
                              'MediaType and title language is optional\nBy default MediaType = ANIME, title = english')

    update.message.reply_text('Go to https://myanimelist.net/import.php and select "MyAnimeList Import" under "Import to My List".')


def unknownMedia(update: Update, context: CallbackContext) -> None:
    """Send a message when the unknown media found."""
    update.message.reply_text('Send text message only.')


def error_handler(update: Update, context: CallbackContext) -> None:
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = ''.join(tb_list)

    # Build the message with some markup and additional information about what happened.
    # You might need to add some logic to deal with messages longer than the 4096 character limit.
    message = (
        f'An exception was raised while handling an update\n'
        f'<pre>update = {html.escape(json.dumps(update.to_dict(), indent=2, ensure_ascii=False))}'
        '</pre>\n\n'
        f'<pre>{html.escape(tb_string)}</pre>'
    )

    # Finally, send the message
    context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode=ParseMode.HTML)


def userData(update: Update, context: CallbackContext) -> None:
    """Using provided details for fetching userData."""

    details = [i.strip() for i in update.message.text.split('\n')]

    username = details[0]
    type_ = 'ANIME'
    title = 'english'


    if len(details) == 3:
        if details[2].lower() in ['english', 'romaji', 'native']:
            title = details[2].lower()
        else:
            update.message.reply_text('Improper title language :(\n\nTry english | romaji | native')
            return

        type_ = details[1].upper()

    elif len(details) == 2:
        if details[1].upper() in ['ANIME', 'MANGA']:
            type_ = details[1].upper()
        elif details[1].lower() in ['english', 'romaji', 'native']:
            title = details[1].lower()
        else:
            update.message.reply_text(f'Invalid argumet received : {details[1]}')
            return

    elif len(details) > 3:
        update.message.reply_text('Make sure to send only 3 or less queries')
        return

    file = anilist_to_mal.fileParser(username = username, type_ = type_, title = title)

    if file[-1] == '!':
        update.message.reply_text(file)
    else:
        with open(file, 'rb') as file:
            context.bot.sendDocument(chat_id=update.effective_chat.id, document=file)
            update.message.reply_text('✔︎ XML successfully exported')


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
    updater = Updater(BOT_TOKEN , use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))

    # on noncommand i.e message - userData the message on Telegram
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, userData))

    dispatcher.add_handler(MessageHandler(~Filters.text & ~Filters.command, unknownMedia))

    # Error handler
    dispatcher.add_error_handler(error_handler)

    # Start the Bot
    updater.start_polling()


    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
