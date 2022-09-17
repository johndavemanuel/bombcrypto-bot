from pyclick import HumanClicker
from PIL import Image, ImageSequence
from cv2 import cv2

import numpy as np
import os
import pyautogui
import random


humanClicker = HumanClicker()

heroes_work_clicked = 0
heroes_work_clicked_total = 0

heroes_house_clicked = 0
heroes_house_clicked_total = 0


class Heroes:
    def __init__(self):
        from src.config import Config
        self.config = Config().read()
        self.next_refresh_heroes = self.config['time_intervals']['send_heroes_for_work'][0]
        self.next_refresh_heroes_positions = self.config['time_intervals']['refresh_heroes_positions'][0]

    def importLibs(self):
        from src.actions import Actions
        from src.auth import Auth
        from src.config import Config
        from src.desktop import Desktop
        from src.error import Errors
        from src.game import Game
        from src.images import Images
        from src.recognition import Recognition
        from src.log import Log
        self.accounts = Config().accounts()
        self.actions = Actions()
        self.auth = Auth()
        self.config = Config().read()
        self.desktop = Desktop()
        self.errors = Errors()
        self.game = Game()
        self.images = Images()
        self.recognition = Recognition()
        self.log = Log()

    def getMoreHeroes(self, heroesMode=None):

        global next_refresh_heroes
        global heroes_work_clicked

        self.importLibs()

        mode = self.config['heroes']['mode']
        if mode in ["all", 'workall', 'full', 'green']:
            self.log.console('Search for heroes to work',
                             emoji='🏢', color='green')

        if self.goToHeroes() is False:
            return False

        if heroesMode is not None:
            mode = heroesMode

        if mode == 'all' or mode == 'workall':
            self.log.console('Sending all heroes to work!',
                             services=True, emoji='⚒️', color='green')
        elif mode == 'full':
            self.log.console(
                'Sending heroes with full stamina bar to work!',
                services=True,
                emoji='⚒️',
                color='green')
        elif mode == 'green':
            self.log.console(
                'Sending heroes with green stamina bar to work!',
                services=True,
                emoji='⚒️',
                color='green')
        elif mode == 'restall':
            self.log.console(
                'Put the heroes to rest',
                services=True,
                emoji='💤',
                color='green')
        else:
            self.log.console('Sending all heroes to work!',
                             services=True,
                             emoji='⚒️',
                             color='green')

        if mode == 'all' or mode == 'workall':
            self.clickSendAllButton()
            self.game.goToMap()
            return

        if mode == 'restall':
            self.clickRestAllButton()
            self.game.goToMap()
            return

        scrolls_attempts = self.config['heroes']['list']['scroll_attempts']
        next_refresh_heroes = random.uniform(
            self.config['time_intervals']['send_heroes_for_work'][0],
            self.config['time_intervals']['send_heroes_for_work'][1]
        )

        account_active = int(os.environ['ACTIVE_BROWSER'])
        houseEnabled = self.accounts[account_active]['house']

        buttonsWorkClicked = 0
        buttonsHouseClicked = 0

        heroes_work_clicked = 0
        heroes_house_clicked = 0
        while(scrolls_attempts > 0):
            if mode == 'full':
                buttonsWorkClicked = self.clickFullBarButtons()
                if buttonsWorkClicked is not None:
                    heroes_work_clicked += buttonsWorkClicked
            elif mode == 'green':
                if houseEnabled is True:
                    number = 0
                    while number < 2:
                        buttonsHouseClicked = self.clickHouseButtons()
                        if buttonsHouseClicked is not None:
                            heroes_house_clicked += buttonsHouseClicked
                            number = number+1
                        else:
                            number = 2

                        if type(buttonsHouseClicked) == int and buttonsHouseClicked > 0:
                            self.actions.sleep(
                                1, 1, randomMouseMovement=False, forceTime=True)

                buttonsWorkClicked = self.clickGreenBarButtons()
                if buttonsWorkClicked is not None:
                    heroes_work_clicked += buttonsWorkClicked

            if buttonsWorkClicked == 0 or buttonsWorkClicked is None:
                scrolls_attempts = scrolls_attempts - 1
                self.scroll()

            self.actions.sleep(1, 1, randomMouseMovement=False, forceTime=True)

        if houseEnabled is True:
            self.log.console('{} total heroes sent to house since the bot started'.format(
                heroes_house_clicked), services=True, emoji='🦸', color='yellow')

        self.log.console('{} total heroes sent to work since the bot started'.format(
            heroes_work_clicked_total), services=True, emoji='🦸', color='yellow')

        self.game.goToMap()

    def goToHeroes(self):
        self.importLibs()
        currentScreen = self.recognition.currentScreen()

        back_button = self.images.image('back_button')
        menu_heroe_icon = self.images.image('menu_heroe_icon')
        wait_for_this_hero_list_object = self.images.image(
            'wait_for_this_hero_list_object')

        if currentScreen == "map":
            if self.actions.clickButton(back_button):
                self.actions.sleep(1, 1, forceTime=True)
                if self.actions.clickButton(menu_heroe_icon):
                    self.actions.sleep(1, 1, forceTime=True)
                    # checkCaptcha()
                    if self.recognition.waitForImage(wait_for_this_hero_list_object, threshold=0.8) is False:
                        self.actions.refreshPage()
                        return False
        if currentScreen == "main":
            if self.actions.clickButton(menu_heroe_icon):
                self.actions.sleep(1, 1, forceTime=True)
                # checkCaptcha()
                if self.recognition.waitForImage(wait_for_this_hero_list_object, threshold=0.9) is False:
                    self.actions.refreshPage()
                    return False
        if currentScreen == "unknown" or currentScreen == "login":
            self.auth.checkLogout()

    def refreshHeroesPositions(self):
        self.importLibs()
        self.log.console('Refreshing heroes positions',
                         emoji='🔃', color='yellow')

        global next_refresh_heroes_positions

        next_refresh_heroes_positions = random.uniform(
            self.config['time_intervals']['refresh_heroes_positions'][0],
            self.config['time_intervals']['refresh_heroes_positions'][1]
        )

        back_button = self.images.image('back_button')
        if self.actions.clickButton(back_button):
            self.actions.sleep(1, 1, forceTime=True)
            self.game.goToMap()
        return True

    def sendToWorking(self, bar, buttons):
        y = bar[1]
        for (_, button_y, _, button_h) in buttons:
            isBelow = y < (button_y + button_h)
            isAbove = y > (button_y - button_h)
            if isBelow and isAbove:
                return True
        return False

    def sendToHome(self, rarities, bar, buttons):
        bar_axis_y = bar[1]
        for (_, rarity_y, _, rarity_h) in reversed(rarities):
            isRariryBelow = bar_axis_y < (rarity_y + rarity_h)
            isRarityAbove = (bar_axis_y+rarity_h) > (rarity_y - rarity_h)
            if isRariryBelow and isRarityAbove:
                for (_, button_y, _, button_h) in reversed(buttons):
                    isBelow = bar_axis_y < (button_y + button_h)
                    isAbove = bar_axis_y > (button_y - button_h)
                    if isBelow and isAbove:
                        return True

        return False

    def scroll(self):
        self.importLibs()

        title_heroes_list = self.images.image('title_heroes_list', theme=True)
        character_indicator_pos = self.recognition.positions(title_heroes_list)
        if character_indicator_pos is False:
            return

        x, y, _, h = character_indicator_pos[0]
        scrollHeight = int(y+420)
        self.actions.move(
            (int(x), scrollHeight), np.random.randint(1, 2))

        self.actions.sleep(0.5, 0.5, randomMouseMovement=False, forceTime=True)
        pyautogui.mouseDown(button='left')
        moveCoordinates = (int(x), int(y+h+2))
        self.actions.move(moveCoordinates, 1, forceTime=True)
        self.actions.sleep(0.5, 0.5, randomMouseMovement=False, forceTime=True)
        pyautogui.mouseUp(button='left')
        self.actions.sleep(1, 1, randomMouseMovement=False, forceTime=True)

    def clickFullBarButtons(self):
        self.importLibs()
        offset = self.config['offsets']['work_button_full']
        threshold = self.config['threshold']

        workButtons = self.checkWorkButton()
        if workButtons is False:
            return

        bar_full_stamina = self.images.image('bar_full_stamina')
        bars = self.recognition.positions(
            bar_full_stamina, threshold=threshold['heroes_full_bar'])

        return self.sendingToWork(bars, workButtons, offset, 'full')

    def clickHouseButtons(self):
        self.importLibs()
        offset = self.config['offsets']['house_button']
        threshold = self.config['threshold']

        rarities = self.checkHeroesRaritySendToHouseButton()
        if len(rarities) == 0:
            return

        homeButtons = self.checkHouseButton()
        if homeButtons is False:
            return

        red_bars = []
        bar_empty_stamina = self.images.image('bar_empty_stamina')
        bars_empty = self.recognition.positions(
            bar_empty_stamina, threshold=threshold['heroes_red_bar'])

        if bars_empty is not False:
            red_bars.extend(bars_empty)

        bar_red_stamina_1 = self.images.image('bar_red_stamina_1')
        red_bars_1 = self.recognition.positions(
            bar_red_stamina_1, threshold=threshold['heroes_red_bar'])

        if red_bars_1 is not False:
            red_bars.extend(red_bars_1)

        bar_red_stamina_2 = self.images.image('bar_red_stamina_2')
        red_bars_2 = self.recognition.positions(
            bar_red_stamina_2, threshold=threshold['heroes_red_bar'])

        if red_bars_2 is not False:
            red_bars.extend(red_bars_2)

        return self.sendingToHouse(rarities, red_bars, homeButtons, offset, 'red')

    def clickGreenBarButtons(self):
        self.importLibs()
        offset = self.config['offsets']['work_button_green']
        threshold = self.config['threshold']

        workButtons = self.checkWorkButton()
        if workButtons is False:
            return

        bar_green_stamina = self.images.image('bar_green_stamina')
        bars = self.recognition.positions(
            bar_green_stamina, threshold=threshold['heroes_green_bar'])

        return self.sendingToWork(bars, workButtons, offset, 'green')

    def clickSendAllButton(self):
        self.importLibs()
        threshold = self.config['threshold']

        send_all_heroes_button = self.images.image('send_all_heroes_button')
        rest_all_heroes_button = self.images.image('rest_all_heroes_button')

        send_all = self.recognition.positions(
            send_all_heroes_button, threshold=threshold['heroes_send_all'])

        if send_all is False:
            return

        self.actions.clickButton(send_all_heroes_button)
        self.recognition.waitForImage(rest_all_heroes_button)

    def clickRestAllButton(self):
        self.importLibs()
        threshold = self.config['threshold']

        rest_all_heroes_button = self.images.image('rest_all_heroes_button')
        send_all_heroes_button = self.images.image('send_all_heroes_button')

        rest_all = self.recognition.positions(
            rest_all_heroes_button, threshold=threshold['heroes_rest_all'])

        if rest_all is False:
            return

        self.actions.clickButton(rest_all_heroes_button)
        self.recognition.waitForImage(send_all_heroes_button)

    def sendingToWork(self, bar_green_elements, workButtons, offset, type):
        if bar_green_elements is False:
            return

        if self.config['log']['console'] is not False:
            self.log.console('%d GREEN STAMINA bars detected' %
                             len(bar_green_elements), emoji='🟩', color='red')
            self.log.console('%d WORK buttons detected' %
                             len(workButtons), emoji='🔳', color='red')

        working_bars = []
        for bar in bar_green_elements:
            sendToWorking = self.sendToWorking(bar, workButtons)
            if sendToWorking is True:
                working_bars.append(bar)

        if len(working_bars) > 0:
            message = 'Clicking in {} heroes with {} bar detected.'.format(
                len(working_bars), type)
            self.log.console(message, emoji='👆', color='green')

        for (x, y, w, h) in working_bars:
            offset_random = random.uniform(offset[0], offset[1])
            self.actions.move(
                (int(x+offset_random+(w/2)), int(y+(h/2))),
                np.random.randint(1, 2)
            )
            humanClicker.click()

            global heroes_work_clicked_total
            global heroes_work_clicked

            heroes_work_clicked_total = heroes_work_clicked_total + 1
            if heroes_work_clicked > 15:
                self.log.console('Too many hero clicks, try to increase the back_button threshold',
                                 services=True, emoji='⚠️', color='yellow')
                return
            self.actions.sleep(1, 2)
        return len(working_bars)

    def sendingToHouse(self, rarities, bar_red_elements, homeButtons, offset, type):
        if len(bar_red_elements) == 0:
            return

        if self.config['log']['console'] is not False:
            self.log.console('%d RED STAMINA bars detected' %
                             len(bar_red_elements), emoji='🥵', color='red')
            self.log.console('%d HOME buttons detected' %
                             len(homeButtons), emoji='🔳', color='red')

        red_bars = []
        for bar in reversed(bar_red_elements):
            sendHome = self.sendToHome(rarities, bar, homeButtons)
            if sendHome is True:
                red_bars.append(bar)

        if self.config['log']['console'] is not False:
            self.log.console('%d RED STAMINA bars detected to send Home' %
                             len(bar_red_elements), emoji='🥵', color='red')

        if len(red_bars) > 0:
            message = 'Sending {} heroes to house.'.format(
                len(red_bars), type)
            self.log.console(message, emoji='🏠', color='green')

        for (x, y, w, h) in red_bars:
            offset_random = random.uniform(offset[0], offset[1])
            self.actions.move(
                (int(x+offset_random+(w/2)), int(y+(h/2))),
                np.random.randint(1, 2)
            )
            humanClicker.click()

            global heroes_house_clicked
            global heroes_house_clicked_total

            heroes_house_clicked_total = heroes_house_clicked_total + 1
            if heroes_house_clicked > 4:
                self.log.console('Too many hero clicks to send house, try to increase the back_button threshold',
                                 services=True, emoji='⚠️', color='yellow')
                return
            self.actions.sleep(1, 2)
        return len(red_bars)

    def checkWorkButton(self):
        threshold = self.config['threshold']
        work_button = self.images.image('work_button')
        return self.recognition.positions(
            work_button, threshold=threshold['work_button'])

    def checkHouseButton(self):
        threshold = self.config['threshold']
        home_enable_button = self.images.image('home_enable_button')
        return self.recognition.positions(
            home_enable_button, threshold=threshold['home_enable_button'])

    def checkHeroesRaritySendToHouseButton(self):
        threshold = self.config['threshold']
        account_active = int(os.environ['ACTIVE_BROWSER'])
        rarities = self.accounts[account_active]['rarity']

        positions = []
        screenshot = self.desktop.printScreen()
        for rarity in rarities:
            if self.config['log']['console'] is not False:
                print('Checking rarity: {}'.format(rarity))

            label_rarity = self.images.image(
                '/heroes_types/diamonds/'+rarity, extension='.gif')

            for frame in ImageSequence.Iterator(label_rarity):
                frame = frame.convert('RGBA').copy()
                opencvImage = cv2.cvtColor(
                    np.array(frame), cv2.COLOR_RGB2BGR)
                position = self.recognition.positions(
                    opencvImage, baseImage=screenshot, threshold=threshold['heroes'][rarity])
                if position is not False:
                    if self.config['log']['console'] is not False:
                        print('Found {}'.format(rarity))
                    positions.append(position[0])

            # position = self.recognition.positions(
            #     label_rarity, threshold=threshold['heroes'][rarity])
            # print('position_rarity', position)
            # if position is not False:
            #     positions.append(position[0])

        return positions
