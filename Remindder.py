import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from apscheduler.schedulers.asyncio_helper import AsyncIOScheduler

from apscheduler.schedulers.background import BackgroundScheduler
import datetime
from telegram.error import TimedOut

BOT_TOKEN = "7901050539:AAF_tvFG_I-jS80TqHt3iEMkh66LQu9_0nA"


scheduler = AsyncIOScheduler()

reminders = {}


async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "Hello! I can remind you of tasks on a specific date and time.\n\n"
        "Use the command:\n"
        "`/remind YYYY-MM-DD HH:MM Task Message`\n\n"
        "Example:\n"
        "`/remind 2025-02-10 14:30 Attend meeting`\n\n"
        "Use `/view` to view all scheduled reminders."
    )


async def set_reminder(update: Update, context: CallbackContext) -> None:
    try:
        args = context.args
        if len(args) < 3:
            await update.message.reply_text("Usage: /remind YYYY-MM-DD HH:MM Task Message")
            return

        date_str = args[0]
        time_str = args[1]
        message = " ".join(args[2:])
        chat_id = update.message.chat_id

        reminder_datetime = datetime.datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")

        if reminder_datetime < datetime.datetime.now():
            await update.message.reply_text("❌ The time you entered is in the past. Please enter a future date & time.")
            return

        # Schedule the reminder as an async job
        job = scheduler.add_job(send_reminder, 'date', run_date=reminder_datetime, args=[chat_id, message, context])

        reminders[job.id] = (chat_id, message, reminder_datetime)

        await update.message.reply_text(f"✅ Reminder set for {date_str} at {time_str}: {message}")

    except ValueError:
        await update.message.reply_text("❌ Invalid format. Use: /remind YYYY-MM-DD HH:MM Task Message")


# This function will be triggered when the scheduled time arrives
async def send_reminder(chat_id, message, context: CallbackContext):
    try:
        await context.bot.send_message(chat_id=chat_id, text=f"🔔 Reminder: {message}")
    except TimedOut:
        print("Telegram request timed out")


async def view_reminders(update: Update, context: CallbackContext) -> None:
    if not reminders:
        await update.message.reply_text("No reminders set.")
        return

    reminders_list = "Scheduled Reminders:\n"
    for reminder in reminders.values():
        reminders_list += f"{reminder[2].strftime('%Y-%m-%d %H:%M')}: {reminder[1]}\n"

    await update.message.reply_text(reminders_list)


def main():
    # Ensure there is an event loop running, else create one
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:  # No running loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # Initialize the bot with the event loop
    app = Application.builder().token(BOT_TOKEN).build()

    # Start the scheduler in the event loop
    scheduler.start()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("remind", set_reminder))
    app.add_handler(CommandHandler("view", view_reminders))

    print("Bot is running...")
    loop.run_until_complete(app.run_polling(timeout=60))  # Run polling in the event loop


if __name__ == "__main__":
    main()
