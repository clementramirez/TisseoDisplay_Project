# Modules importation
from HI_Treads import Led, Button_Retreiver, LCDscreen
from DB_Treads import DB_Tread
import time
import threading
import configparser
import logging
# import coloredlogs # Uncomment if used later
from logging.handlers import RotatingFileHandler


class DebugShell(threading.Thread):
    def run(self):
        while True:
            ipt = input()
            ipt = ipt.split(" ")
            if ipt[0] == "read":
                print(BT_R.read())
            elif ipt[0] == "led":
                try:
                    LED.set(int(ipt[1]), float(ipt[2]))
                except Exception as exep:
                    print("Error: mode or/and option incorrect ==>", exep)
            elif ipt[0] == "clear":
                LCD.reset()
            elif ipt[0] == "exit":
                BT_R.stop()
                DB_T.stop()
                LCD.stop()
                print("Bye Bye !!")
                break
            else:
                print("Unknown command entered")


# Configuration File Data Retreiving
config = configparser.ConfigParser()
config.read('TisseoDisplay.conf')

# Logger Init
logger = logging.getLogger()
# coloredlogs.install(level='DEBUG', logger=logger) #Uncomment if used later
formatter = logging.Formatter('%(asctime)s | [%(levelname)s] | %(message)s')
file_handler = RotatingFileHandler(config['LogFile_config']['Filename'], 'a', 10000000, 1)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

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

debugshell = DebugShell()
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
        logger.error(e)

    time.sleep(0.01)
