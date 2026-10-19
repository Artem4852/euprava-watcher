import os, dotenv, json
from zoneinfo import ZoneInfo
import html
import asyncio
import secrets
import logging
from datetime import datetime, timedelta, timezone
from telegram import Bot, ForceReply, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, MessageHandler, filters

from main import fetch_available, filter_available

dotenv.load_dotenv()

token = os.getenv("TELEGRAM_BOT_TOKEN")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def reply_keyboard(buttons):
    if isinstance(buttons[0], list):
        keyboard = [[KeyboardButton(button) for button in row] for row in buttons]
    else:
        keyboard = [[KeyboardButton(button) for button in buttons]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update, context):
    await update.message.reply_text(
        "Hello. I am the bot meant to watch euprava for B kategorija. I will resend you all slots whenever there are changes. Your id is " + str(update.message.chat_id)
    )

async def recheck_site(context):
    print("Rechecking site for available slots...")
    user_ids = [879805663]
    places = {
        879805663: ["LJUBLJANA", "DOMŽALE"]
    }

    data = fetch_available()
    for user in user_ids:
        filtered_data = filter_available(data, filter_places=places[user])
        if not filtered_data:
            continue
        months = {}
        for slot in filtered_data:
            date = datetime.strptime(slot["date"], "%d. %m. %Y")
            month = date.strftime("%b")
            if month not in months:
                months[month] = []
            months[month].append(slot)

        last_seen = []

        months = dict(sorted(months.items(), key=lambda x: datetime.strptime(x[0], "%b").month))

        message = "<b>Available slots:</b>\n"
        for month, slots in months.items():
            message += f"{month}:\n"

            slots = sorted(slots, key=lambda x: datetime.strptime(x["date"], "%d. %m. %Y"))
            for slot in slots:
                formatted_date = datetime.strptime(slot["date"], "%d. %m. %Y").strftime("%d %b")

                event_timestamp = datetime.strptime(f"{slot['date']} {slot['time']}", "%d. %m. %Y %H:%M").timestamp()

                last_seen.append(f"{slot['date']} {slot['time']} - {slot['place']}")

                message += (
                    f'- <tg-time unix="{event_timestamp}" format="wdt">{formatted_date} at {slot["time"]}</tg-time> - '
                    f'{html.escape(slot["place"].capitalize())}\n'
                )

        if not os.path.exists(f"last_seen_{user}.json"):
            with open(f"last_seen_{user}.json", "w") as f:
                json.dump([], f)
        with open(f"last_seen_{user}.json", "r") as f:
            try:
                previous_last_seen = json.load(f)
            except json.JSONDecodeError:
                previous_last_seen = []

        if last_seen == previous_last_seen:
            print("No new slots found.")
            continue

        await context.bot.send_message(chat_id=user, text=message, parse_mode="HTML")

        with open(f"last_seen_{user}.json", "w") as f:
            json.dump(last_seen, f)

        # if filtered_data:
            # message = "Available slots:\n\n"
            # for slot in filtered_data:
            #     message += f"{slot['date']} {slot['time']} - {slot['place']}\n"
            # await context.bot.send_message(chat_id=user, text=message)

def main():
    application = ApplicationBuilder().token(token).build()

    application.add_handler(CommandHandler('start', start))

    application.job_queue.run_repeating(recheck_site, interval=900)
    application.job_queue.run_once(recheck_site, when=0)

    application.run_polling()


if __name__ == '__main__':
    main()