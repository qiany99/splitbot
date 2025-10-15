import os
import sqlite3
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ConversationHandler, filters, CallbackQueryHandler
from dotenv import load_dotenv

load_dotenv("token.env")
TOKEN = os.getenv("BOT_TOKEN")

# Conversation states
TYPE, NAME, AMOUNT, PAID_BY, SHARED_WITH = range(5)

# Fixed categories for type of expenses
TYPE_CATEGORIES = [
    ["🏠 Accommodation", "🎯 Activities & Entertainment"],
    ["📱 Communication & Connectivity", "🍕 Food & Drinks"],
    ["🏥 Health & Safety", "🛍️ Shopping & Souvenirs"],
    ["🚗 Transportation", "🔄 Others"]
]

# Get all registered users for a specific chat
def get_registered_users(chat_id):
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, name, username FROM users WHERE chat_id = ?', (chat_id,))
    users = cursor.fetchall()
    
    conn.close()
    
    return users

# Initialize SQLite database
def setup_database():
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    
    # Create table to store expenses
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            type TEXT,
            name TEXT,
            amount REAL,
            paid_by INTEGER,
            shared_with TEXT
        )
    ''')

     # Create table to store users
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        user_id INTEGER,
        name TEXT,
        username TEXT
    )
''')

    conn.commit()
    conn.close()

# Sends an introductory message to user when input /start
async def start(update, context):
    chat_id = update.message.chat.id
    user_id = update.effective_user.id
    name = update.effective_user.first_name
    username = update.effective_user.username  # Could be None if they don't have one
    
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE chat_id = ? AND user_id = ?', (chat_id, user_id))
    existing_user = cursor.fetchone()
    
    if not existing_user:
        cursor.execute('INSERT INTO users (chat_id, user_id, name, username) VALUES (?, ?, ?, ?)', 
                      (chat_id, user_id, name, username))
        conn.commit()
        welcome_msg = f"Welcome {name}! You've been registered."
    else:
        welcome_msg = f"Welcome back {name}!"
    
    conn.close()
    
    await update.message.reply_text(
        f"{welcome_msg}\n\n"
        "Use /add to add a new expense.\n" 
        "Use /list to see all expenses.\n"
        "Use /help to see what else I can do!\n\n"
        "⚠️ IMPORTANT: Make sure ALL group members type /start to register before adding expenses!"
    )
# Handler for /add command to start adding an expense    
async def add_start(update, context):
    reply_markup = ReplyKeyboardMarkup(TYPE_CATEGORIES, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "Select the type of expense:",
        reply_markup=reply_markup
    )
    return TYPE

# Handler to add the type of expense
async def add_type(update, context):

    context.user_data['type'] = update.message.text
    await update.message.reply_text(
        "Enter the name/description of the expense:",
        reply_markup=ReplyKeyboardRemove()
    )
    return NAME

# Handler to add the name/description of the expense
async def add_name(update, context):

    context.user_data['name'] = update.message.text
    await update.message.reply_text("Enter the amount spent:")
    return AMOUNT

# Handler to add the amount spent
async def add_amount(update, context):
    try:
        context.user_data['amount'] = float(update.message.text)
    except ValueError:
        await update.message.reply_text("Please enter a valid number for the amount:")
        return AMOUNT
    
    chat_id = update.message.chat.id
    users = get_registered_users(chat_id)
    
    if not users:
        await update.message.reply_text(
            "⚠️ No registered users found!\n"
            "Please make sure all group members type /start first."
        )
        return ConversationHandler.END

    # Create inline button for each user
    keyboard = []
    for user in users:
        user_id = user[0]
        name = user[1]
        username = user[2]
    
    # Format display name
    if username:
        display_text = f"{name} (@{username})"
    else:
        display_text = name
    
    # Create inline button with user_id in callback_data
    button = InlineKeyboardButton(display_text, callback_data=f"payer_{user_id}")
    keyboard.append([button])

    reply_markup = InlineKeyboardMarkup(keyboard)  

    await update.message.reply_text("Who paid for the expense:", reply_markup=reply_markup)
    
    return ConversationHandler.END

async def handle_split_selection(update, context):
    """Handle inline button clicks for selecting who to split with"""
    query = update.callback_query
    await query.answer()  # Acknowledge the button click
    
    # Check if "Done" button was clicked
    if query.data == "split_done":
        # Handle "Done" - we'll add this logic later
        await query.edit_message_text("Processing...")
        return
    
    # Check if "who paid" button was clicked
    if query.data.startswith("payer_"):
        # Extract user_id from callback_data
        user_id = int(query.data.replace("payer_", ""))
        
        # Store the user_id
        context.user_data['payer'] = user_id
        
        # Initialize empty list for split selections
        context.user_data['selected_users'] = []
        
        # Get all users to show split selection
        chat_id = query.message.chat.id
        users = get_registered_users(chat_id)
        
        # Create keyboard with checkboxes
        keyboard = []
        for user in users:
            user_id_loop = user[0]
            name = user[1]
            username = user[2]
            
            # Format display text
            if username:
                display_text = f"☐ {name} (@{username})"
            else:
                display_text = f"☐ {name}"
            
            button = InlineKeyboardButton(display_text, callback_data=f"split_{user_id_loop}")
            keyboard.append([button])
        
        # Add Done button
        done_button = InlineKeyboardButton("✅ Done", callback_data="split_done")
        keyboard.append([done_button])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Update the message to show split selection
        await query.edit_message_text(
            "✅ Payer selected!\n\n"
            "Select who should split this expense (tap to toggle):",
            reply_markup=reply_markup
        )
        return
    
    # If not "Done", it must be a user selection button; Extract user_id from callback_data (format: "split_456789")
    user_id = int(query.data.replace("split_", ""))

    # Toggle user selection
    if user_id in context.user_data['selected_users']:
        # Already selected → Remove it (unselect)
        context.user_data['selected_users'].remove(user_id)
    else:
        # Not selected → Add it (select)
        context.user_data['selected_users'].append(user_id)

    # Rebuild the keyboard with updated checkboxes
    chat_id = query.message.chat.id
    users = get_registered_users(chat_id)
    
    keyboard = []
    for user in users:
        user_id_loop = user[0]
        name = user[1]
        username = user[2]
        
        # Check if this user is selected
        if user_id_loop in context.user_data['selected_users']:
            checkbox = "☑"  # Checked
        else:
            checkbox = "☐"  # Unchecked
        
        # Format display text with appropriate checkbox
        if username:
            display_text = f"{checkbox} {name} (@{username})"
        else:
            display_text = f"{checkbox} {name}"
        
        button = InlineKeyboardButton(display_text, callback_data=f"split_{user_id_loop}")
        keyboard.append([button])

    # Add Done button back
    done_button = InlineKeyboardButton("✅ Done", callback_data="split_done")
    keyboard.append([done_button])

    # Update the message with new keyboard
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_reply_markup(reply_markup=reply_markup)

# Handler to add the users who shared the expense
async def add_user(update, context):
    context.user_data['users'] = update.message.text
    
    # Storing the expense in a dictionary
    expense = {
        'type': context.user_data['type'],
        'name': context.user_data['name'],
        'amount': context.user_data['amount'],
        'paid_by': context.user_data['payer'],
        'shared_with': context.user_data['users'],
    }

    # Get the chat ID (each group has unique ID)
    chat_id = update.message.chat.id
    
    # Store the expense in SQLite database
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO expenses (chat_id, type, name, amount, paid_by, shared_with)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (chat_id, expense['type'], expense['name'], expense['amount'],expense['paid_by'], expense['shared_with']))

    conn.commit()
    conn.close()

    await update.message.reply_text(
        f"Expense added!\n"
        f"Type: {expense['type']}\n"
        f"Name: {expense['name']}\n"
        f"Amount: {expense['amount']}\n"
        f"Paid By: {expense['paid_by']}\n"
        f"Split between: {expense['shared_with']}"
    )
    return ConversationHandler.END
    
# Handler to cancel the conversation
async def cancel(update, context):
    await update.message.reply_text("Expense addition cancelled.")
    return ConversationHandler.END

# Handler to list all expenses in the group
async def list_expenses(update, context):
    chat_id = update.message.chat.id
    
    # Connect to database and get expenses for this chat
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM expenses WHERE chat_id = ?', (chat_id,))
    expenses = cursor.fetchall()
    
    conn.close()
    
    # Check if no expenses found
    if not expenses:
        await update.message.reply_text("No expenses found for this group yet!")
        return
    
    # Build the message from database results
    message = "💰 Group Expenses:\n\n"
    for i, expense in enumerate(expenses, 1):
        # expense is a tuple: (id, chat_id, type, name, amount, paid_by, shared_with)
        message += f"{i}. {expense[3]} - ${expense[4]}\n"        # name - amount
        message += f"   Type: {expense[2]}\n"                    # type
        message += f"   Paid by: {expense[5]}\n"                 # paid_by
        message += f"   Split between: {expense[6]}\n\n"         # shared_with
    await update.message.reply_text(message)

def main():
    setup_database()
    app = Application.builder().token(TOKEN).build()
   
    # ConversationHandler for /add
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('add', add_start)],
        states={
            TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_type)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_name)],
            AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_amount)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    # Add Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", list_expenses))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(handle_split_selection))


    # Run the bot
    app.run_polling()

if __name__ == "__main__":
    main()