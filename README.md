# 💰 SplitBot - Your Smart Expense Tracker
> A Telegram bot that helps you split bills and track expenses with your friends and groups effortlessly!

---

## Video Demo

<URL HERE>

---

## ✨ Features

- 📊 **Track Group Expenses** - Keep tabs on all shared costs
- 💸 **Split Bills Fairly** - Automatically calculate who owes what
- 🏷️ **Categorize Spending** - Organize expenses by category (Food, Transport, etc.)
- 👥 **Multi-User Support** - Works seamlessly in group chats
- 📈 **Spending Analytics** - View personal and group breakdowns
- ⚡ **Real-time Updates** - Instant balance calculations
- 🔒 **Secure** - Your data stays private

---

## 🚀 Quick Start

### For Users

1. **Find the bot on Telegram:** Search for `@splitbot`
2. **Add to a group:** Invite the bot to your group chat
3. **Register members:** All group members must send `/start`
4. **Start tracking:** Use `/add` to log expenses!

### Commands
| Command | Description |
|---------|-------------|
| `/start` | Register and see available commands |
| `/add` | Add a new expense |
| `/list` | View all recorded expenses |
| `/balance` | See whether each member of the group owe or are owed money |
| `/settle` | See who needs to pay whom (settlement instructions) |
| `/mybreakdown` | View your personal spending by category |
| `/groupbreakdown` | View group spending by category |
| `/cancel` | Cancel current operation |

---

## 💡 Usage Examples

### Adding an axpense using /add

```
1. Enter amount: 50
2. Enter description: Dinner at Italian restaurant
3. Choose category: 🍕 Food & Drinks
4. Select who paid
5. Select who should split the bill
6. Done! ✅

```

### Checking group balances using /balance 

```
💰 Group Balances 💰

• Banana (@bananasplit) is owed $50.00 
• Grape (@grapeslush) is owes $50.00
• Apple (@applepie) is settled up

```
### Using /settle for settlement instructions

```
💸 Settlement Plan 💸

• Grape (@grapeslush) pays Banana (@bananasplit) $50.00

```

### Obtain personal spending patterns and balance using /mybreakdown 

```
💰 Apple (@applepie)'s Expense Summary (By Category) 💰

• 🏠 Accommodation: $500.00
• 🍕 Food & Drinks: $100.00
• 🚗 Transportation: $300.00
• 🛍️ Shopping & Souvenirs: $1300.00

📊 Apple (@applepie)'s Current Balance 📊

✅ You are settled up!

```
### Obtain group spending patterns using /groupbreakdown

```
💰 Group Expense Summary (By Category) 💰

• 🏠 Accommodation: $500.00
• 🍕 Food & Drinks: $100.00
• 🚗 Transportation: $300.00
• 🛍️ Shopping & Souvenirs: $1300.00

💵 Total Spent: $ 2200.00

```
---

## 📁 Project Structure

Here's what each file in the project does:

### Core Files

| File | Description |
|------|-------------|
| `bot.py` | Main bot application containing the main entry point (`main()` function that starts the bot), datbase setup (`setup_database()` function that creates SQLite tables), all command handlers (functions for `/start`, `/add`, `/list`, `/balance`, `/settle`, etc), conversation flows (multi-step conversations for adding expenses), and business logic (calculations for splitting bills and tracking balances) for expense tracking and splitting |
| `requirements.txt` | Lists all Python package dependencies needed to run the bot (python-telegram-bot, python-dotenv) |
| `runtime.txt` | Specifies the Python version (3.12.0) for deployment platforms like Render |
| `.env` | Stores sensitive environment variables like `BOT_TOKEN` which was provided by @BotFather (⚠️ **never committed to Git**) |
| `.gitignore` | Tells Git which files to ignore (database files, virtual environment, secrets) |
| `README.md` | This file! Project documentation and setup instructions |

### Generated Files (Not in Repository)

| File | Description |
|------|-------------|
| `expenses.db` | SQLite database file that stores all expenses and user data (created automatically when bot runs) |
| `venv/` | Virtual environment folder containing isolated Python packages (created by you during setup) |

---

## 🌐 Deployment

### Deployed on Railway 

1. Fork this repository
2. Sign up at [Railway.app](https://railway.app)
3. Create a new project from GitHub repo
4. Add environment variable: `BOT_TOKEN`
5. Deploy! 🚀

---

## 📊 Database Schema

### Expenses Table

```sql
CREATE TABLE expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    type TEXT,
    name TEXT NOT NULL,
    amount REAL NOT NULL,
    paid_by TEXT NOT NULL,
    shared_with TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Users Table

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    UNIQUE(chat_id, user_id)
);
```

---

## 🙏 Acknowledgments

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) 
- [Railway](https://railway.app) 
- All contributors and users who make this project better! ❤️
