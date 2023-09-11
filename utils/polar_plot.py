import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from matplotlib.colors import PowerNorm
from scipy.interpolate import griddata
from scipy.ndimage import gaussian_filter




def plot(df, sensor_id, save_prefix=None, smoothed=True, cols=None):
    """
    Plot data for the given sensor ID.
    """
    plot_path = f"imgs/{sensor_id}"
    Path(plot_path).mkdir(parents=True, exist_ok=True)
    save_prefix = save_prefix if save_prefix else smoothed
    prefix = os.path.join(plot_path, save_prefix)

    cols = cols if cols else df.columns
    non_null_cols = [c for c in cols if not df[c].isnull().all()]

    plt_obj = PolarPlot()
    plt_obj.time_variation(df, prefix, non_null_cols)
    plt_obj.wind_rose_plot(df, prefix, non_null_cols)


class PolarPlot:
    """
    Class to generate polar plots.
    """

    def time_variation(self, df, file_prefix, pollutants, figsize=(12, 7)):
        """
        Plot time variation for pollutants.
        """
        for p in pollutants:
            plt.figure(figsize=figsize)
            df.groupby(df['timestamp_local'].dt.hour)[p].mean().plot(kind='bar')
            plt.title(f'Normalized {p.upper()} Diurnal Profile')
            plt.xlabel('Hour of Day')
            plt.ylabel(f'{p.upper()} Concentration')
            plt.savefig(f"{file_prefix}_diurnal_{p}.png")
            plt.close()


    def polar_plot(self, df, file_prefix, pollutants, figsize=(7, 7)):
        """
        Generate polar plots for pollutants.
        """
        if 'wind_dir' not in df.columns:
            raise ValueError("The dataframe must contain a 'wind_dir' column.")

        # Convert wind direction to radians
        df['wind_rad'] = np.deg2rad(df['wind_dir'])

        # Define bins for wind direction and speed
        dir_bins = np.deg2rad(np.arange(0, 361, 10))
        speed_bins = np.arange(0, df['wind_speed'].max() + 1, 1)

        for p in pollutants:
            plt.figure(figsize=figsize)
            ax = plt.subplot(1, 1, 1, polar=True)
            self._configure_polar_axes(ax)
            valid_data = df.dropna(subset=[p])
            valid_data = valid_data[np.isfinite(valid_data[p])]

            dir_idx = np.digitize(valid_data['wind_rad'], dir_bins)
            speed_idx = np.digitize(valid_data['wind_speed'], speed_bins)
            binned_data = valid_data.groupby([dir_idx, speed_idx])[p].mean().reset_index()

            binned_data['wind_rad'] = dir_bins[binned_data.iloc[:, 0].values - 1]
            binned_data['wind_speed'] = speed_bins[binned_data.iloc[:, 1].values - 1]

            # Interpolate to create a continuous field
            grid_dir, grid_speed = np.meshgrid(dir_bins, speed_bins)
            grid_data = griddata((binned_data['wind_rad'], binned_data['wind_speed']), binned_data[p], (grid_dir, grid_speed), method='cubic')
            grid_data = np.nan_to_num(grid_data, nan=np.nanmin(grid_data), posinf=np.nanmax(grid_data), neginf=np.nanmin(grid_data))
            threshold = df[p].min() + 0.01 * (df[p].max() - df[p].min())
            grid_data = gaussian_filter(grid_data, sigma=1.5)
            grid_data[grid_data < threshold] = np.nan

            
            # Plot
            levels = np.linspace(np.nanmin(grid_data), np.nanmax(grid_data), 100)
            cntr = ax.contourf(grid_dir, grid_speed, grid_data, levels=levels,cmap='gist_ncar', alpha=0.9)
            cbar = plt.colorbar(cntr, ax=ax, pad=0.1)
            plt.title(f'{p.upper()} Wind Plot')
            plt.savefig(f"{file_prefix}_polar_{p}.png")
            plt.close()


    def _configure_polar_axes(self, ax):
        """
        Configure polar axes settings.
        """
        ax.set_theta_direction(-1)
        ax.set_theta_offset(np.pi/2)
        ax.set_xticks(np.deg2rad(np.arange(0, 360, 45)))
        ax.set_xticklabels(['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'])
        ax.spines['polar'].set_visible(True)

    def _get_levels_and_norm(self, df, p):
        """
        Get levels and normalization for contour plots.
        """
        levels = np.linspace(df[p].min(), df[p].max(), 1000)
        norm = PowerNorm(gamma=0.6, vmin=df[p].min(), vmax=df[p].max())
        return levels, norm

    def _configure_colorbar(self, cbar, levels, p):
        """
        Configure colorbar settings.
        """
        cbar.set_label(f'{p} (ug/m3)')
        num_ticks = 5
        tick_indices = np.linspace(0, len(levels) - 1, num_ticks, dtype=int)
        cbar.set_ticks(levels[tick_indices])
        cbar.set_ticklabels(np.round(levels[tick_indices], 1))
