"""
Author: Neel Dhulipala, Alexis (Xinyi) Wu
Project: Air Partners

Prototype of static reporting pipeline. Used primarily for testing scripts (for now).
"""

from calendar import weekday
from .create_plots import *
from multiprocessing import Process



class PlotPipeline():
    def __init__(self, year,month, sn_list, sn_dict):
        self.YEAR = year
        self.MONTH = month
        self.date_str = str(self.YEAR) + '-0' + str(self.MONTH) if self.MONTH <= 9 else str(self.YEAR) + '-' + str(self.MONTH)
        self.sn_list = sn_list
        self.sn_dict = sn_dict
        


    def plot_graphs(self):
        pl = Plotter(self.date_str, self.sn_list, self.sn_dict)
        

        # Define the tasks to be run in parallel
        tasks = [
            lambda: pl.plot_and_export(calendar_plot, pm='pm1', month=self.MONTH, year=self.YEAR),
            lambda: pl.plot_and_export(calendar_plot, pm='pm25', month=self.MONTH, year=self.YEAR),
            lambda: pl.plot_and_export(calendar_plot, pm='pm10', month=self.MONTH, year=self.YEAR),
            lambda: pl.plot_and_export(timeplot_threshold, pm=None),
            lambda: pl.plot_and_export(diurnal_plot, pm='pm1', weekday=True),
            lambda: pl.plot_and_export(diurnal_plot, pm='pm25', weekday=True),
            lambda: pl.plot_and_export(diurnal_plot, pm='pm10', weekday=True),
            lambda: pl.plot_and_export(diurnal_plot, pm='pm1', weekday=False),
            lambda: pl.plot_and_export(diurnal_plot, pm='pm25', weekday=False),
            lambda: pl.plot_and_export(diurnal_plot, pm='pm10', weekday=False),
            lambda: pl.plot_and_export(wind_polar_plot, pm='pm1'),
            lambda: pl.plot_and_export(wind_polar_plot, pm='pm25'),
            lambda: pl.plot_and_export(wind_polar_plot, pm='pm10')
        ]


        # Create and start a process for each task
        processes = []
        for task in tasks:
            p = Process(target=task)
            processes.append(p)
            p.start()

        # Wait for all processes to finish
        for p in processes:
            p.join()

        print('All plots generated.')

    def run(self):
        self.plot_graphs()
