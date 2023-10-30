import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
from pygam import LinearGAM, s,te



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

    
    def __generate_plot(self, df, pollutant, file_prefix):
        fig = plt.figure(figsize=self.figsize)
        ax = plt.subplot(1, 1, 1, polar=True)
        self.__configure_polar_axes(ax)
        df = df.dropna(subset=['wind_dir', 'wind_speed'])

        bin_edges = np.arange(0, 370, 10)  # This creates 36 bins of 10 degrees each
        df = df.dropna(subset=['wind_dir', 'wind_speed', pollutant])
        df['wind_dir'] = df['wind_dir'] % 360  # Ensures wind_dir values are within [0, 360)
        df['wind_dir_bin'] = pd.cut(df['wind_dir'], bins=bin_edges, include_lowest=True, right=False)
        df['wind_speed_bin'] = pd.cut(df['wind_speed'], bins=np.arange(0, df['wind_speed'].max() + 1, 0.1), include_lowest=True)
        #aggregating pollutant concentration
        binned_data = df.groupby(['wind_dir_bin', 'wind_speed_bin'],observed=False)[pollutant].mean().reset_index()

        binned_data['wind_dir_midpoint_rad'] = np.deg2rad(binned_data['wind_dir_bin'].apply(lambda x: x.mid).astype(float))  # Converted to radians
        binned_data['wind_speed_midpoint'] = binned_data['wind_speed_bin'].apply(lambda x: x.mid).astype(float)

        nan_rows = binned_data[pollutant].isna()
        inf_rows = np.isinf(binned_data[pollutant])
        invalid_rows = nan_rows | inf_rows
        binned_data = binned_data[~invalid_rows]


        # Modelling with GAM
        
        # gam = LinearGAM(s(0,basis='cp') + s(1)).fit(binned_data[['wind_dir_midpoint_rad', 'wind_speed_midpoint']], (binned_data[pollutant]))
        gam = LinearGAM(te(0, 1, lam=0.5, n_splines=[25, 20],basis=['cp', 'ps'])).fit(binned_data[['wind_dir_midpoint_rad', 'wind_speed_midpoint']], binned_data[pollutant])

        #cartesian grids
        theta_grid, r_grid = np.meshgrid(
                            np.deg2rad(np.linspace(0, 360, 100)),
                            np.linspace(binned_data['wind_speed_midpoint'].min(), binned_data['wind_speed_midpoint'].max(), 200))
        
        predicted_concentration = gam.predict(np.column_stack((theta_grid.ravel(), r_grid.ravel()))).reshape(theta_grid.shape)
        invalid_mask =  np.isnan(predicted_concentration) | np.isinf(predicted_concentration)
        predicted_concentration = np.ma.masked_where(invalid_mask, predicted_concentration)
        levels = np.linspace(np.min(predicted_concentration), np.max(predicted_concentration), 1000)
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
