import os
import time
import pyautogui
import pyperclip
from click import group
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from .base_bot import BaseBot
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer


class TelegramBot(BaseBot):
    def __init__(self, bot_id):
        super().__init__(bot_id)
        self.driver = None
        self.group_links = []

    async def start(self):
        self.status = "running"
        print(f"TelegramBot {self.bot_id} started")

    async def stop(self):
        self.status = "stopped"
        if self.driver:
            self.driver.quit()
        print(f"TelegramBot {self.bot_id} stopped")

    async def create_bot(self, phone_number):
        options = Options()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        options.add_argument("--disable-blink-features=AutomationControlled")

        self.driver = webdriver.Chrome(options=options)

        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        self.driver.get("https://web.telegram.org/k/")
        time.sleep(5)

        try:
            phone_input_btn = self.driver.find_element(By.CSS_SELECTOR, ".btn-primary")
            self.driver.execute_script("arguments[0].click();", phone_input_btn)
            time.sleep(2)
            phone_input = self.driver.find_element(By.CSS_SELECTOR, "#auth-pages > div.scrollable.scrollable-y.no-scrollbar > div.tabs-container.auth-pages__container > div.tabs-tab.page-sign.active > div > div.input-wrapper > div.input-field.input-field-phone > div.input-field-input")
            self.driver.execute_script("""
                var div = arguments[0];
                div.innerText = arguments[1];  // Вставляем текст
            """, phone_input, phone_number)
            time.sleep(2)
            next_btn = self.driver.find_element(By.CSS_SELECTOR, "#auth-pages > div.scrollable.scrollable-y.no-scrollbar > div.tabs-container.auth-pages__container > div.tabs-tab.page-sign.active > div > div.input-wrapper > button.btn-primary.btn-color-primary.rp")
            self.driver.execute_script("arguments[0].click();", next_btn)
            print(f"📲 Phone number: {phone_number}")
        except Exception as e:
            print(f"❌ Error while starting the authorization process: {e}")

        print("✅ Phone number entered, awaiting verification code")

    async def verify_bot(self, verification_code):
        if not self.driver:
            raise Exception("Bot is not initialized. Please create the bot first.")

        try:
            code_input = self.driver.find_element(By.CSS_SELECTOR, "#auth-pages > div.scrollable.scrollable-y.no-scrollbar > div.tabs-container.auth-pages__container > div.tabs-tab.page-authCode.active > div > div.input-wrapper > div > input")
            code_input.send_keys(verification_code)
            code_input.send_keys(Keys.RETURN)
        except Exception as e:
            print(f"❌ Verification error: {e}")

        print("✅ Verification completed")



    async def search_groups(self, keyword):
        self.group_links = ["https://web.telegram.org/k/#@rabo_kiev"]
        for group_link in self.group_links:
            try:
                self.driver.get(group_link)
                time.sleep(3)
                search_btn = self.driver.find_element(By.XPATH, "/html/body/div[2]/div/div[4]/div/div/div[2]/div[1]/div[2]/button[7]")
                self.driver.execute_script("arguments[0].click();", search_btn)
                search_input_field = self.driver.find_element(By.CSS_SELECTOR,
                                                              "#column-center > div > div > div.sidebar-header.topbar.has-avatar.is-pinned-message-shown > div.topbar-search-container > div.topbar-search-left-container > div.input-search.topbar-search-input-container > input")
                search_input_field.send_keys(keyword)
                search_input_field.send_keys(Keys.ENTER)

                time.sleep(2)
            except Exception as e:
                print(f"❌ Ошибка поиска: {e}")




    async def get_group_links(self):
        return self.group_links
