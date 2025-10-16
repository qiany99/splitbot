import json
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

# Validate that group has users and expenses. Returns error message or None if valid.
def validate_group_data(chat_id):
    
    # Check if users are registered
    users = get_registered_users(chat_id)
    if not users:
        return "⚠️ No registered users found!\n Please make sure all group members type /start first."
    
    # Check if expenses exist
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM expenses WHERE chat_id = ?', (chat_id,))
    count = cursor.fetchone()[0]
    conn.close()
    
    if count == 0:
        return "No expenses found for this group yet!"
    
    return None

#Calculate balances for all users in a group. Returns (user_balances, creditors, debtors)
def calculate_balances(chat_id):

    # Get expenses
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    cursor.execute('SELECT amount, paid_by, shared_with FROM expenses WHERE chat_id = ?', (chat_id,))
    expenses = cursor.fetchall()
    conn.close()
       
    # Get users
    users = get_registered_users(chat_id)
    
    user_balances = []  # List of (display_name, balance)
    creditors = []
    debtors = []
    
    # Calculate balance for each user
    for user in users:
        user_id = user[0]
        name = user[1]
        username = user[2]
        
        # Format display name
        if username:
            display_name = f"{name} (@{username})"
        else:
            display_name = name
        
        # Calculate balance
        money_owe = 0
        money_owed = 0
        
        for expense in expenses:
            amount = expense[0]
            if expense[1] == user_id:
                money_owed += amount
            
            shared_with = json.loads(expense[2])
            if user_id in shared_with:
                split_amount = amount / len(shared_with)
                money_owe += split_amount
        
        balance = money_owed - money_owe
        
        # Store in all lists
        user_balances.append((display_name, balance))
        
        if balance > 0:
            creditors.append((display_name, balance))
        elif balance < 0:
            debtors.append((display_name, abs(balance)))
    
    return user_balances, creditors, debtors

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
        "📝 Available commands 📝\n"
        "• /add - Add a new expense\n" 
        "• /list - See all expenses\n"
        "• /balance - See who owes what\n"
        "• /settle - Settle up expenses\n"
        "• /mybreakdown - View personal spending by category\n"
        "• /groupbreakdown - View group spending by category\n\n"
        "⚠️ IMPORTANT: Make sure ALL group members type /start to register! ⚠️"
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
            "⚠️ No registered users found! ⚠️\n"
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

#Handle inline button clicks for selecting who to split with
async def handle_split_selection(update, context):
    query = update.callback_query
    await query.answer()  # Acknowledge the button click
    
    # Check if "Done" button was clicked
    if query.data == "split_done":
        
        # Validate that at least one user was selected
        if not context.user_data['selected_users']:
            await query.answer("⚠️ Please select at least one person! ⚠️", show_alert=True)
            return
    
        # Get the stored data
        chat_id = query.message.chat.id
        expense_type = context.user_data['type']
        expense_name = context.user_data['name']
        amount = context.user_data['amount']
        payer_id = context.user_data['payer']
        selected_user_ids = context.user_data['selected_users']
    
        # Convert selected_user_ids list to JSON string
        shared_with_json = json.dumps(selected_user_ids)

        # Get payer name from database
        payer_user = None
        shared_users = []

        # Fetch all users to get names
        users = get_registered_users(chat_id)
    
        for user in users:
            user_id = user[0]
            name = user[1]
            username = user[2]
        
            # Format display name
            if username:
                display_name = f"{name} (@{username})"
            else:
                display_name = name
        
            # Check if this is the payer
            if user_id == payer_id:
                payer_user = display_name
        
            # Check if this user is in shared list
            if user_id in selected_user_ids:
                shared_users.append(display_name)
        
        # Seeking for confirmation message
        confirmation = (
            f"❗️❗️Please confirm the expense details❗️❗️\n\n"
            f"• Type: {expense_type}\n"
            f"• Name: {expense_name}\n"
            f"• Amount: ${amount}\n"
            f"• Paid by: {payer_user}\n"
            f"• Split between: {', '.join(shared_users)}"
        )
        
        keyboard = []
        confirm_button = InlineKeyboardButton("✅ Confirm & Save", callback_data="confirm")
        keyboard.append([confirm_button])
        cancel_button = InlineKeyboardButton("❌ Cancel", callback_data="cancel")
        keyboard.append([cancel_button]) 
        reply_markup= InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(confirmation, reply_markup=reply_markup)
        return
    
    if query.data == "cancel":
        await query.edit_message_text("❌ Expense cancelled. Not saved.")
        return ConversationHandler.END

    if query.data == "confirm":
        
        # Get the stored data
        chat_id = query.message.chat.id
        expense_type = context.user_data['type']
        expense_name = context.user_data['name']
        amount = context.user_data['amount']
        payer_id = context.user_data['payer']
        selected_user_ids = context.user_data['selected_users']
    
        # Convert selected_user_ids list to JSON string
        shared_with_json = json.dumps(selected_user_ids)

        # Get payer name from database
        payer_user = "Unknown"
        shared_users = []

        # Fetch all users to get names
        users = get_registered_users(chat_id)
    
        for user in users:
            user_id = user[0]
            name = user[1]
            username = user[2]
        
            # Format display name
            if username:
                display_name = f"{name} (@{username})"
            else:
                display_name = name
        
            # Check if this is the payer
            if user_id == payer_id:
                payer_user = display_name
        
            # Check if this user is in shared list
            if user_id in selected_user_ids:
                shared_users.append(display_name)

        # Acknowledgement message
        acknowledgement = (
            f"✅ Expense saved!\n\n"
            f"📋 Summary 📋\n"
            f"• Type: {expense_type}\n"
            f"• Name: {expense_name}\n"
            f"• Amount: ${amount}\n"
            f"• Paid by: {payer_user}\n"
            f"• Split between: {', '.join(shared_users)}"
        )

        # Save to database
        conn = sqlite3.connect('expenses.db')
        cursor = conn.cursor()
    
        cursor.execute('''
            INSERT INTO expenses (chat_id, type, name, amount, paid_by, shared_with)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (chat_id, expense_type, expense_name, amount, payer_id, shared_with_json))
    
        conn.commit()
        conn.close()
    
        await query.edit_message_text(acknowledgement)
        return ConversationHandler.END
    
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

# Handler to cancel the conversation
async def cancel(update, context):
    await update.message.reply_text("Expense addition cancelled.")
    return ConversationHandler.END

# Handler to list all expenses in the group
async def list_expenses(update, context):
    chat_id = update.message.chat.id
    
    # Validate group data
    error_msg = validate_group_data(chat_id)
    if error_msg:
        await update.message.reply_text(error_msg)
        return

    # Connect to database and get expenses for this chat
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM expenses WHERE chat_id = ?', (chat_id,))
    expenses = cursor.fetchall() 
    conn.close()
    
    users = get_registered_users(chat_id)

    # Build the message from database results
    message = "💰 Group Expenses:\n\n"
    for i, expense in enumerate(expenses, 1):
        # expense is a tuple: (id, chat_id, type, name, amount, paid_by, shared_with)
        message += f"{i}. {expense[3]} - ${expense[4]}\n"        # name - amount
        message += f"   Type: {expense[2]}\n"                    # type

        # Get payer name from database
        payer_user = None
        shared_users = []
        # Fetch all users to get names
        for user in users:
            user_id = user[0]
            name = user[1]
            username = user[2]
            # Format display name
            if username:
                display_name = f"{name} (@{username})"
            else:
                display_name = name    
            # Check if this is the payer
            if user_id == expense[5] :
                payer_user = display_name       
            # Check if this user is in shared list
            if user_id in json.loads(expense[6]):
                shared_users.append(display_name)

        message += f"   Paid by: {payer_user}\n"    # paid_by
        message += f"   Split between: {', '.join(shared_users)}\n\n"   # shared_with

    await update.message.reply_text(message)

# Handler to balance all expenses in the group
async def balance_expenses(update, context):
    chat_id = update.message.chat.id

   # Validate group data
    error_msg = validate_group_data(chat_id)
    if error_msg:
        await update.message.reply_text(error_msg)
        return
    
    # Get calculated balances
    user_balances, creditors, debtors = calculate_balances(chat_id)
    
    # Build message
    message = "💰 Group Balances 💰\n\n"
    for display_name, balance in user_balances:
        if balance > 0:
            message += f"• {display_name} is owed ${balance:.2f}\n"
        elif balance < 0:
            message += f"• {display_name} owes ${-balance:.2f}\n"
        else:
            message += f"• {display_name} is settled up\n"
    
    await update.message.reply_text(message)

async def settle_expenses(update, context):
    chat_id = update.message.chat.id
    validate_group_data(chat_id)
    
    # Validate group data
    error_msg = validate_group_data(chat_id)
    if error_msg:
        await update.message.reply_text(error_msg)
        return

    # Get calculated balances - we only need creditors and debtors!
    user_balances, creditors, debtors = calculate_balances(chat_id)
    
    # Settlement algorithm
    settlements = []
    creditors.sort(key=lambda x: x[1], reverse=True)
    debtors.sort(key=lambda x: x[1], reverse=True)
    
    while creditors and debtors:
        creditor_name, creditor_amount = creditors[0]
        debtor_name, debtor_amount = debtors[0]
        
        transfer_amount = min(creditor_amount, debtor_amount)
        settlements.append(f"• {debtor_name} pays {creditor_name} ${transfer_amount:.2f}")
        
        creditors[0] = (creditor_name, creditor_amount - transfer_amount)
        debtors[0] = (debtor_name, debtor_amount - transfer_amount)
        
        if creditors[0][1] == 0:
            creditors.pop(0)
        if debtors[0][1] == 0:
            debtors.pop(0)
    
    # Display settlements
    if settlements:
        message = "💸 Settlement Plan 💸\n\n" + "\n".join(settlements)
    else:
        message = "✅ Everyone is settled up!"
    
    await update.message.reply_text(message)

async def group_breakdown(update, context):
    chat_id = update.message.chat.id

     # Validate group data
    error_msg = validate_group_data(chat_id)
    if error_msg:
        await update.message.reply_text(error_msg)
        return
    
    # Connect to database and get expenses for this chat
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    cursor.execute('SELECT type, SUM(amount) FROM expenses WHERE chat_id = ? GROUP BY type ORDER BY type', (chat_id,))
    expenses = cursor.fetchall() 
    conn.close()

    # Build the message from database results
    message = "💰 Group Expense Summary (By Category) 💰\n\n"
    total_spend = 0
    for expense in expenses:
        message +=f"{expense[0]}: ${expense[1]:.2f}\n"
        total_spend += expense[1]

    message += f"\n💵 Total Spent: ${total_spend:.2f}"
    
    await update.message.reply_text(message)

async def my_breakdown(update, context):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id

    # Validate group data
    error_msg = validate_group_data(chat_id)
    if error_msg:
        await update.message.reply_text(error_msg)
        return

    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, name, username FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchall()

    if not user: 
        message = "⚠️ You are not registered! ⚠️\n Please type /start to register!"
        await update.message.reply_text(message)
        return
    
    # Format display name
    name = user[0][1]
    username = user[0][2]
    # Format display name
    if username:
        display_name = f"{name} (@{username})"
    else:
        display_name = name
            
    # Connect to database and get expenses for this chat
    cursor.execute('SELECT type, amount, shared_with FROM expenses WHERE chat_id = ? ORDER BY type', (chat_id,))
    expenses = cursor.fetchall() 
    conn.close()

    # Use a dictionary to accumulate totals
    category_totals = {}

    for expense in expenses:
        expense_type = expense[0]
        amount = expense[1]
        shared_with = json.loads(expense[2])
        
        # CHECK if user is in this expense!
        if user_id in shared_with:
            split_amount = amount / len(shared_with)
            
            # Add to category total
            if expense_type in category_totals:
                category_totals[expense_type] += split_amount
            else:
                category_totals[expense_type] = split_amount

    # Print all categories
    message = f"💰 {display_name}'s Expense Summary (By Category) 💰\n\n"
    if not category_totals:
        message += "No expenses found for you yet!\n\n"
    else:
        for category, total in sorted(category_totals.items()):
            message += f"• {category}: ${total:.2f}\n"
        message += "\n"  # Add spacing before balance

    user_balances, creditors, debtors = calculate_balances(chat_id)
    
    for user_balance in user_balances:
        if user_balance[0] == display_name:
            message += f"📊 <b><u>{display_name}'s Current Balance</u></b> 📊\n"
            if user_balance[1] > 0:
                message += f"💰 You are owed ${user_balance[1]:.2f}\n\n"
            elif user_balance[1] < 0:
                message += f"💸 You owe ${-user_balance[1]:.2f}\n\n"
            elif user_balance[1] == 0:
                message += "✅ You are settled up!\n\n"
            break

    await update.message.reply_text(message, parse_mode="HTML")
    return

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
    app.add_handler(CommandHandler("balance", balance_expenses))
    app.add_handler(CommandHandler("settle", settle_expenses))
    app.add_handler(CommandHandler("groupbreakdown", group_breakdown))
    app.add_handler(CommandHandler("mybreakdown", my_breakdown))

    # Run the bot
    app.run_polling()

if __name__ == "__main__":
    main()