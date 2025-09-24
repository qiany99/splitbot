import os
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, ConversationHandler, filters
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

# Dictionary to store group expenses temporarily
group_expenses = {}

# Sends an introductory message to user when input /start
async def start(update, context):
    await update.message.reply_text(
        "Hello! I am The Split Bot! I am here to manage your group expenses.\n"
        "Use /add to add a new expense.\n" 
        "Use /help to see what else I can do!"
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
    
    await update.message.reply_text("Who paid for the expense:")
    return PAID_BY

# Handler to add the user who paid
async def add_payer(update, context):
    context.user_data['payer'] = update.message.text
    await update.message.reply_text("Who should the expense be split between:")
    return SHARED_WITH

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
    
    # Create list for this group if it doesn't exist
    if chat_id not in group_expenses:
        group_expenses[chat_id] = []
    
    # Store the expense in the group's expense list
    group_expenses[chat_id].append(expense)

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
    
    if chat_id not in group_expenses or not group_expenses[chat_id]:
        await update.message.reply_text("No expenses found for this group yet!")
        return
    
    message = "💰 Group Expenses:\n\n"
    for i, expense in enumerate(group_expenses[chat_id], 1):
        message += f"{i}. {expense['name']} - ${expense['amount']}\n"
        message += f"   Type: {expense['type']}\n"
        message += f"   Paid by: {expense['paid_by']}\n"
        message += f"   Split between: {expense['shared_with']}\n\n"
    
    await update.message.reply_text(message)

def main():
    app = Application.builder().token(TOKEN).build()
   
    # ConversationHandler for /add
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('add', add_start)],
        states={
            TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_type)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_name)],
            AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_amount)],
            PAID_BY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_payer)],
            SHARED_WITH: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_user)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    # Add Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", list_expenses))
    app.add_handler(conv_handler)

    # Run the bot
    app.run_polling()

if __name__ == "__main__":
    main()