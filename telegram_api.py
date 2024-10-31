import logging
import os
from telegram import Update
from telegram.ext import (
    filters,
    MessageHandler,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackContext,
)
import whisper
from pydub import AudioSegment

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

CHECK_ALLOWED = False
ALLOWED_USERS = ["5158783121"]
ADMIN_USERS = ["5158783121"]


def check_allowed_user(func):
    async def wrapper(self, update: Update, context: CallbackContext, *args, **kwargs):
        if CHECK_ALLOWED and str(update.effective_user.id) not in ALLOWED_USERS:
            print(update.effective_user.id)
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Nie masz uprawnień do korzystania z tego bota 😥",
            )
            return
        return await func(self, update, context, *args, **kwargs)

    return wrapper


def check_admin_user(func):
    async def wrapper(self, update: Update, context: CallbackContext, *args, **kwargs):
        if str(update.effective_user.id) not in ADMIN_USERS:
            print(update.effective_user.id)
            await context.bot.send_message(
                chat_id=update.effective_chat.id, text="Nie jestes adminem."
            )
            return
        return await func(self, update, context, *args, **kwargs)

    return wrapper


class TelegramBot:
    def __init__(self, api_key: str):
        self.application = ApplicationBuilder().token(api_key).build()
        self.whisper_model = whisper.load_model("tiny.en")  # or "tiny", "small", "medium", "large"
        self._setup_handlers()

    def _setup_handlers(self):
        start_handler = CommandHandler("start", self.start)
        caps_handler = CommandHandler("caps", self.caps)
        echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), self.echo)
        unknown_handler = MessageHandler(filters.COMMAND, self.unknown)
        # admin cmd
        menu_set_handler = CommandHandler("setmenu", self.set_bot_menu)
        voice_handler = MessageHandler(filters.VOICE, self.handle_voice)

        self.application.add_handler(start_handler)
        self.application.add_handler(echo_handler)
        self.application.add_handler(caps_handler)
        self.application.add_handler(unknown_handler)
        self.application.add_handler(menu_set_handler)
        self.application.add_handler(voice_handler)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Hej <b>{update.effective_user.first_name}</b> 🖐️\n\n",
            parse_mode='HTML'
        )
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"<b><u>{update.effective_user.id}</u></b>",
            parse_mode='HTML')

    async def send_message(self, chat_id, message):
        await self.application.bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")

    async def echo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=update.message.text
        )

    async def caps(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text_caps = " ".join(context.args).upper()
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text_caps)

    async def unknown(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        command = update.message.text.split()[0] if update.message.text else "Unknown"
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Nie rozumiem polecenia: {command}. Sprawdź, czy polecenie jest poprawne."
        )
        logging.warning(f"Unknown command received: {command}")

    @check_admin_user
    async def set_bot_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        logging.warning(
            f"Admin cmd set_bot_menu called from {update.effective_chat.id}"
        )
        await self.application.bot.set_my_commands(
            [
                ("caps", "🔠 Caps"),
            ]
        )
        await update.message.reply_text("Menu ustawione!")

    async def handle_voice(self, update, context):
        voice = update.message.voice
        file_id = voice.file_id
        new_file = await context.bot.get_file(file_id)
        await new_file.download_to_drive("voice.ogg")
        transcript = self.whisper_model.transcribe("voice.ogg")
        await self.send_message(update.effective_chat.id, transcript["text"])

    def run(self):
        self.application.run_polling()


if __name__ == "__main__":
    bot = TelegramBot(api_key=os.getenv("telegram_api_key"))
    bot.run()
