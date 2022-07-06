"""
Author: Neel Dhulipala, Andrew DeCandia
Project: Air Partners

Script for importing necessary data for air quality analysis for static reporting.
"""

import sys
import pandas as pd
from calendar import monthrange
import quantaq
from quantaq.utils import to_dataframe
from datetime import datetime
from data_analysis.iem import fetch_data
import data_analysis.quantaq_pipeline as qp
from utils.create_maps import main

with open('token.txt', 'r') as f:
    token = f.read()

client = quantaq.QuantAQAPIClient(token)

class DataImporter(object):
    """
    Imports necessary sensor and wind data for analysis.
    """

    def __init__(self, year, month):
        """
        Args:
            year: (int) year from which data should be imported
            month: (int) month of year from which data should be imported
        """
        self.year = year
        self.month = month

    def get_sensor_list(self):
        """
        Gets the list of sensors currently within Roxbury QuantAQ database.
        """
        devices_raw = to_dataframe(client.devices.list(filter="city,like,%_oxbury%"))
        devices_simplified = devices_raw.iloc[:,[4,3,11,15,16,5,7,8,10,12]]
        return devices_simplified, devices_raw


    def _data_month(self, sensor_sn):
        """
        Downloads data from sensor for a particular month (specified in __init__)

        Args:
            sensor_sn: (str) ID of sensor from which to download data
        """
        # get start and end dates of the month
        start_date, end_date = self._get_start_end_dates(self.year, self.month)
        # instantiate handler used to download data
        mod_handler = qp.ModPMHandler(start_date=start_date, end_date=end_date)

        # Check if pckl file exists, pull data otherwise
        try:
            start_date, end_date = self._get_start_end_dates(self.year, self.month)
            df = mod_handler.load_df(sensor_sn, start_date, end_date)
            print("\r Data pulled from Pickle file", flush=True)
        # Otherwise download it from API
        except:
            try:
                # Pull dataframe from API, will return the dataframe and will also pickle the results for you to open and use later
                df = mod_handler.from_api(sensor_sn)
            except:
                # If there is a request protocol error, create an empty dataframe (temp solution)
                df = pd.DataFrame()
        return df

    def _get_start_end_dates(self, year_int_YYYY, month_int):
        """
        Gets the start and end dates for a given month and year.

        Args:
            year_int_YYYY: (int) the particular year
            month_int: (int) the given month
        """
        # get number of days in month_int of that year
        no_of_days = monthrange(year_int_YYYY, month_int)[1]
        # get start and end dates in type datetime
        start_date = datetime(year_int_YYYY, month_int, 1)
        end_date = datetime(year_int_YYYY, month_int, no_of_days)
        return start_date, end_date

    def get_PM_data(self):
        """
        Downloads the data from all available sensors in the given month and year.
        """
        # Get list of sensors, where this function returns two pandas.DataFrames of the devices
        df_sensor_list, _ = self.get_sensor_list()
        # Simplify output of last function into list of sensors
        sn_list = list(df_sensor_list.sn)
        sn_count = len(sn_list)
        sn_dict = {}

        sensor_count = 1
        # For every sensor, download DataFrame with data of that sensor and insert it into dictionary
        for sn in sn_list:
            # Print out sensor downloading progress
            print('\rSensor Progress: {0} / {1}\n'.format(sensor_count, sn_count), end='', flush=True)
            # If sensor data already exists in pickle file, use that
            df = self._data_month(sn)
            # Add new dataframe to dictionary
            sn_dict[sn] = df
            sensor_count+=1
        print('\nDone!')
        return sn_list, sn_dict


if __name__ == '__main__':
    (year, month) = (sys.argv[1], sys.argv[2])
    di = DataImporter(year=int(year), month=int(month))
    sn_list, sn_dict = di.get_PM_data()
    main(sn_list, sn_dict)