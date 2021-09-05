# Modules importation
from DB_Treads import DB_Tread
import sys
import threading
import time
import RPi.GPIO as GPIO
import datetime

import socket
import lcddriver
import logging
import tinytuya

# Logger Init
logger = logging.getLogger()


class Led():
    """
    Returns a Led Object

    Attributes
    ----------
    LED_1 : int
        Pin connected to the led
    mode : int
        Indicates the current mode for the led
    option : float
        Indicates the current option for the led
    timer : treading.Timer object
        Timer which is used for the blinking mode
    blinkstate : int
        Indicates if the led is powered on or off

    Methods
    -------
    blink()
        Blink function that works with a timer which is called after a specified number of seconds
    set(mode, option)
        Sets a new mode for the led with a specified mode and an associed option
    cancel()
        Cancels the timer to kill the Tread process
    """
    def __init__(self, pin):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(int(pin), GPIO.OUT)
        self.LED_1 = int(pin)
        self.mode = 0
        self.lastmode = 0
        self.option = 0
        self.lastoption = 0
        self.timer = threading.Timer(self.option, self.blink)
        self.blinkstate = 0
        GPIO.output(self.LED_1, 0)

    def blink(self):
        """Blink function that works with a timer which is called after a specified number of seconds"""
        self.blinkstate = (self.blinkstate + 1) % 2
        GPIO.output(self.LED_1, self.blinkstate)
        logger.debug("Led state is : %s", self.blinkstate)
        self.timer = threading.Timer(self.option, self.blink)
        self.timer.start()

    def set(self, mode, option):
        """
        Sets a new mode for the led with a specified mode and an associed option

        Parameters
        ----------
        mode (int) : Mode for controling the led
            -If mode == 0: Persistant state
            -If mode == 1: Blinking state
        option (float or int) :
            -For Persistant state : 0 turn off // 1 turn on
            -For Blink state : option is the period time of the blinking
        """
        self.mode = mode
        self.option = option

        # Persistant mode
        if mode == 0:
            self.cancel()
            try:
                if option != self.lastoption and mode != self.lastmode:
                    GPIO.output(self.LED_1, int(option))
                    logger.info("Led switched to mode : %s with option : %s", mode, option)
                    self.lastmode = mode
            except Exception:
                print("Error: mode or/and option incorrect")
        # Blinking mode
        elif mode == 1:
            if option != 0 and option != self.lastoption:
                logger.info("Led switched to mode : %s with option : %s", mode, option)
                self.lastoption = option
                self.lastmode = mode
                self.cancel()
                self.blink()

    def cancel(self):
        """Cancels the timer to kill the Tread process"""
        self.timer.cancel()


class Button_Retreiver(threading.Thread):
    """
    Returns a Led object

    Attributes
    ----------
    Button_Buff : list
        FIFO list that contains tuples of buttons configurations
    updt_rate : float
        Time between two update of buttons states in seconds
    wantstop : boolean
        Shows if the user or program wants to stop the current thread
    BT_UP : int
        Pin connected to UP Button
    BT_DW : int
        Pin connected to DOWN Button
    BT_LF : int
        Pin connected to LEFT Button
    BT_RG : int
        Pin connected to RIGHT Button
    BT_OK : int
        Pin connected to OK Button

    Methods
    -------
    run()
        Reserved function for the treading process
    read()
        Returns the First element and deletes it from the FIFO self.Button_Buff
    stop()
        Stop the current tread
    """
    def __init__(self, updt_rate=0.2, bt_up=38, bt_dw=31, bt_lf=37, bt_rg=36, bt_ok=33):
        """Constructs all attributes and set GPIO pins"""
        threading.Thread.__init__(self)
        self.Button_Buff = []
        self.updt_rate = updt_rate
        self.wantstop = False
        self.BT_UP = int(bt_up)
        self.BT_DW = int(bt_dw)
        self.BT_LF = int(bt_lf)
        self.BT_RG = int(bt_rg)
        self.BT_OK = int(bt_ok)

        # Sets pins references to BOARD
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)

        # Registers buttons pins as Input
        GPIO.setup([self.BT_UP, self.BT_DW, self.BT_LF, self.BT_RG, self.BT_OK], GPIO.IN)

        logger.warning("Button_Retreiver Thread Initialised")

    def run(self):
        """Reserved function for the treading process"""
        logger.warning("Button_Retreiver Thread Started")
        lastElement = [(GPIO.input(self.BT_UP), GPIO.input(self.BT_DW),
                        GPIO.input(self.BT_LF), GPIO.input(self.BT_RG),
                        GPIO.input(self.BT_OK))]

        while not self.wantstop:
            act_Data = (GPIO.input(self.BT_UP), GPIO.input(self.BT_DW),
                        GPIO.input(self.BT_LF), GPIO.input(self.BT_RG),
                        GPIO.input(self.BT_OK))

            # Adding the actual tuple of data in the FIFO
            if (act_Data != lastElement and act_Data != (0, 0, 0, 0, 0)):
                self.Button_Buff.append(act_Data)
                logger.info("Button Pressed : %s", act_Data)
            lastElement = act_Data

            time.sleep(self.updt_rate)

    def read(self):
        """Returns the First element and deletes it from the FIFO self.Button_Buff"""
        if self.Button_Buff:
            recup_line = self.Button_Buff[0]
            del self.Button_Buff[0]

            return recup_line
        else:
            return None

    def stop(self):
        """Stops the current tread"""
        logger.warning("Button_Retreiver Thread Stopped")
        self.wantstop = True


class LCDscreen(threading.Thread):
    """
    Returns a LCD screen object that is capable of displays menus and information

    Attributes
    ----------
    lcd : lcddriver.object
        LCD screen object
    mode : int
        Indicates the current menu that is shown on the screen
    wantstop : boolean
        Shows if the user or program want to stop the current thread
    DB_T : DB object
        The DB object used to retrieve autobus information stocked in mysql DB
    nightMode_is_active : boolean
        Indicates if the night mode is active

    Methods
    -------
    run()
        Reserved function for the treading process
    stop()
        Stops the current tread
    set(mode)
        Changes the current menu or mode of the screen
    reset()
        Resets the lcd screen
    set_backlight()
        Sets the LCD backlight ON or OFF
    """
    def __init__(self, **kargs):
        """Constructs all attributes, initialised the lcd screen and shows splash screen"""
        threading.Thread.__init__(self)

        self.DB_T, self.LED_T, self.METEO_T, self.IMPR3D_GPIO, self.MAINBULB_TUYA = kargs['DB_object'], kargs['LED_object'], kargs['METEO_object'], kargs['IMPR3D_object'], kargs['MAINBULB_TUYA']

        # Initialisation of the LCD screen
        self.lcd = lcddriver.lcd()
        self.lcd.lcd_clear()
        self.mode = 0
        self.selectedLine = 2
        self.available = True
        self.wantstop = False
        self.nightMode_is_active = False

        # Shows the init screen
        self.lcd.lcd_display_string("*------------------*", 1)
        self.lcd.lcd_display_string("|  Tisseo Display  |", 2)
        self.lcd.lcd_display_string("|       V1.0       |", 3)
        self.lcd.lcd_display_string("*------------------*", 4)

    def run(self):
        """Reserved function for the treading process"""
        timenow = datetime.datetime.now()
        while not self.wantstop:
            try:
                # Check internet connection
                socket.setdefaulttimeout(1)
                socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))

                if self.available is True:
                    self.available = False

                    # Concatenate Datas from the DB
                    lasttimenow = timenow
                    timenow = datetime.datetime.now()
                    RawData = self.DB_T.read()
                    if timenow.second != lasttimenow.second and RawData != []:
                        datas = []
                        timestr = "%02d:%02d" % (timenow.hour, timenow.minute)
                        for line in RawData:
                            deltaT = line[0] - timenow
                            datas.append(str(str(deltaT).split(".")[0]).split(":"))

                    # Retreive meteo data
                    current_meteo = self.METEO_T.read()
                    # Apply different senarios for the led
                    if 7 < int(datas[0][1]) <= 10:
                        self.LED_T.set(1, 1)
                    elif 5 <= int(datas[0][1]) <= 7:
                        self.LED_T.set(1, 0.5)
                    elif 2 <= int(datas[0][1]) < 5:
                        self.LED_T.set(1, 0.25)
                    else:
                        self.LED_T.set(0, 0)

                    if self.mode == 0:
                        if timenow.second != lasttimenow.second and RawData != []:
                            self.lcd.lcd_display_string(" Prch Passages " + timestr, 1)
                            for i, data in enumerate(datas, 2):
                                self.lcd.lcd_display_string("79-Ramon %02dh %02dm %02ds" % (int(data[0]),
                                                                                            int(data[1]),
                                                                                            int(data[2])), i)
                    # Second display mode
                    elif self.mode == 1:
                        if timenow.second != lasttimenow.second and RawData != []:
                            self.lcd.lcd_display_string("     Meteo     " + timestr, 1)
                            self.lcd.lcd_display_string("Wind: %02dkm/h - %02d" % (current_meteo['Wind_spd'],
                                                                                   current_meteo['Wind_hdg']), 2)
                            self.lcd.lcd_display_string("Clouds: %02d%% - Rn: %02d" % (current_meteo['Clds'],
                                                                                       current_meteo['Rain']), 3)
                            self.lcd.lcd_display_string("T: %02d/%02dC - H: %02d%%" % (current_meteo['T_real'],
                                                                                       current_meteo['T_ressent'],
                                                                                       current_meteo['Hum']), 4)
                    elif self.mode == 2:
                        self.lcd.lcd_display_string(" Interrupteurs " + timestr, 1)
                        self.lcd.lcd_display_string(" Impr 3d         {}".format(" ON" if self.IMPR3D_GPIO.getState() else "OFF"), 2)
                        self.lcd.lcd_display_string(" Main Bulb      {}".format(self.MAINBULB_TUYA.getState()), 3)
                        self.lcd.lcd_display_string("                    ", 4)
                        self.lcd.lcd_display_string(">", self.selectedLine + 2)
                        time.sleep(0.2)
                    elif self.mode == 3:
                        self.lcd.lcd_display_string("  Parametres   " + timestr, 1)
                        self.lcd.lcd_display_string(" Mode Nuit       {}".format(" ON" if self.nightMode_is_active else "OFF"), 2)
                        self.lcd.lcd_display_string("                    ", 3)
                        self.lcd.lcd_display_string("                    ", 4)
                        self.lcd.lcd_display_string(">", self.selectedLine + 2)
                        time.sleep(0.2)
                    self.available = True
            except socket.error as ex:
                self.lcd.lcd_display_string("*------------------*", 1)
                self.lcd.lcd_display_string("|     Internet     |", 2)
                self.lcd.lcd_display_string("|   Disconnected   |", 3)
                self.lcd.lcd_display_string("*------------------*", 4)
            except OSError:
                logger.error("I/O Error of the LCD screen")
                self.available = True
            except ValueError as e:
                logger.error("Value Error as %s\n With FormDat as %s" % e)
                self.available = True
            except NameError as e:
                logger.error("Name Error as %s" % (e))
                self.available = True
            time.sleep(0.2)

    def stop(self):
        """Stops the current tread"""
        self.wantstop = True

    def set(self, mode):
        """Changes the current menu or mode of the screen"""
        while self.available is False:
            pass
        self.available = False
        self.reset()
        self.mode = mode
        logger.info("Screen switched to mode : %d", mode)
        self.available = True

    def reset(self):
        """Resets the lcd screen"""
        self.lcd = lcddriver.lcd()
        self.lcd.lcd_clear()

    def set_backlight(self, state):
        while self.available is False:
            pass
        self.available = False
        self.lcd.lcd_backlight(state)
        self.available = True


class GPIO_device():
    '''
    Return a GPIO_device that is capable to return his binary state and change it

    Attributes
    ----------
    pin : int
        Indicate the pin of the GPIO device
    name : str
        Indicate the name of the GPIO device
    Methods
    -------
    getState()
        Return the current state of the GPIO device
    setState()
        Change the state of the GPIO device
    '''
    def __init__(self, pin, name):
        self.pin = int(pin)
        self.name = name
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.pin, GPIO.OUT)

    def getState(self):
        """Return the current state of the GPIO device"""
        return GPIO.input(self.pin)

    def setState(self, state):
        """Change the state of the GPIO device"""
        GPIO.output(self.pin, state)
        logger.info("GPIO device <%s> switched to %s", self.name, state)


class TuyaBulb_device():
    '''
    Return a TuyaBulb_device that is capable to use tinytuya package and configure it

    Attributes
    ----------
    device_id : str
        Device ID
    device_ip : str
        Device IP
    device_key : str
        Device local key
    device_version : float
        Device version (3.1 or 3.3(default))
    powerStatus : boolean
        Indicate if the bulb is ON, OFF or Unknown
    rawStatus : dictionnary
        Store the result of device.status() function
    device : tinytuya.BulbDevice.object
        BulbDevice object from tinytuya package
    Methods
    -------
    toggle()
        Toogle the bulb according with the last retreived status
    getState()
        Change the state of the GPIO device
    '''
    def __init__(self, device_id, device_ip, device_key, name, device_version=3.3):
        self.device_id = device_id
        self.device_ip = device_ip
        self.device_key = device_key
        self.name = name
        self.device_version = device_version

        self.device = tinytuya.BulbDevice(device_id, device_ip, device_key)
        self.device.set_version(device_version)
        self.device.set_socketTimeout(0.2)
        self.device.set_socketRetryLimit(1)

    def getState(self):
        self.rawStatus = self.device.status()
        if self.rawStatus.get('Error', False) == 'Network Error: Device Unreachable':
            return 'DISC'
        elif self.rawStatus.get('dps', {}).get('1') is True:
            self.powerStatus = True
            return '  ON'
        elif self.rawStatus.get('dps', None).get('1') is False:
            self.powerStatus = False
            return ' OFF'
        else:
            self.powerStatus = None
            return '????'

    def toggle(self):
        """Toogle the bulb according with the last retreived status"""
        if self.powerStatus is True:
            self.device.turn_off()
        elif self.powerStatus is False:
            self.device.turn_on()
        else:
            pass
        logger.info("Tuya device <%s> switched to %s", self.name, not self.powerStatus)