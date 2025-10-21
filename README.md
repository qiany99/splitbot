# 💰 SplitBot - Your Smart Expense Tracker
> A Telegram bot that helps you split bills and track expenses with your friends and groups effortlessly!

## Video Demo:  <URL HERE>

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
2. **Start the bot:** Send `/start`
3. **Add to a group:** Invite the bot to your group chat
4. **Register members:** All group members must send `/start`
5. **Start tracking:** Use `/add` to log expenses!

---

### Commands
| Command | Description |
|---------|-------------|
| `/start` | Register and see available commands |
| `/add` | Add a new expense |
| `/list` | View all recorded expenses |
| `/balance` | Check who owes what |
| `/settle` | Mark expenses as settled |
| `/mybreakdown` | View your personal spending by category |
| `/groupbreakdown` | View group spending by category |
| `/cancel` | Cancel current operation |

---

## 💡 Usage Examples

### Adding an Expense

```
1. Send /add
2. Enter amount: 50
3. Enter description: Dinner at Italian restaurant
4. Choose category: Food
5. Select who paid
6. Select who should split the bill
7. Done! ✅
```

### Checking Balance

```
Send /balance to see:
• Who owes you money
• Who you owe money to
• Total amounts
```

### Viewing Breakdowns

```
/mybreakdown - See your spending patterns
/groupbreakdown - See group spending trends
```

---

## 📁 Project Structure

Here's what each file in the project does:

### Core Files

| File | Description |
|------|-------------|
| `bot.py` | Main bot application containing all command handlers, conversation flows, and business logic for expense tracking and splitting |
| `requirements.txt` | Lists all Python package dependencies needed to run the bot (python-telegram-bot, python-dotenv) |
| `runtime.txt` | Specifies the Python version (3.12.0) for deployment platforms like Render and Railway |
| `.env` | Stores sensitive environment variables like `BOT_TOKEN` (⚠️ **never committed to Git**) |
| `.gitignore` | Tells Git which files to ignore (database files, virtual environment, secrets) |
| `README.md` | This file! Project documentation and setup instructions |

### Generated Files (Not in Repository)

| File | Description |
|------|-------------|
| `expenses.db` | SQLite database file that stores all expenses and user data (created automatically when bot runs) |
| `venv/` | Virtual environment folder containing isolated Python packages (created by you during setup) |

### bot.py - Main Application

The `bot.py` file contains:

- **Database Setup:** `setup_database()` function that creates SQLite tables
- **Command Handlers:** Functions for `/start`, `/add`, `/list`, `/balance`, `/settle`, etc.
- **Conversation Handlers:** Multi-step conversations for adding expenses
- **Business Logic:** Calculations for splitting bills and tracking balances
- **User Management:** Registration and tracking of group members
- **Main Entry Point:** `main()` function that starts the bot

### requirements.txt - Dependencies

```txt
python-telegram-bot==21.6  # Telegram Bot API wrapper
python-dotenv==1.0.0       # Environment variable management
```

### runtime.txt - Python Version

```txt
python-3.12.0  # Ensures deployment platforms use correct Python version
```

### .env - Environment Variables

```bash
BOT_TOKEN=your_bot_token_here  # Your Telegram bot token from @BotFather
```

> ⚠️ **Important:** This file should **NEVER** be committed to Git! It's listed in `.gitignore` to prevent accidental exposure of your bot token.

### .gitignore - Ignored Files

```bash
# Environment variables
.env

# Database files
*.db
*.sqlite
*.sqlite3

# Python cache
__pycache__/
*.pyc
*.pyo

# Virtual environment
venv/
env/

# OS files
.DS_Store
```

---

## 🌐 Deployment

### Deploy on Railway (Recommended - Free!)

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

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Amazing bot framework
- [Railway](https://railway.app) - Easy and free hosting
- All contributors and users who make this project better! ❤️
