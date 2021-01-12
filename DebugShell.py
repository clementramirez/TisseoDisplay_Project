import logging
from logging.handlers import RotatingFileHandler
import configparser
import threading
# Logger Init
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Configuration File Data Retreiving
config = configparser.ConfigParser()
config.read('TisseoDisplay.conf')

# coloredlogs.install(level='DEBUG', logger=logger) #Uncomment if used later
formatter = logging.Formatter('%(asctime)s | [%(levelname)s] | %(message)s')
file_handler = RotatingFileHandler(config['LogFile_config']['Filename'], 'a', 10000000, 1)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


class DebugShell(threading.Thread):
    def __init__(self, LED, BT_R, LCD):
        threading.Thread.__init__(self)
        self.LED = LED
        self.LCD = LCD
        self.BT_R = BT_R

    def run(self):
        while True:
            try:
                ipt = input()
                ipt = ipt.split(" ")
                if ipt[0] == "read":
                    print(self.BT_R.read())
                elif ipt[0] == "led":
                    try:
                        self.LED.set(int(ipt[1]), float(ipt[2]))
                    except Exception as exep:
                        print("Error: mode or/and option incorrect ==>", exep)
                elif ipt[0] == "clear":
                    self.LCD.reset()
                elif ipt[0] == "button":
                    self.BT_R.Button_Buff.append((0,0,0,1,0))
                elif ipt[0] == "exit":
                    self.BT_R.stop()
                    DB_T.stop()
                    self.LCD.stop()
                    self.LED.cancel()
                    print("Bye Bye !!")
                    break
                else:
                    print("Unknown command entered")
            except Exception as e:
                logger.critical("Uncatched Error : %s", e)