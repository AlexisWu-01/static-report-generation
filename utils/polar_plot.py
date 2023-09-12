import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from matplotlib.colors import PowerNorm
from scipy.interpolate import griddata
from scipy.ndimage import gaussian_filter
from scipy.stats import gaussian_kde
from matplotlib.ticker import FormatStrFormatter
import matplotlib.cm as cm
from windrose import WindroseAxes





class PolarPlot:
    """
    Class to generate polar plots.
    """

    def __init__(self, figsize=(7, 7)):
        self.figsize = figsize

    def polar_plot(self, df, file_prefix, pollutants, dir_bins_count=721, speed_bins_count=1000):
        """
        Generate polar plots for pollutants.

        Parameters:
        - df: DataFrame containing wind data and pollutant values.
        - file_prefix: Prefix for the saved file.
        - pollutants: List of pollutant column names to plot.
        - dir_bins_count: Number of bins for wind direction.
        - speed_bins_count: Number of bins for wind speed.
        """
        if 'wind_dir' not in df.columns or 'wind_speed' not in df.columns:
            raise ValueError("The dataframe must contain 'wind_dir' and 'wind_speed' columns.")

        dir_bins = np.deg2rad(np.linspace(0, 360, dir_bins_count))
        speed_bins = np.linspace(0, df['wind_speed'].max() + 1, speed_bins_count)

        for p in pollutants:
            # self.__generate_plot(df, dir_bins, speed_bins, p, file_prefix)
            self.__generate_plot_pcolormesh(df, dir_bins, speed_bins, p, file_prefix)
            # self.__generate_plot_tricontourf(df, p, file_prefix)

    def __generate_plot_tricontourf(self, df, pollutant, file_prefix):
        fig = plt.figure(figsize=self.figsize)
        ax = plt.subplot(1, 1, 1, polar=True)
        self.__configure_polar_axes(ax)

        valid_data = df.dropna(subset=[pollutant])
        valid_data = valid_data[np.isfinite(valid_data[pollutant])]
        wind_rad = np.deg2rad(valid_data['wind_dir'])
        vmax = valid_data[pollutant].quantile(0.95)
        levels = np.linspace(0, vmax, 100)

        cntr = ax.tricontourf(wind_rad, valid_data['wind_speed'], valid_data[pollutant], levels=levels, cmap='jet', alpha=0.9, extend='max')
        cbar = plt.colorbar(cntr, ax=ax, pad=0.1, shrink=0.5)
        cbar.set_label(f'{pollutant.upper()} Concentration ($\mu g/m^3$)', rotation=270, labelpad=20)
        cbar.ax.tick_params(labelsize=10)  # Adjust font size
        cbar.formatter = FormatStrFormatter('%.1f')  # Format to 2 decimal places
        cbar.update_ticks()
        plt.title(f'{pollutant.upper()} ($\mu g/m^3$)', pad=20)
        plt.savefig(f"{file_prefix}_polar_{pollutant}.png")
        plt.close()

    def __generate_plot_pcolormesh(self, df, dir_bins, speed_bins, pollutant, file_prefix):
        fig = plt.figure(figsize=self.figsize)
        ax = plt.subplot(1, 1, 1, polar=True)
        self.__configure_polar_axes(ax)

        valid_data = df.dropna(subset=[pollutant])
        valid_data = valid_data[np.isfinite(valid_data[pollutant])]
        wind_rad = np.deg2rad(valid_data['wind_dir'])

        grid_dir, grid_speed = np.meshgrid(dir_bins, speed_bins)
        grid_data = griddata((wind_rad, valid_data['wind_speed']), valid_data[pollutant], (grid_dir, grid_speed), method='cubic')
        vmax = valid_data[pollutant].quantile(0.95)  # 95% quantile for the color scale
        grid_data = gaussian_filter(grid_data, sigma=1.0)

        mesh = ax.pcolormesh(grid_dir, grid_speed, grid_data, cmap='jet', shading='auto',vmin=0, vmax=vmax)
        cbar = plt.colorbar(mesh, ax=ax, pad=0.1, shrink=0.5)
        cbar.set_label(f'{pollutant.upper()} Concentration ($\mu g/m^3$)', rotation=270, labelpad=20)
        cbar.ax.tick_params(labelsize=10)
        cbar.formatter = FormatStrFormatter('%.1f')
        cbar.update_ticks()
        plt.tight_layout()
        plt.title(f'{pollutant.upper()} ($\mu g/m^3$)', pad=20, fontsize=16, fontweight='bold')
        plt.savefig(f"{file_prefix}_polar_{pollutant}.png")
        plt.close()


    def __generate_plot(self, df, dir_bins, speed_bins, pollutant, file_prefix):
        fig = plt.figure(figsize=self.figsize)
        ax = plt.subplot(1, 1, 1, polar=True)
        self.__configure_polar_axes(ax)

        valid_data = df.dropna(subset=[pollutant])
        valid_data = valid_data[np.isfinite(valid_data[pollutant])]
        wind_rad = np.deg2rad(valid_data['wind_dir'])
        vmax = valid_data[pollutant].quantile(0.95)
        levels = np.linspace(0, vmax, 100)

        grid_dir, grid_speed = np.meshgrid(dir_bins, speed_bins)
        grid_data = griddata((wind_rad, valid_data['wind_speed']), valid_data[pollutant], (grid_dir, grid_speed), method='cubic')
        
        # for _ in range(3):
        #     grid_data = gaussian_filter(grid_data, sigma=1.0)

        cntr = ax.contourf(grid_dir, grid_speed, grid_data, levels=levels, cmap='jet', alpha=0.9, extend='max')
        cbar = plt.colorbar(cntr, ax=ax, pad=0.1, shrink=0.5)
        cbar.set_label(f'{pollutant.upper()} Concentration ($\mu g/m^3$)', rotation=270, labelpad=20)
        cbar.ax.tick_params(labelsize=10)  # Adjust font size
        cbar.formatter = FormatStrFormatter('%.1f')  # Format to 2 decimal places
        cbar.update_ticks()
        plt.title(f'{pollutant.upper()} ($\mu g/m^3$)', pad=20)
        plt.savefig(f"{file_prefix}_polar_{pollutant}.png")
        plt.close()

    def __configure_polar_axes(self, ax):
        ax.set_theta_direction(-1)
        ax.set_theta_offset(np.pi/2)
        ax.set_xticks(np.deg2rad(np.arange(0, 360, 45)))
        ax.set_xticklabels(['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'])
        ax.spines['polar'].set_visible(True)
