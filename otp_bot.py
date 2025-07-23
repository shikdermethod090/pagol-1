
import os
import time
import re
import requests
import hashlib
from bs4 import BeautifulSoup
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
LOGIN_URL = os.getenv("LOGIN_URL")
SMS_URL = os.getenv("SMS_URL")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
MESSAGE_SELECTOR = os.getenv("MESSAGE_SELECTOR", "div.sms-msg-content")

session_active = False
sent_hashes = set()

def send_to_telegram(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print("Telegram error:", e)

def solve_captcha(question):
    match = re.search(r'(\d+)\s*\+\s*(\d+)', question)
    if match:
        return str(int(match.group(1)) + int(match.group(2)))
    return ""

def login(driver):
    global session_active
    driver.get(LOGIN_URL)
    time.sleep(3)

    try:
        driver.find_element(By.NAME, "username").send_keys(USERNAME)
        driver.find_element(By.NAME, "password").send_keys(PASSWORD)

        question = driver.find_element(By.XPATH, "//label[contains(text(),'What is')]").text
        answer = solve_captcha(question)
        driver.find_element(By.NAME, "captcha").send_keys(answer)

        driver.find_element(By.XPATH, "//button[contains(text(),'Login')]").click()
        time.sleep(4)

        if SMS_URL in driver.current_url:
            session_active = True
            send_to_telegram("✅ OTP BOT IS RUNNING")
            send_to_telegram("✅ Login successful")
            return True
        else:
            send_to_telegram("⚠️ Login failed")
            return False
    except Exception as e:
        send_to_telegram(f"⚠️ Error during login: {str(e)}")
        return False

def extract_messages(driver):
    global sent_hashes
    driver.get(SMS_URL)
    time.sleep(3)
    try:
        messages = driver.find_elements(By.CSS_SELECTOR, MESSAGE_SELECTOR)
        for msg_elem in messages:
            msg = msg_elem.text.strip()
            msg_hash = hashlib.sha256(msg.encode()).hexdigest()
            if msg_hash not in sent_hashes:
                sent_hashes.add(msg_hash)
                format_and_send(msg)
    except Exception as e:
        send_to_telegram(f"⚠️ Error reading messages: {str(e)}")

def format_and_send(msg):
    otp_match = re.search(r'(\d{3}[\-\s]?\d{3})', msg)
    otp = otp_match.group(1).replace(" ", "") if otp_match else "N/A"
    number = "Unknown"

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"""🚨 New WhatsApp OTP Received Successfully

📅 Date: {now}
🌍 Country: 🇷🇺 Russia
📞 Number: {number}
📱 App/Sender: WhatsApp
🔑 OTP: {otp}

📬 Full Message : {msg}

🤖 BOT MAKER BY : @MR_OWNER_057"""
    send_to_telegram(formatted)

def main():
    global session_active
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.binary_location = "/usr/bin/chromium"

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    if login(driver):
        while True:
            extract_messages(driver)
            time.sleep(20)
    else:
        send_to_telegram("❌ BOT EXITED")

if __name__ == "__main__":
    main()
