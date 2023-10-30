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
        gam = LinearGAM(te(0, 1, lam=0.3, n_splines=[20, 15],basis=['cp', 'ps'])).fit(binned_data[['wind_dir_midpoint_rad', 'wind_speed_midpoint']], binned_data[pollutant])

        #cartesian grids
        theta_grid, r_grid = np.meshgrid(
                            np.deg2rad(np.linspace(0, 360, 500)),
                            np.linspace(binned_data['wind_speed_midpoint'].min(), binned_data['wind_speed_midpoint'].max(), 500))
        
        predicted_concentration = gam.predict(np.column_stack((theta_grid.ravel(), r_grid.ravel()))).reshape(theta_grid.shape)
        
        # Assuming `binned_data_mask` is a boolean mask indicating where data exists
        radius = 1.5  # adjust this value based on your data's scale

        # Create an empty mask with the same dimensions as the grid
        binned_data_mask = np.zeros(theta_grid.shape, dtype=bool)

        # Iterate through binned_data and mark the corresponding grid cells in the mask
        for index, row in binned_data.iterrows():
            theta, r = row['wind_dir_midpoint_rad'], row['wind_speed_midpoint']
            
            # Compute the squared distance from each grid cell to the data point
            distance_squared = ((theta_grid - theta) * r)**2 + (r_grid - r)**2
            
            # Update the binned_data_mask for cells that fall within the defined radius
            binned_data_mask |= (distance_squared < radius**2)
        
        predicted_concentration = np.ma.masked_where(~binned_data_mask, predicted_concentration)
        levels = np.linspace(np.min(predicted_concentration), np.max(predicted_concentration), 50)
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
