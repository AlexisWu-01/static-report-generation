"""
Author: Neel Dhulipala
Project: Air Partners

Prototype of static reporting pipeline. Used primarily for testing scripts (for now).
"""

from data_import import DataImporter
from create_plots import *
from report_generation import generate_report

# STATICS (for testing)
YEAR = 2022
MONTH = 4

# import sensor data
di = DataImporter(year=YEAR, month=MONTH)
sn_list, sn_dict = di.get_PM_data()
iem_df = di.get_iem_data()

# create date string for data storage
date_str = str(YEAR) + '-0' + str(MONTH) if MONTH<=9 else str(YEAR) + '-' + str(MONTH)

# plot graphs
pl = Plotter(date_str, sn_list, sn_dict)

# calendar plots
pl.plot_and_export(calendar_plot, month=MONTH, year=YEAR)
print('Calendars plotted')

# timeplots with thresholds
pl.plot_and_export(timeplot_threshold)
print('Timelines plotted')

# time of day plots
pl.plot_and_export(time_of_day_plot)
print('Time of day plotted')

# daily average plots
pl.plot_and_export(daily_average_plot)
print('Daily averages plotted')

# wind polar plots
pl.plot_and_export(wind_polar_plot, month=MONTH, iem_df=iem_df)
print('Wind polar plots plotted')

# generate reports for each sensor
for sn in sn_list:
    if not sn_dict[sn].empty:
        generate_report(MONTH, YEAR, sn)
        print(f"Finished report {sn}.")
