import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from matplotlib.colors import PowerNorm



def plot(df, sensor_id, save_prefix=None, smoothed=True, cols=None):
    plot_path = f"imgs/{sensor_id}"
    Path(plot_path).mkdir(parents=True, exist_ok=True)
    save_prefix = save_prefix if save_prefix else smoothed
    prefix = os.path.join(plot_path, save_prefix)

    cols = cols if cols else df.columns
    non_null_cols = [c for c in cols if not df[c].isnull().all()]

    plt_obj = PolarPlot()
    plt_obj.time_variation(df, prefix, non_null_cols)
    plt_obj.polar_plot(df, prefix, non_null_cols)

class PolarPlot:

    def time_variation(self, df, file_prefix, pollutants):
        for p in pollutants:
            plt.figure(figsize=(12, 7))
            df.groupby(df['timestamp_local'].dt.hour)[p].mean().plot(kind='bar')
            plt.title(f'Normalized {p.upper()} Diurnal Profile')
            plt.xlabel('Hour of Day')
            plt.ylabel(f'{p.upper()} Concentration')
            plt.savefig(f"{file_prefix}_diurnal_{p}.png")
            plt.close()

    def polar_plot(self, df, file_prefix, pollutants):
        for p in pollutants:
            plt.figure(figsize=(7, 7))
            ax = plt.subplot(1, 1, 1, polar=True)
            ax.set_theta_direction(-1)
            ax.set_theta_offset(np.pi/2)
            ax.set_xticks(np.deg2rad(np.arange(0, 360, 45)))
            ax.set_xticklabels(['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'])

            # Convert wind direction to radians
            df['wind_rad'] = np.deg2rad(df['wind_dir'])

            # Contour plot
            levels = np.linspace(df[p].min(), df[p].max(), 1000)
            norm = PowerNorm(gamma=0.6, vmin=df[p].min(), vmax=df[p].max())
            unique_rows = df[['wind_rad', 'wind_speed']].drop_duplicates().shape[0]
            if unique_rows >= 3:
                cntr = ax.tricontourf(df['wind_rad'], df['wind_speed'], df[p], levels=levels, cmap='gist_ncar', alpha=0.9, norm=norm)
                cbar = plt.colorbar(cntr, ax=ax, pad=0.1)
                threshold = df[p].quantile(0.99)

            # Find extreme outliers in the dataset
                outliers = df[df[p] > threshold]

            # Create a scatter plot with outlier points on top of the contour plot
                scatter = ax.scatter(outliers['wind_rad'], outliers['wind_speed'], c=outliers[p], cmap='gist_ncar', alpha=0.7, norm=norm, marker='o', s=120, linewidths=4)

               
            else:
                scatter = ax.scatter(df['wind_rad'], df['wind_speed'], c=df[p], cmap='gist_ncar', alpha=0.75, norm=norm,s=300,linewidths=30)
                cbar = plt.colorbar(scatter, ax=ax, pad=0.1)


            cbar.set_label(f'{p} (ug/m3)')
            num_ticks = 5
            tick_indices = np.linspace(0, len(levels) - 1, num_ticks, dtype=int)
            cbar.set_ticks(levels[tick_indices])
            cbar.set_ticklabels(np.round(levels[tick_indices], 1))
            # Axis labels
            ax.set_yticks(np.unique(df['wind_speed'].round(1)))
            ax.set_yticklabels([f'{s}\nws' if i % 2 == 0 else '' for i, s in enumerate(np.unique(df['wind_speed'].round(1)))])
            ax.set_rlabel_position(135)

            # Add box around boundary
            ax.spines['polar'].set_visible(True)

            plt.title(f'{p.upper()} Wind Plot')

            plt.savefig(f"{file_prefix}_polar_{p}.png")
            plt.close()
