from cv2 import cv2
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

import mss
import numpy as np
import telegram
import yaml


class Telegram:
    def __init__(self):
        from src.config import Config
        self.config = Config().read()
        self.enableTelegram = self.config['services']['telegram']
        self.updater = None

        if self.enableTelegram == True:
            self.telegramConfig = self.telegramConfig()
            try:
                self.updater = Updater(self.telegramConfig['botfather_token'])
                self.TelegramBot = telegram.Bot(
                    token=self.telegramConfig['botfather_token'])
            except telegram.error.InvalidToken:
                self.updater = None
                if self.enableTelegram == True:
                    print('Telegram: BotFather Token invalid or Bot not initialized.')
                    exit()
                return

    def importLibs(self):
        from src.actions import Actions
        from src.desktop import Desktop
        from src.images import Images
        from src.log import Log
        from src.recognition import Recognition
        self.actions = Actions()
        self.desktop = Desktop()
        self.images = Images()
        self.log = Log()
        self.recognition = Recognition()

    def telegramConfig(self):
        try:
            file = open("./config/services/telegram.yaml",
                        'r', encoding='utf8')
        except FileNotFoundError:
            print('Info: Telegram not configure, rename EXAMPLE-telegram.yaml to telegram.yaml in /config/services/ folder')
            exit()

        with file as s:
            stream = s.read()
        return yaml.safe_load(stream)

    def start(self):
        self.importLibs()
        if self.enableTelegram == False:
            return

        self.log.console('Initializing Telegram...', emoji='📱')
        self.updater = Updater(self.telegramConfig['botfather_token'])

        try:
            def send_print(update: Update, context: CallbackContext) -> None:
                update.message.reply_text('🔃 Proccessing...')
                screenshot = self.desktop.printScreen()
                image = './logs/print-report.{}'.format(
                    self.telegramConfig['format_of_image'])
                cv2.imwrite(image, screenshot)
                update.message.reply_photo(photo=open(image, 'rb'))

            def send_id(update: Update, context: CallbackContext) -> None:
                update.message.reply_text(
                    f'🆔 Your id is: {update.effective_user.id}')

            def send_map(update: Update, context: CallbackContext) -> None:
                update.message.reply_text('🔃 Proccessing...')
                if self.sendMapReport() is None:
                    update.message.reply_text('😿 An error has occurred')

            def send_bcoin(update: Update, context: CallbackContext) -> None:
                update.message.reply_text('🔃 Proccessing...')
                if self.sendBCoinReport() is None:
                    update.message.reply_text('😿 An error has occurred')

            def send_donation(update: Update, context: CallbackContext) -> None:
                update.message.reply_text(
                    f'🎁 BCBOT Chave PIX: \n\n 08912d17-47a6-411e-b7ec-ef793203f836 \n\n Muito obrigado! 😀')
                update.message.reply_text(
                    f'🎁 Smart Chain Wallet: \n\n 0x4847C29561B6682154E25c334E12d156e19F613a \n\n Thank You! 😀')

            def send_stop(update: Update, context: CallbackContext) -> None:
                update.message.reply_text(f'🛑 Shutting down bot...')

            commands = [
                ['print', send_print],
                ['id', send_id],
                ['map', send_map],
                ['bcoin', send_bcoin],
                ['donation', send_donation],
                ['stop', send_stop]
            ]

            for command in commands:
                self.updater.dispatcher.add_handler(
                    CommandHandler(command[0], command[1]))

            self.updater.start_polling()
        except:
            self.log.console(
                'Bot not initialized, see configuration file', emoji='🤖')

    def stop(self):
        if self.updater:
            self.updater.stop()

    def sendMapReport(self):
        self.importLibs()
        if self.enableTelegram == False:
            return
        if(len(self.telegramConfig['chat_ids']) <= 0 or self.telegramConfig['enable_map_report'] is False):
            return

        currentScreen = self.recognition.currentScreen()

        back_button = self.images.image('back_button')
        close_button = self.images.image('close_button')
        full_screen_button = self.images.image('full_screen_button')
        treasure_hunt_banner = self.images.image('treasure_hunt_banner')

        if currentScreen == "main":
            if self.actions.clickButton(treasure_hunt_banner):
                self.actions.sleep(2, 2)
        elif currentScreen == "character":
            if self.clickButton(close_button):
                self.actions.sleep(2, 2)
                if self.clickButton(treasure_hunt_banner):
                    self.actions.sleep(2, 2)
        elif currentScreen == "treasure_hunt":
            self.actions.sleep(2, 2)
        else:
            return

        back_btn = self.recognition.positions(back_button, return0=True)
        full_screen_btn = self.recognition.positions(
            full_screen_button, return0=True)

        if len(back_btn) <= 0 or len(full_screen_btn) <= 0:
            return
        x, y, _, _ = back_btn[0]
        x1, y1, w, _ = full_screen_btn[0]

        newY0 = y
        newY1 = y1
        newX0 = x
        newX1 = x1 + w

        image = './logs/map-report.%s' % self.telegramConfig['format_of_image']
        with mss.mss() as sct:
            monitorToUse = self.config['app']['monitor_to_use']
            monitor = sct.monitors[monitorToUse]
            sct_img = np.array(sct.grab(monitor))
            crop_img = sct_img[newY0:newY1, newX0:newX1]

            cv2.imwrite(image, crop_img)
            self.actions.sleep(1, 1)
            try:
                for chat_id in self.telegramConfig['chat_ids']:
                    self.TelegramBot.send_photo(
                        chat_id=chat_id, photo=open(image, 'rb'))
            except:
                self.log.console('Telegram offline', emoji='😿')

            try:
                self.sendPossibleAmountReport(sct_img[:, :, :3])
            except:
                self.log.console('Error finding chests',
                                 services=True, emoji='😿')

        self.actions.clickButton(close_button)
        self.log.console('Map report sent', services=True, emoji='📄')
        return True

    def sendPossibleAmountReport(self, baseImage):
        if self.enableTelegram == False:
            return

        chest_01 = self.images.image('chest_01')
        chest_02 = self.images.image('chest_02')
        chest_03 = self.images.image('chest_03')
        chest_04 = self.images.image('chest_04')

        threshold = self.config['threshold']['chest']

        c01 = len(self.recognition.positions(
            chest_01, threshold, baseImage, True))
        c02 = len(self.recognition.positions(
            chest_02, threshold, baseImage, True))
        c03 = len(self.recognition.positions(
            chest_03, threshold, baseImage, True))
        c04 = len(self.recognition.positions(
            chest_04, threshold, baseImage, True))

        chestValues = self.config['chests']['values']
        value01 = c01 * chestValues["chest_01"]
        value02 = c02 * chestValues["chest_02"]
        value03 = c03 * chestValues["chest_03"]
        value04 = c04 * chestValues["chest_04"]

        total = value01 + value02 + value03 + value04

        report = """
Possible quantity chest per type:
🟤 - """+str(c01)+"""
🟣 - """+str(c02)+"""
🟡 - """+str(c03)+"""
🔵 - """+str(c04)+"""

🤑 Possible amount: """+f'{total:.3f} BCoin'+"""
"""
        self.log.console(report, services=True)

    def sendBCoinReport(self):
        self.importLibs()
        if self.enableTelegram == False:
            return
        if(len(self.telegramConfig['chat_ids']) <= 0 or self.telegramConfig['enable_coin_report'] is False):
            return

        treasure_hunt_banner = self.images.image('treasure_hunt_banner')
        close_button = self.images.image('close_button')
        treasure_chest_button = self.images.image('treasure_chest_button')
        bcoins = self.images.image('bcoins')

        currentScreen = self.recognition.currentScreen()
        if currentScreen == "main":
            if self.actions.clickButton(treasure_hunt_banner):
                self.actions.sleep(2, 2)
        elif currentScreen == "character":
            if self.actions.clickButton(close_button):
                self.actions.sleep(2, 2)
                if self.actions.clickButton(treasure_hunt_banner):
                    self.actions.sleep(2, 2)
        elif currentScreen == "treasure_hunt":
            self.actions.sleep(2, 2)
        else:
            return

        self.actions.clickButton(treasure_chest_button)
        self.actions.sleep(5, 15)

        coin = self.recognition.positions(bcoins, return0=True)
        image = './logs/bcoin-report.%s' % self.telegramConfig['format_of_image']
        if len(coin) > 0:
            x, y, w, h = coin[0]

            with mss.mss() as sct:
                monitorToUse = self.config['app']['monitor_to_use']
                monitor = sct.monitors[monitorToUse]
                sct_img = np.array(sct.grab(monitor))
                crop_img = sct_img[y:y+h, x:x+w]
                cv2.imwrite(image, crop_img)
                self.actions.sleep(1, 1)
                try:
                    for chat_id in self.telegramConfig['chat_ids']:
                        self.TelegramBot.send_photo(
                            chat_id=chat_id, photo=open(image, 'rb'))
                except:
                    self.log.console('Telegram offline', emoji='😿')
        self.actions.clickButton(close_button)
        self.log.console('BCoin report sent', services=True, emoji='📄')
        return True

    def sendTelegramMessage(self, message):
        self.importLibs()
        if self.enableTelegram == False:
            return

        try:
            if(len(self.telegramConfig['chat_ids']) > 0):
                for chat_id in self.telegramConfig['chat_ids']:
                    self.TelegramBot.send_message(
                        text=message, chat_id=chat_id)
        except:
            self.log.console(
                'Error to send telegram message. See configuration file', emoji='📄')
            return

    def sendTelegramPrint(self):
        self.importLibs()
        if self.enableTelegram == False:
            return
        try:
            image = './logs/print-report.%s' % self.telegramConfig['format_of_image']
            if(len(self.telegramConfig['chat_ids']) > 0):
                screenshot = self.desktop.printScreen()
                cv2.imwrite(image, screenshot)
                for chat_id in self.telegramConfig['chat_ids']:
                    self.TelegramBot.send_photo(
                        chat_id=chat_id, photo=open(image, 'rb'))
        except:
            self.log.console(
                'Error to send telegram print. See configuration file', emoji='📄')
