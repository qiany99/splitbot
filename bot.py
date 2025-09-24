import os
from telegram.ext import Application, CommandHandler
from dotenv import load_dotenv

load_dotenv("token.env")
TOKEN = os.getenv("BOT_TOKEN")

async def start(update, context):
    await update.message.reply_text("Hello! I am The Split Bot! I am here to manage your group expenses. Use /help to see what I can do.")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()

if __name__ == "__main__":
    main()