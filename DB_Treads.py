# Modules importation
from lxml import etree
import requests
import sys
import threading
import datetime
import mysql.connector
import time
import logging

# Logger Init
logger = logging.getLogger()


class DB_Tread(threading.Thread):
    """
    Returns a DB object that can retrieves information from Tisseo Api and saves them on a mysql DB

    Attributes
    ----------
    updt_rate : float
        Time between two updates of the DB in seconds
    wantstop : boolean
        Shows if the user or program want to stop the current thread
    HTTPRequest : str
        Contains the body of the Tisseo API HTTP request
    APIKey : str
        Contains the API key sent by Tisseo (If you want to obtain it, please send an email to opendata@tisseo.fr)
    mydb : mysql.connector object
        mysql.connector object created if the connection process succeeds
    addNextStopData : tuple with str inside
        Contains the structure of mysql request to send data to the DB

    Methods
    -------
    RecupAndUpload()
        Sends the HTTP request and uploads filtered data to mysql DB
    run()
        Reserved function for the treading process
    stop()
        Stops the current tread
    read()
        Returns latest autobus data
    """
    def __init__(self, host, user, password, database, request, api_key, updt_rate=5):
        """
        Constructor for DB_Tread class

        Parameters
        ----------
            host (str) : Host name or adress for the mysql DB
            user (str) : User name of mysql DB
            password (str) : Password for selected user
            database (str) : Database name that contain your autobus lines data
            request (str) : String that contains the body of the Tisseo API HTTP request
            api_key (str) : String that contains the API key sent by Tisseo (If you want to obtain it, please send an email to opendata@tisseo.fr)
            updt_rate (float) : Time between two updates of the DB in seconds
        """
        threading.Thread.__init__(self)
        self.updt_rate = updt_rate
        self.wantstop = False
        self.HTTPRequest = request
        self.APIKey = api_key

        # Establishing a connection with the DB
        try:
            self.mydb = mysql.connector.connect(host=host, user=user, password=password, database=database)
            cursor = self.mydb.cursor()

            '''
            addNextStopData = ("INSERT INTO 79_Ramonville_Périgord "
                                "(Next_Bus_1, Real_Time_1, Next_Bus_2, Real_Time_2, Next_Bus_3, Real_Time_3) "
                                "VALUES (%s, %s, %s, %s, %s, %s)")
            '''

            self.addNextStopData = ("UPDATE 79_Ramonville_Périgord SET Next_Bus_1 = %s, Real_Time_1 = %s, Next_Bus_2 = %s, Real_Time_2 = %s, Next_Bus_3 = %s, Real_Time_3 = %s")

            logger.warning("Connection Opened !!")
        except mysql.connector.Error as details:
            logger.critical("Error While Connecting to the DataBase : %s", details)

    def RecupAndUpload(self):
        """Sends the HTTP request and upload filtered data to mysql DB"""
        ExtractedData = []
        self.FormatedData = []

        cursor = self.mydb.cursor()

        # Retreiving XML data from Tisseo API
        try:
            queryAsw = requests.get(self.HTTPRequest + "&key=" + self.APIKey).text.encode('utf-8')
            # XML data exctraction
            xmlf = etree.fromstring(queryAsw)
            for departure in xmlf.xpath('/departures/departure'):
                ExtractedData.append([departure.get('dateTime'), departure.get('realTime')])

            for passage in ExtractedData[:3]:
                passDateTime = datetime.datetime.strptime(passage[0], "%Y-%m-%d %H:%M:%S")
                if passage[1] == "yes":
                    passage[1] = True
                else:
                    passage[1] = False
                self.FormatedData.append([passDateTime, passage[1]])

            # Sending extracted data to mysql DB
            cursor.execute(self.addNextStopData, (self.FormatedData[0][0], self.FormatedData[0][1],
                                                  self.FormatedData[1][0], self.FormatedData[1][1],
                                                  self.FormatedData[2][0], self.FormatedData[2][1]))
            self.mydb.commit()
        except Exception:
            logger.critical("Network Failed !!")
        cursor.close()

    def run(self):
        """Reserved function for the treading process"""
        while not self.wantstop:
            self.RecupAndUpload()
            time.sleep(5)

    def read(self):
        """Returns latest autobus data"""
        return self.FormatedData

    def stop(self):
        """Stops the current tread"""
        try:
            self.mydb.close()
            logger.warning("Connection Closed !!")
        except mysql.connector.Error as details:
            logger.error("Error While Disconnecting from the DataBase : ", details)

        self.wantstop = True


# Test code which uploads Tisseo data to mysql DB
if __name__ == "__main__":
    DB_T = DB_Tread('localhost', 'User', 'password', 'db_name')
    DB_T.start()

    while True:
        ipt = input("Enter a command : ")
        if ipt == "exit":
            print("Bye Bye")
            DB_T.stop()
        else:
            print("Unknow command")
