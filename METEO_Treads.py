# Modules importation
import time
import threading
import logging
from datetime import datetime
from meteofrance_api import MeteoFranceClient
from meteofrance_api.model import Place

# Logger Init
logger = logging.getLogger()


class METEO_Tread():
    """
    Return a METEO_Tread object

    Attributes
    ----------

    Methods
    -------


    """
    def __init__(self, updt_rate=300):
        self.updt_rate = updt_rate
        self.client = MeteoFranceClient()
        self.currentmeteo = {}
        self.retreiveAndExtract()

    def read(self):
        return self.currentmeteo

    def retreiveAndExtract(self):
        rawDatas = self.client.get_forecast(latitude=43.534240, longitude=1.518130)
        self.timer = threading.Timer(self.updt_rate, self.retreiveAndExtract)
        self.timer.start()
        self.currentmeteo = {'T_real': round(rawDatas.current_forecast["T"]["value"]),
                             'T_ressent': rawDatas.current_forecast["T"]["windchill"],
                             'Hum': round(rawDatas.current_forecast["humidity"]),
                             'Wind_spd': rawDatas.current_forecast["wind"]["speed"],
                             'Wind_hdg': rawDatas.current_forecast["wind"]["direction"],
                             'Clds': rawDatas.current_forecast["clouds"],
                             'Rain': rawDatas.current_forecast["rain"]["1h"]}
        logger.info("New meteo data retreived !")

    def stop(self):
        self.timer.cancel()


if __name__ == "__main__":
    met = METEO_Tread()
    while True:
        print(met.read())
        time.sleep(2)
