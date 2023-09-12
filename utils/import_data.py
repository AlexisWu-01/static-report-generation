"""
Author: Andrew DeCandia, Neel Dhulipala
Project: Air Partners

Script for importing necessary data for air quality analysis for static reporting.
"""
import sys
import pandas as pd
from quantaq import QuantAQAPIClient
from quantaq.utils import to_dataframe
from datetime import datetime
from . import quantaq_pipeline as qp
from .pull_from_drive import pull_sensor_install_data
from .create_maps import main
import concurrent.futures



TOKEN_FILE = 'creds/quantaq_token.txt'
SENSOR_INSTALL_DATA_FILE = 'google_drive/sensor_install_data.csv'
CITY_FILTER = "city,like,%_oxbury%"


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
        with open(TOKEN_FILE,'r') as f:
            self.client = QuantAQAPIClient(f.read().strip())


    def get_all_sensor_list(self):
        """
        Gets the list of sensors currently within Roxbury QuantAQ database.
        Retrieves a list of sensor names from QuantAQ API.

        :returns: A filtered list of sensor information
        :returns: A list of all sensor information
        """
        devices_raw = to_dataframe(
            self.client.devices.list(filter=CITY_FILTER))
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
            df = pd.read_csv(SENSOR_INSTALL_DATA_FILE)
            df = df.rename(columns={
                'Sensor serial number (SN)': 'sn',
                'Select action': 'action',
                'Is the sensor being installed indoors or outdoors?': 'indoors_outdoors'
            })
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

        active_sensors = [row.sn for row in df.itertuples() if row.action == 'installation' and pd.to_datetime(row.Date) < end_date and row.indoors_outdoors == 'Outdoors']
        return active_sensors

    # def adjust_timezone(self, df, timestamp_col="timestamp"):
    #     """
    #     Adjusts the timezone of the timestamp column in the dataframe.

    #     :param df: (DataFrame) the dataframe containing meteorological data
    #     :param timestamp_col: (str) the name of the timestamp column
    #     :returns: DataFrame with adjusted timezone
    #     """
    #     # Ensure the timestamp column is in datetime format
    #     df[timestamp_col] = pd.to_datetime(df[timestamp_col])

    #     # Set the timezone to UTC and then convert to America/New_York
    #     df[timestamp_col] = df[timestamp_col].dt.tz_localize('UTC').dt.tz_convert('America/New_York')

    #     return df

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
            print(f"{sensor_sn}: Loaded from pickle file")
        except:
            try:
                # Pull dataframe from API, will return the dataframe and save it as a pickle file
                df = mod_handler.from_api(sensor_sn)
                print(f"{sensor_sn}: Pulled from API")
            except:
                # If there is a request protocol error, return an empty dataframe (temp solution)
                return pd.DataFrame()

        # If dataframe comes back empty, return it
        if df.empty:
            return df

        # Only get rows of the DataFrame between the installation and removal dates of the sensor
        install_df = self._get_install_data().loc[self._get_install_data()['sn'] == sensor_sn]

        # Create a mask for each installation and removal date of the sensor
        mask = pd.Series(False, index=df.index)
        for row in install_df.itertuples():
            when = pd.to_datetime(f"{row.Date} {row.Time}")
            if start_date <= when <= end_date:
                if row.action == 'installation':
                    mask |= (df['timestamp'] > when)
                elif row.action == 'removal':
                    mask |= (df['timestamp'] < when)
            elif when < start_date and row.action == 'installation':
                mask |= (df['timestamp'] > when)

        # Filter the DataFrame based on the created mask
        # df = self.adjust_timezone(df)
        filtered_df = df.loc[mask]
        return filtered_df

    def _get_start_end_dates(self, year_int_YYYY, month_int):
        """
        Creates datetime objects for the start and end of the specified month.

        :param year_int_YYYY: (int) The year
        :param month_int: (int) The month

        :returns: DateTime object for the first day of the month
        :returns: DateTime object for the last day of the month
        """
        # get next month
        next_month = self.month + 1 if self.month != 12 else 1
        next_year = self.year if next_month != 1 else self.year + 1
        start_date = datetime(self.year, self.month, 1)
        end_date = datetime(next_year, next_month, 1)
        return start_date, end_date

    def _data_month_worker(self, sn):
        """
        Worker function to be used with ThreadPoolExecutor.
        """
        print(f'\rFetching data for sensor: {sn} \n', end='', flush=True)
        # print(f"sn: {sn}")
        # print(f"self._data_month(sn): {self._data_month(sn)}")
        return sn, self._data_month(sn)

    def get_PM_data(self):
        """
        Collects data from all sensors for the month.

        :returns: A list of all sensors available from QuantAQ API
        :returns: A dictionary of sensor serial number keys and pandas dataframes containing sensor data
        """
        # try to get installed sensor list; if there are no credentials, get all sensors
        try:
            sn_list = self.get_installed_sensor_list()
        except Exception as e:
            print(f"Error fetching installed sensor list: {e}")
            sn_list, _ = self.get_all_sensor_list()
            sn_list = self.get_all_sensor_list()
        sn_dict = {}
   
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = list(executor.map(self._data_month_worker, sn_list))
        sn_list = []
        for sn, df in results:
            if not df.empty:
                sn_dict[sn] = df
                sn_list.append(sn)

        print('\nDone!')
        # print(f"sn_list: {sn_list}")
        # print(f"sn_dict: {sn_dict}")
        return sn_list, sn_dict

if __name__ == '__main__':
    (year, month) = (sys.argv[1], sys.argv[2])
    di = DataImporter(year=int(year), month=int(month))
    sn_list, sn_dict = di.get_PM_data()
    main(sn_list, sn_dict)
