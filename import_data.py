"""
Author: Andrew DeCandia, Neel Dhulipala
Project: Air Partners

Script for importing necessary data for air quality analysis for static reporting.
"""
import sys
import pandas as pd
from calendar import monthrange
import quantaq
from quantaq.utils import to_dataframe
from datetime import datetime
import data_analysis.quantaq_pipeline as qp
from pull_from_drive import pull_sensor_install_data
from utils.create_maps import main

with open('quantaq_token.txt', 'r') as f:
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
        self.install_data = None  # initialize to None


    def get_all_sensor_list(self):
        """
        Gets the list of sensors currently within Roxbury QuantAQ database.
        Retrieves a list of sensor names from QuantAQ API.

        :returns: A filtered list of sensor information
        :returns: A list of all sensor information
        """
        devices_raw = to_dataframe(
            client.devices.list(filter="city,like,%_oxbury%"))
        devices_simplified = devices_raw.iloc[:, [
            4, 3, 11, 15, 16, 5, 7, 8, 10, 12]]
        
        return devices_simplified, devices_raw

    def _get_install_data(self):
        """
        Pull sensor installation notes from google drive and modifies dataframe for ease of use.

        :returns: a dataframe of sensor install data
        """
        if self.install_data is None:
            pull_sensor_install_data()
            df = pd.read_csv('sensor_install_data.csv')
            print(df)
            df = df[["Timestamp", "Select action", "Sensor serial number (SN)", "Date", "Time",
                 "Location site", "Is the sensor being installed indoors or outdoors?"]]

            df = df.rename(columns={'Sensor serial number (SN)': 'sn',
                                'Select action': 'action',
                                'Is the sensor being installed indoors or outdoors?': 'indoors_outdoors'}
                                )
            df['action'] = df['action'].str.extract(r'sensor (.*)$')

            self.install_data = df

        return self.install_data

    def get_installed_sensor_list(self):
        """
        Pull sensor installation notes from google drive and create list of all sensors with data for the given month.

        :returns: a list of serial numbers for all sensors that were installed that month
        """
        start_date, end_date = self._get_start_end_dates(self.year, self.month)

        df = self._get_install_data()

        active_sensors = []

        for row in df.itertuples():
            if (row.sn not in active_sensors and row.action == 'installation' and pd.to_datetime(row.Date) < end_date
                    and row.indoors_outdoors == 'Outdoors'):
                active_sensors.append(row.sn)
            elif (row.sn in active_sensors and row.action == 'removal' and pd.to_datetime(row.Date) < start_date):
                active_sensors.remove(row.sn)

        return active_sensors

    def _data_month(self, sensor_sn):
        """
        Gets data for a specific sensor.
        If data doesn't already exist in a pickle file, data is pulled from QuantAQ API.

        :param sensor_sn: (str) The serial number of the sensor to pull data for
        :returns: A pandas dataframe containing all of the sensor data for the month
        """
        start_date, end_date = self._get_start_end_dates(self.year, self.month)
        # instantiate handler used to download data
        mod_handler = qp.ModPMHandler(start_date=start_date, end_date=end_date)

        try:
            # Try to load data from a pickle file first
            df = mod_handler.load_df(sensor_sn, start_date, end_date)
            print("\r Data pulled from Pickle file", flush=True)
        except:
            try:
                # Pull dataframe from API, will return the dataframe and save it as a pickle file
                df = mod_handler.from_api(sensor_sn)
            except:
                # If there is a request protocol error, return an empty dataframe (temp solution)
                return pd.DataFrame()

        # If dataframe comes back empty, return it
        if df.empty:
            print(f"{sensor_sn}: Empty dataframe returned")
            return df

        # Only get rows of the DataFrame between the installation and removal dates of the sensor
        install_df = self._get_install_data()
        install_df = install_df.loc[install_df['sn'] == sensor_sn]\
        # Create a mask for each installation and removal date of the sensor
        mask = pd.Series(False, index=df.index)
        for row in install_df.itertuples():
            when = pd.to_datetime(row.Date + ' ' + row.Time)
            if when > start_date and when < end_date:
                if row.action == 'installation':
                    mask |= (df['timestamp'] > when)
                elif row.action == 'removal':
                    mask |= (df['timestamp'] < when)
        # Filter the DataFrame based on the created mask
        df = df.loc[mask]

        return df

    def _get_start_end_dates(self, year_int_YYYY, month_int):
        """
        Creates datetime objects for the start and end of the specified month.

        :param year_int_YYYY: (int) The year
        :param month_int: (int) The month

        :returns: DateTime object for the first day of the month
        :returns: DateTime object for the last day of the month
        """
        # get next month
        next_month = month_int+1 if month_int!=12 else 1
        # get next year
        next_year = year_int_YYYY if next_month!=1 else year_int_YYYY+1
        # get start and end dates in type datetime
        start_date = datetime(year_int_YYYY, month_int, 1)
        # end date defined as first day of next month since the cutoff for
        # downloading data from API is midnight of that day, which means all
        # of the last day of the previous month gets included
        end_date = datetime(next_year, next_month, 1)
        return start_date, end_date

    def get_PM_data(self):
        """
        Collects data from all sensors for the month.

        :returns: A list of all sensors available from QuantAQ API
        :returns: A dictionary of sensor serial number keys and pandas dataframes containing sensor data
        """
        # try to get installed sensor list; if there are no credentials, get all sensors
        try:
            sn_list = self.get_installed_sensor_list()
        except:
            sn_list = self.get_all_sensor_list()
        sn_dict = {}

        #  modify to meet manny's need
        sn_count = len(sn_list)

        sensor_count = 1
        # For every sensor, download DataFrame with data of that sensor and insert it into dictionary
        for sn in sn_list:
            # Print out sensor downloading progress
            print(
                '\rSensor Progress: {0} / {1}\n'.format(sensor_count, sn_count), end='', flush=True)
            # If sensor data already exists in pickle file, use that
            df = self._data_month(sn)
            print('checking data')
            # print(df)
            # Add new dataframe to dictionary
            sn_dict[sn] = df
            sensor_count += 1
        print('\nDone!')
        
        return sn_list, sn_dict


if __name__ == '__main__':
    (year, month) = (sys.argv[1], sys.argv[2])
    di = DataImporter(year=int(year), month=int(month))
    sn_list, sn_dict = di.get_PM_data()
    print(sn_list, sn_dict)
    main(sn_list, sn_dict)
