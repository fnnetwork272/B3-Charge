import aiohttp
import asyncio
import re
import random
import string
import os
import json
import logging
from datetime import datetime
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler
)
from colorama import Fore, init
from functools import wraps
from pymongo import MongoClient
from dateutil.relativedelta import relativedelta
import dateutil.parser

# Initialize colorama and logging
init()
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class AdvancedCardChecker:
    def __init__(self):
        # Database setup
        self.mongo_client = MongoClient('mongodb+srv://ElectraOp:BGMI272@cluster0.1jmwb.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')  # Update connection string as needed
        self.db = self.mongo_client['stripe_checker']
        self.users_col = self.db['users']
        self.keys_col = self.db['keys']

        # Admin configuration
        self.admin_id = 7593550190
        self.admin_username = "FNxElectra"
        self.bot_username = None
        self.active_tasks = {}
        self.user_stats = {}
        self.proxy_pool = []
        self.load_proxies()
        self.request_timeout = aiohttp.ClientTimeout(total=45)
        self.max_concurrent = 5
        self.stripe_key = "pk_live_51JwIw6IfdFOYHYTxyOQAJTIntTD1bXoGPj6AEgpjseuevvARIivCjiYRK9nUYI1Aq63TQQ7KN1uJBUNYtIsRBpBM0054aOOMJN"
        self.bin_cache = {}

    def create_banner(self):
        """Create a dynamic banner with system information."""
        return f"""
{Fore.CYAN}
╔══════════════════════════════════════════════════════════════╗
║ 🔥 Cc CHECKER BOT                                            ║
╠══════════════════════════════════════════════════════════════╣
║ ➤ Admin ID: {self.admin_id:<15}                             ║
║ ➤ Bot Username: @{self.bot_username or 'Initializing...':<20}║
║ ➤ Admin Contact: https://t.me/{self.admin_username:<15}      ║
╚══════════════════════════════════════════════════════════════╝
{Fore.YELLOW}
✅ System Ready
{Fore.RESET}
"""

    async def post_init(self, application: Application):
        """Initialize bot properties after startup"""
        self.bot_username = application.bot.username
        print(self.create_banner())

    def load_proxies(self):
        if os.path.exists('proxies.txt'):
            with open('proxies.txt', 'r') as f:
                self.proxy_pool = [line.strip() for line in f if line.strip()]

    async def is_user_allowed(self, user_id):
        """Check if user has active subscription"""
        user = self.users_col.find_one({'user_id': str(user_id)})
        if user and user.get('expires_at', datetime.now()) > datetime.now():
            return True
        return user_id == self.admin_id

    class AdvancedCardChecker:
    def __init__(self):
    @staticmethod
    def check_subscription(func):
        @wraps(func)
        async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
            user_id = update.effective_user.id
            if not await self.is_user_allowed(user_id):
                await update.message.reply_text(
                    "⛔ Subscription expired or invalid!\n"
                    f"Purchase a key with /redeem <key> or contact admin: https://t.me/{self.admin_username}"
                )
                return
            return await func(self, update, context)
        return wrapper

    async def send_admin_notification(self, user):
        keyboard = [
            [InlineKeyboardButton(f"✅ Allow {user.id}", callback_data=f'allow_{user.id}'),
             InlineKeyboardButton(f"❌ Deny {user.id}", callback_data=f'deny_{user.id}')]
        ]
        message = (
            f"⚠️ New User Request:\n\n"
            f"👤 Name: {user.full_name}\n"
            f"🆔 ID: {user.id}\n"
            f"📧 Username: @{user.username if user.username else 'N/A'}\n\n"
            f"Click buttons below to approve/reject:"
        )
        try:
            await self.application.bot.send_message(
                chat_id=self.admin_id,
                text=message,
                reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception as e:
            logger.error(f"Failed to send admin notification: {e}")

    class AdvancedCardChecker:
    def __init__(self):
    @check_subscription
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        keyboard = [
            [InlineKeyboardButton("📁 Upload Combo", callback_data='upload'),
             InlineKeyboardButton("🛑 Cancel Check", callback_data='cancel')],
            [InlineKeyboardButton("📊 Live Stats", callback_data='stats'),
             InlineKeyboardButton("❓ Help", callback_data='help')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "🔥 Welcome to Advanced Card Checker Bot!\n\n"
            "📁 Send combo file or use buttons below:",
            reply_markup=reply_markup
        )

    async def handle_admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if user.id != self.admin_id:
            await update.message.reply_text("⛔ Command restricted to admin only!")
            return

        command = update.message.text.split()
        if len(command) < 2:
            await update.message.reply_text("❌ Usage: /allow <user_id> or /deny <user_id>")
            return

        action = command[0][1:]
        target_user = command[1]

        if action == 'allow':
            self.users_col.update_one(
                {'user_id': target_user},
                {'$set': {'expires_at': datetime.now() + relativedelta(days=30)}},
                upsert=True
            )
            await update.message.reply_text(f"✅ User {target_user} approved!")
        elif action == 'deny':
            self.users_col.delete_one({'user_id': target_user})
            await update.message.reply_text(f"❌ User {target_user} removed!")

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        if query.data.startswith('allow_'):
            user_id = query.data.split('_')[1]
            self.users_col.update_one(
                {'user_id': user_id},
                {'$set': {'expires_at': datetime.now() + relativedelta(days=30)}},
                upsert=True
            )
            await query.edit_message_text(f"✅ User {user_id} approved!")
            await self.application.bot.send_message(
                chat_id=int(user_id),
                text="🎉 Your access has been approved!\n"
                     "Use /start to begin checking cards."
            )
            
        elif query.data.startswith('deny_'):
            user_id = query.data.split('_')[1]
            self.users_col.delete_one({'user_id': user_id})
            await query.edit_message_text(f"❌ User {user_id} denied!")
            
        elif query.data == 'upload':
            if await self.is_user_allowed(query.from_user.id):
                await query.message.reply_text("📤 Please upload your combo file (.txt)")
            else:
                await query.message.reply_text("⛔ You are not authorized!")
                
        elif query.data == 'stats':
            await self.show_stats(update, context)
        elif query.data == 'help':
            await self.show_help(update, context)
        elif query.data == 'cancel':
            await self.stop_command(update, context)

    @check_subscription
    async def broadcast_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if user.id != self.admin_id:
            await update.message.reply_text("⛔ Admin only command!")
            return
        
        message = ' '.join(context.args)
        if not message:
            await update.message.reply_text("Usage: /broadcast Your message here")
            return
        
        users = self.users_col.find()
        success = 0
        failed = 0
        for user in users:
            try:
                await self.application.bot.send_message(
                    chat_id=int(user['user_id']),
                    text=f"📢 Admin Broadcast:\n\n{message}"
                )
                success += 1
            except:
                failed += 1
        await update.message.reply_text(f"Broadcast complete:\n✅ Success: {success}\n❌ Failed: {failed}")

    async def genkey_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if user.id != self.admin_id:
            await update.message.reply_text("⛔ Admin only command!")
            return
        
        if len(context.args) != 1:
            await update.message.reply_text("Usage: /genkey <duration>\nDurations: 1d, 7d, 1m")
            return
        
        duration = context.args[0].lower()
        key_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=3))
        key_code = ''.join(random.choices(string.digits, k=2))
        key = f"FN-CHECKER-{key_id}-{key_code}"
        
        delta = self.parse_duration(duration)
        if not delta:
            await update.message.reply_text("Invalid duration! Use 1d, 7d, or 1m")
            return
        
        self.keys_col.insert_one({
            'key': key,
            'duration_days': delta.days,
            'used': False,
            'created_at': datetime.now()
        })
        
        await update.message.reply_text(f"🔑 New key generated:\n`{key}`\nDuration: {delta.days} days")

    def parse_duration(self, duration):
        if duration.endswith('d'):
            days = int(duration[:-1])
            return relativedelta(days=days)
        if duration.endswith('m'):
            months = int(duration[:-1])
            return relativedelta(months=months)
        return None

    async def redeem_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if not context.args:
            await update.message.reply_text("Usage: /redeem <key>")
            return
        
        key = context.args[0].upper()
        key_data = self.keys_col.find_one({'key': key, 'used': False})
        
        if not key_data:
            await update.message.reply_text("❌ Invalid or expired key!")
            return
        
        expires_at = datetime.now() + relativedelta(days=key_data['duration_days'])
        self.users_col.update_one(
            {'user_id': str(user.id)},
            {'$set': {
                'user_id': str(user.id),
                'username': user.username,
                'full_name': user.full_name,
                'expires_at': expires_at
            }},
            upsert=True
        )
        
        self.keys_col.update_one({'key': key}, {'$set': {'used': True}})
        await update.message.reply_text(
            f"🎉 Subscription activated until {expires_at.strftime('%Y-%m-%d')}!"
        )

    # ... (Keep all existing methods below unchanged except for start command which is modified above)
    # [Rest of the original class methods remain unchanged]
    # [Make sure to maintain all existing methods like process_combos, chk_command, etc.]

def main():
    checker = AdvancedCardChecker()
    application = Application.builder().token("7737411241:AAEmBxOM2n7sXWOmid5u3CHqxD0EHvSkw9E").post_init(checker.post_init).build()
    checker.application = application
    
    handlers = [
        CommandHandler('start', checker.start),
        CommandHandler('allow', checker.handle_admin_command),
        CommandHandler('deny', checker.handle_admin_command),
        CommandHandler('stop', checker.stop_command),
        CommandHandler('stats', checker.show_stats),
        CommandHandler('help', checker.show_help),
        CommandHandler('chk', checker.chk_command),
        CommandHandler('broadcast', checker.broadcast_command),
        CommandHandler('genkey', checker.genkey_command),
        CommandHandler('redeem', checker.redeem_command),
        MessageHandler(filters.Document.TXT, checker.handle_file),
        CallbackQueryHandler(checker.button_handler)
    ]
    
    for handler in handlers:
        application.add_handler(handler)
    
    application.add_error_handler(checker.error_handler)
    application.run_polling()

if __name__ == "__main__":
    main()