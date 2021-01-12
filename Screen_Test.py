# Modules importation
from HI_Treads import Led, Button_Retreiver, LCDscreen
from DB_Treads import DB_Tread
from DebugShell import DebugShell
import time
import threading
import configparser
import sys
import logging
# import coloredlogs # Uncomment if used later
from logging.handlers import RotatingFileHandler

# Configuration File Data Retreiving
config = configparser.ConfigParser()
config.read('TisseoDisplay.conf')

# Logger Init
logger = logging.getLogger()

# Declaration of global variables
...

# Initialisation of Human-Machine Interface and DB_Thread
LED = Led()
BT_R = Button_Retreiver(0.1)
DB_T = DB_Tread(config['DB_config']['Host'],
                config['DB_config']['User'],
                config['DB_config']['Password'],
                config['DB_config']['Database'],
                config['TisseoAPI_config']['Request'],
                config['TisseoAPI_config']['API_key'],
                config['DB_config']['Updt_Rate'])
LCD = LCDscreen(DB_object=DB_T)
BT_R.start()
DB_T.start()
LCD.start()

debugshell = DebugShell(LED, BT_R, LCD)
debugshell.start()
logger.debug("Hello")
time.sleep(3)
timei = 0.5

while True:
    try:
        button = BT_R.read()
        if button is not None:
            if button[4] == 1:
                dispmode = (dispmode + 1) % 2
                LED.set(0, dispmode)
            if button[3] == 1:
                LCD.set((LCD.mode + 1) % 2)
            if button[0] == 1:
                timei += 0.1
                LED.set(1, timei)
            if button[1] == 1:
                timei -= 0.1
                LED.set(1, timei)
    except Exception as e:
        logger.critical("Uncatched Error : %s", e)

    time.sleep(0.01)
