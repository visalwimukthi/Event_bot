import logging
import sqlite3
import re
from telegram import Update, Bot, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Database setup
DB_FILE = "tickets.db"

def setup_database():
    """Sets up the database to store ticket information."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(''' 
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            full_name TEXT,
            email TEXT,
            tickets INTEGER,
            ticket_id TEXT
        )
    ''')
    conn.commit()
    conn.close()

# States for the conversation
NAME, EMAIL, TICKETS = range(3)

# Email validation function
def is_valid_email(email):
    """Validates the email address format."""
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None

# Bot commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command."""
    await update.message.reply_text(
        "Welcome to the Event Ticketing Bot! 🎉\n\n"
        "------------------Event Details:--------------\n"
        "Organizer: ARES_Group\n"
        "Ticket Price: Starting from LKR 2500\n"
        "Event Date and Time: December 10, 2024, at 7:00 PM\n\n"
        "Use /register to get your free ticket.\n"
        "For help, use /help."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /help command."""
    await update.message.reply_text(
        "Commands:\n"
        "/start - Start the bot and get event details\n"
        "/register - Register for the event\n"
        "/help - Get help and instructions"
    )

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /register command."""
    await update.message.reply_text("Please enter your full name:")
    return NAME

async def collect_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Collects the user's full name."""
    context.user_data['full_name'] = update.message.text
    await update.message.reply_text("Please enter your email address:")
    return EMAIL

async def collect_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Collects the user's email address and validates it."""
    email = update.message.text
    if is_valid_email(email):
        context.user_data['email'] = email
        await update.message.reply_text("How many tickets do you need? (Max: 5)")
        return TICKETS
    else:
        await update.message.reply_text("Invalid email address. Please enter a valid email address:")
        return EMAIL

async def collect_tickets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Collects the number of tickets requested."""
    try:
        tickets = int(update.message.text)
        if tickets < 1 or tickets > 5:
            raise ValueError("Invalid number of tickets")
        context.user_data['tickets'] = tickets

        # Generate a ticket ID
        ticket_id = f"TICKET-{update.effective_user.id}-{tickets}"
        context.user_data['ticket_id'] = ticket_id

        # Store data in the database
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute(''' 
            INSERT INTO tickets (user_id, username, full_name, email, tickets, ticket_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            update.effective_user.id,
            update.effective_user.username,
            context.user_data['full_name'],
            context.user_data['email'],
            tickets,
            ticket_id
        ))
        conn.commit()
        conn.close()

        # Send confirmation message
        await update.message.reply_text(
            f"Thank you, {context.user_data['full_name']}! 🎟\n\n"
            f"You have successfully registered for {tickets} ticket(s). "
            f"Your ticket ID is {ticket_id}.\n\n"
            "You will now be added to the event group."
        )

        # Add user to the group
        GROUP_CHAT_ID = 1890846699  
        bot: Bot = context.bot
        await bot.add_chat_members(chat_id=GROUP_CHAT_ID, user_ids=[update.effective_user.id])

        return ConversationHandler.END

    except ValueError:
        await update.message.reply_text("Please enter a valid number between 1 and 5.")
        return TICKETS

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancels the registration process."""
    await update.message.reply_text("Registration canceled.")
    return ConversationHandler.END

# Main function to set up the bot
def main():
    """Main function to set up the bot."""
    setup_database()  

    application = ApplicationBuilder().token("7634676316:AAFjxjLLUsdbygerFivIug2NKIvSqJwaMqI").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("register", register)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_name)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_email)],
            TICKETS: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_tickets)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(conv_handler)

    application.run_polling()

if __name__ == "__main__":
    main()
