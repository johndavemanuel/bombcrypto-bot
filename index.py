from colorama import init, Fore, Style

from src.application import Application
from src.log import Log
from src.multi_account import MultiAccount

from src.services.telegram import Telegram

import sys

init()

banner = """
*******************************************************************************
** BOMBCRYPTO - BOT
**
*******************************************************************************
** Press CTRL + C to kill the bot.
*******************************************************************************"""

print(Fore.GREEN + banner + Style.RESET_ALL)

application = Application()
log = Log()
multi_account = MultiAccount()
telegram = Telegram()


def main():
    application.start()
    telegram.start()
    multi_account.start()


def onlyMap():
    application.start()
    telegram.start()
    multi_account.startOnlyMapAction()


if __name__ == '__main__':
    try:
        if 'only-map' in sys.argv:
            onlyMap()
        else:
            main()
    except KeyboardInterrupt:
        log.console('Shutting down the bot',
                    services=True, emoji='😓', color='red')
        telegram.stop()
        exit()
