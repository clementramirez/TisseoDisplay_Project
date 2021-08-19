# Modules importation
from HI_Treads import Led, Button_Retreiver, LCDscreen, GPIO_device, TuyaBulb_device
from DB_Treads import DB_Tread
from METEO_Treads import METEO_Tread
import time
import threading
import configparser
import logging
# import coloredlogs # Uncomment if used later
from logging.handlers import RotatingFileHandler

# Used Pins
IMPR3D_pin = 22


class DebugShell(threading.Thread):
    def run(self):
        while True:
            ipt = input()
            ipt = ipt.split(" ")
            if ipt[0] == "read":
                print(BT_R.read())
            if ipt[0] == "button":
                try:
                    if ipt[1] == "right":
                        BT_R.Button_Buff.append([0, 0, 0, 1, 0])
                    elif ipt[1] == "left":
                        BT_R.Button_Buff.append([0, 0, 1, 0, 0])
                    elif ipt[1] == "up":
                        BT_R.Button_Buff.append([1, 0, 0, 0, 0])
                    elif ipt[1] == "down":
                        BT_R.Button_Buff.append([0, 1, 0, 0, 0])
                    elif ipt[1] == "ok":
                        BT_R.Button_Buff.append([0, 0, 0, 0, 1])
                    else:
                        print("The specified button does not exist")
                except IndexError:
                    print("You haven't specified any button to press")
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
formatter = logging.Formatter('%(asctime)s || %(module)s-->l.%(lineno)d || [%(levelname)s] | %(message)s')
file_handler = RotatingFileHandler(config['LogFile_config']['Filename'], 'a', 10000000, 1)
file_handler.setLevel(20)
logger.setLevel(20)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
threading.current_thread().name = "Main Program"

# Declaration of global variables


# Initialisation of Human-Machine Interface and DB_Thread
LED = Led()
METEO_T = METEO_Tread()
BT_R = Button_Retreiver(0.1)
DB_T = DB_Tread(config['DB_config']['Host'],
                config['DB_config']['User'],
                config['DB_config']['Password'],
                config['DB_config']['Database'],
                config['TisseoAPI_config']['Request'],
                config['TisseoAPI_config']['API_key'],
                config['DB_config']['Updt_Rate'])
IMPR3D_GPIO = GPIO_device(IMPR3D_pin, "Impr 3D")
MAINBULB_TUYA = TuyaBulb_device('020836852462ab546927', "192.168.1.18", "e56e24202f6f428f", "Main Bulb")
LCD = LCDscreen(DB_object=DB_T, LED_object=LED, METEO_object=METEO_T,
                IMPR3D_object=IMPR3D_GPIO, MAINBULB_TUYA=MAINBULB_TUYA)
BT_R.start()
DB_T.start()
LCD.start()

debugshell = DebugShell()
debugshell.start()
logger.debug("Let's Go !!")
time.sleep(3)

while True:
    try:
        button = BT_R.read()
        if button is not None:
            if button[4] == 1:
                if LCD.mode == 2:
                    if LCD.selectedLine == 0:
                        IMPR3D_GPIO.setState((IMPR3D_GPIO.getState() + 1) % 2)
                    elif LCD.selectedLine == 1:
                        MAINBULB_TUYA.toggle()
            if button[3] == 1:
                LCD.set((LCD.mode + 1) % 3)
            if button[2] == 1:
                LCD.set((LCD.mode - 1) % 3)
            if button[1] == 1:
                if LCD.mode == 2:
                    LCD.selectedLine = (LCD.selectedLine + 1) % 3
            if button[0] == 1:
                if LCD.mode == 2:
                    LCD.selectedLine = (LCD.selectedLine - 1) % 3
    except Exception as e:
        logger.error(e)

    time.sleep(0.01)
