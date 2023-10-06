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
from sklearn.neighbors import KernelDensity
from matplotlib.colors import ListedColormap
from matplotlib.ticker import FormatStrFormatter
from scipy.interpolate import Rbf
from pygam import LinearGAM, s



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

        # aggregated = self.aggregate_data(df)


        for p in pollutants:
            self.__generate_plot(df, p, file_prefix)
            # self.__generate_plot_pcolormesh(df, dir_bins, speed_bins, p, file_prefix)
            # self.__generate_plot_tricontourf(df, p, file_prefix)

    def aggregate_data(self, df):
        # Assuming wind direction is in degrees and wind speed is numerical
        df['wind_dir_bin'] = pd.cut(df['wind_dir'], bins=np.linspace(0, 360, 10), include_lowest=True)
        df['wind_speed_bin'] = pd.cut(df['wind_speed'], bins=np.linspace(0, df['wind_speed'].max() + 1, 21), include_lowest=True)
        aggregated = df.groupby(['wind_dir_bin', 'wind_speed_bin']).mean().reset_index()
        aggregated['wind_dir_bin_mid'] = aggregated['wind_dir_bin'].apply(lambda x: x.mid)
        aggregated['wind_speed_bin_mid'] = aggregated['wind_speed_bin'].apply(lambda x: x.mid)
        return aggregated

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

    
    def __generate_plot(self, df, pollutant, file_prefix):
        fig = plt.figure(figsize=self.figsize)
        ax = plt.subplot(1, 1, 1, polar=True)
        self.__configure_polar_axes(ax)
        df = df.dropna(subset=['wind_dir', 'wind_speed'])

        bin_edges = np.linspace(0, 360, 9, endpoint=True)  # This creates 8 bins of 45 degrees each
        df = df.dropna(subset=['wind_dir', 'wind_speed', pollutant])
        df['wind_dir'] = df['wind_dir'] % 360  # Ensures wind_dir values are within [0, 360)
        df['wind_dir_bin'] = pd.cut(df['wind_dir'], bins=np.concatenate(([0], bin_edges + 45)), include_lowest=True, right=False)
        df['wind_speed_bin'] = pd.cut(df['wind_speed'], bins=np.linspace(0, df['wind_speed'].max() + 1, 100), include_lowest=True)
        #aggregating pollutant concentration
        binned_data = df.groupby(['wind_dir_bin', 'wind_speed_bin'],observed=False)[pollutant].mean().reset_index()

        binned_data['wind_dir_midpoint_rad'] = np.deg2rad(binned_data['wind_dir_bin'].apply(lambda x: x.mid).astype(float))  # Converted to radians
        binned_data['wind_speed_midpoint'] = binned_data['wind_speed_bin'].apply(lambda x: x.mid).astype(float)
        nan_rows = binned_data[pollutant].isna()
        inf_rows = np.isinf(binned_data[pollutant])
        invalid_rows = nan_rows | inf_rows
        binned_data = binned_data[~invalid_rows]


        # Modelling with GAM
        gam = LinearGAM(s(0,basis='cp') + s(1)).fit(binned_data[['wind_dir_midpoint_rad', 'wind_speed_midpoint']], np.sqrt(binned_data[pollutant]))
        #cartesian grid
        theta_grid, r_grid = np.meshgrid(
                            np.deg2rad(np.linspace(0, 360, 100)),
                            np.linspace(binned_data['wind_speed_midpoint'].min(), binned_data['wind_speed_midpoint'].max(), 200))
        
        predicted_concentration = gam.predict(np.column_stack((theta_grid.ravel(), r_grid.ravel()))).reshape(theta_grid.shape)
        invalid_mask =  np.isnan(predicted_concentration) | np.isinf(predicted_concentration)
        predicted_concentration = np.ma.masked_where(invalid_mask, predicted_concentration)
        levels = np.linspace(np.min(predicted_concentration), np.max(predicted_concentration), 100)
        contour = ax.contourf(theta_grid, r_grid, predicted_concentration, levels = levels, cmap='jet')
        cbar = plt.colorbar(contour, ax=ax, pad=0.1, shrink=0.5)
        cbar.set_label(f'{pollutant.upper()} Concentration ($\mu g/m^3$)', rotation=270, labelpad=20)
        cbar.ax.tick_params(labelsize=10)
        cbar.formatter = FormatStrFormatter('%.1f')
        cbar.update_ticks()
        plt.tight_layout()
        plt.title(f'{pollutant.upper()} ($\mu g/m^3$)', pad=20, fontsize=16, fontweight='bold')
        plt.savefig(f"{file_prefix}_polar_{pollutant}.png")
        plt.close()

    def __configure_polar_axes(self, ax):
        ax.set_theta_direction(-1)
        ax.set_theta_offset(np.pi/2)
        ax.set_xticks(np.deg2rad(np.arange(0, 360, 45)))
        ax.set_xticklabels(['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'])
        ax.spines['polar'].set_visible(True)
