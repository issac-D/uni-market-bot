import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from src.config import BOT_TOKEN
# 1. ADDED delete_user_data to imports
from src.database import init_db, get_user, get_all_users, delete_user_data
from src.handlers.auth import registration_handler
from src.handlers.selling import selling_handler
from src.handlers.lost_found import lost_found_handler
from src.handlers.feedback import feedback_handler
from src.keep_alive import keep_alive
from src.handlers.admin import handle_approval, handle_sold_status

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- MENU NAVIGATION ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point: Shows the Main Menu."""
    # Updated keyboard to include Feedback
    keyboard = [
        ['🛒 Marketplace', '🔍 Lost & Found'],
        ['📝 Feedback']
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "👋 Welcome to Uni Market!\nChoose an option:", 
        reply_markup=markup
    )

async def marketplace_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows Marketplace options (Register vs Sell)."""
    user = get_user(update.effective_user.id)
    
    if user and user['is_seller']:
        # REGISTERED USER VIEW
        buttons = [['➕ Sell Item'], ['🔙 Main Menu']]
        msg = f"👤 Seller: {user['real_name']}\n📍 {user['location']}\n\nWhat would you like to do?"
    else:
        # GUEST VIEW
        buttons = [['📝 Register'], ['🔙 Main Menu']]
        msg = "🔒 Marketplace Access\nYou need to register to sell items."
        
    markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    await update.message.reply_text(msg, reply_markup=markup)

async def lost_found_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows Lost & Found options."""
    buttons = [['📢 I Lost', '🙋‍♂️ I Found'], ['🔙 Main Menu']]
    markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    await update.message.reply_text("🔍 Lost & Found Section", reply_markup=markup)

# --- ADMIN COMMANDS ---
ADMIN_IDS = [7775309813, 6112723745, 1836483387] 

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if the user is an Admin
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Access Denied: You are not an admin.")
        return

    # If allowed, show the list
    users = get_all_users()
    
    if not users:
        await update.message.reply_text("👥 Total Users: 0\n(Database is empty)")
        return

    text = f"👥 Total Users: {len(users)}\n\n"
    for u in users:
        text += f"ID: `{u['user_id']}` | {u['real_name']} | {u['phone_number']}\n"
    
    await update.message.reply_text(text)

# 2. NEW BAN COMMAND FUNCTION
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command: /ban [user_id]"""
    # Security Check
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Access Denied.")
        return

    # Get User ID from args
    try:
        if not context.args:
             await update.message.reply_text("⚠️ Usage: /ban [user_id]\nExample: /ban 123456789")
             return
        target_id = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ Invalid ID format.")
        return

    # Perform Deletion
    try:
        delete_user_data(target_id)
        await update.message.reply_text(f"✅ User `{target_id}` and all their posts have been removed.", parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"❌ Error banning user: {e}")

if __name__ == '__main__':
    keep_alive()
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # --- CALLBACK HANDLERS (Button Clicks) ---
    app.add_handler(CallbackQueryHandler(handle_approval, pattern="^(approve|reject)_"))
    app.add_handler(CallbackQueryHandler(handle_sold_status, pattern="^sold_"))

    # --- CONVERSATION HANDLERS ---
    app.add_handler(registration_handler)
    app.add_handler(selling_handler)
    app.add_handler(lost_found_handler)
    app.add_handler(feedback_handler)
    
    # --- NAVIGATION COMMANDS & TEXT FILTERS ---
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('users', list_users))
    
    # 3. REGISTER BAN COMMAND
    app.add_handler(CommandHandler('ban', ban_user))
    
    app.add_handler(MessageHandler(filters.Regex("^🛒 Marketplace$"), marketplace_menu))
    app.add_handler(MessageHandler(filters.Regex("^🔍 Lost & Found$"), lost_found_menu))
    app.add_handler(MessageHandler(filters.Regex("^🔙 Main Menu$"), start))

    print("Bot is polling...")
    app.run_polling()