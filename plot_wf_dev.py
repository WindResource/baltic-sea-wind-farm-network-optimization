import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import make_interp_spline

def plot_capacity_development():
    # Data points
    years = [2023, 2030, 2040, 2050]
    min_capacity = [19.38, 109, 215, 281]
    max_capacity = [19.38, 112, 248, 354]
    avg_capacity = [19.38, (109+112)/2, (215+248)/2, (281+354)/2]

    # Interpolation for smooth curve
    years_smooth = np.linspace(2023, 2050, 300)
    spl = make_interp_spline(years, avg_capacity, k=3)
    capacity_smooth = spl(years_smooth)

    # Plotting
    plt.figure(figsize=(6, 4))
    plt.plot(years_smooth, capacity_smooth, label='Average Capacity', color='green')
    plt.errorbar(years, avg_capacity, yerr=[np.array(avg_capacity)-np.array(min_capacity), np.array(max_capacity)-np.array(avg_capacity)], 
                fmt='o', color='green', ecolor='darkgreen', capsize=5, label='Min-Max Range')

    plt.fill_between(years, min_capacity, max_capacity, color='lightgreen', alpha=0.2, label='Capacity Range')

    plt.xlabel('Year')
    plt.ylabel('Capacity (GW)')
    plt.xlim(2020, 2055)
    plt.ylim(0, 360)
    plt.legend(loc='upper left', bbox_to_anchor=(0, 1.25), ncol=1, frameon=False)
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.minorticks_on()
    plt.show()

def plot_percentage_development():
    # Data points
    years = [2023, 2030, 2040, 2050]
    avg_capacity = [19.38, (109+112)/2, (215+248)/2, (281+354)/2]
    
    # Calculate percentage of development
    base_capacity = avg_capacity[0]
    max_capacity = avg_capacity[-1]
    percentages = [(cap - base_capacity) / (max_capacity - base_capacity) * 100 for cap in avg_capacity]

    # Interpolation for smooth curve
    years_smooth = np.linspace(2023, 2050, 300)
    spl = make_interp_spline(years, percentages, k=3)
    percentages_smooth = spl(years_smooth)

    # Plotting
    plt.figure(figsize=(6, 4))
    plt.plot(years_smooth, percentages_smooth, label='Future Development', color='green')
    plt.scatter(years, percentages, color='green')

    # Add values to the points
    for i, txt in enumerate(percentages):
        plt.annotate(f'{txt:.0f}%', (years[i], percentages[i]), textcoords="offset points", xytext=(0,10), ha='center', fontsize=10, color='black')

    plt.xlabel('Year')
    plt.ylabel('Development (%)')
    plt.xlim(2020, 2055)
    plt.ylim(-10, 110)
    plt.legend(loc='upper left', bbox_to_anchor=(0, 1.15), ncol=1, frameon=False)
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.minorticks_on()
    plt.show()

# Call the function to plot
plot_capacity_development()

# Call the function to plot
plot_percentage_development()