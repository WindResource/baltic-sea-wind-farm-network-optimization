import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, FuncFormatter

from scripts.present_value import present_value
from scripts.iac_cost import iac_cost_ceil
from scripts.colors import cost_colors


# Define font parameters
font = {'family': 'serif',
        'weight': 'normal',
        'size': 12}

# Set font
plt.rc('font', **font)


def calc_total_cost_iac(distance, capacity):
    
    first_year = 2040
    
    equip_cost, inst_cost = iac_cost_ceil(distance, capacity)
    
    ope_cost_yearly = 0.002 * equip_cost
    
    deco_cost = 0.5 * inst_cost

    # Calculate present value
    total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost = present_value(first_year, equip_cost, inst_cost, ope_cost_yearly, deco_cost)
    
    return total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost

def plot_costs_vs_distance():
    capacity = 120  # MW
    distances = np.linspace(0, 1.5, 100)  # Distances in km

    total_costs, equip_costs, inst_costs, total_ope_costs, deco_costs = [], [], [], [], []

    for distance in distances:
        total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost = calc_total_cost_iac(distance * 1e3, capacity)
        total_costs.append(total_cost)
        equip_costs.append(equip_cost)
        inst_costs.append(inst_cost)
        total_ope_costs.append(total_ope_cost)
        deco_costs.append(deco_cost)

    fig, axs = plt.subplots(2, 1, figsize=(6, 6), gridspec_kw={'height_ratios': [4, 1]}, sharex=True)

    # Get the color mapping
    colors = cost_colors()

    # Define custom formatting functions for this figure
    def format_x_axis_distance(value, tick_position):
        return f'{value:.2f}' if value != 0 else '0'  # 2 decimal places for x-axis

    def format_y_axis_distance(value, tick_position):
        return f'{value:.3f}' if value != 0 else '0'  # 3 decimal places for y-axis

    # Plotting the larger range
    axs[0].plot(distances, total_costs, label='Total Cost', color=colors['Total Cost'])
    axs[0].plot(distances, equip_costs, label='Equipment Cost', color=colors['Equipment Cost'])
    axs[0].plot(distances, inst_costs, label='Installation Cost', color=colors['Installation Cost'])
    axs[0].plot(distances, total_ope_costs, label='Operating Cost', color=colors['Operating Cost'])
    axs[0].plot(distances, deco_costs, label='Decommissioning Cost', color=colors['Decommissioning Cost'])

    axs[0].set_xlim(0, 1.5)
    axs[0].set_ylim(0, 0.5)
    axs[0].yaxis.set_major_locator(MultipleLocator(0.5 / 4))
    axs[0].yaxis.set_minor_locator(MultipleLocator(0.5 / 4 / 4))
    axs[0].yaxis.set_major_formatter(FuncFormatter(format_y_axis_distance))
    axs[0].xaxis.set_major_formatter(FuncFormatter(format_x_axis_distance))

    # Plotting the smaller range
    axs[1].plot(distances, total_costs, label='Total Cost', color=colors['Total Cost'])
    axs[1].plot(distances, equip_costs, label='Equipment Cost', color=colors['Equipment Cost'])
    axs[1].plot(distances, inst_costs, label='Installation Cost', color=colors['Installation Cost'])
    axs[1].plot(distances, total_ope_costs, label='Operating Cost', color=colors['Operating Cost'])
    axs[1].plot(distances, deco_costs, label='Decommissioning Cost', color=colors['Decommissioning Cost'])

    axs[1].set_xlim(0, 1.5)
    axs[1].set_ylim(0, 0.025)
    axs[1].yaxis.set_major_locator(MultipleLocator(0.025))
    axs[1].yaxis.set_minor_locator(MultipleLocator(0.025 / 4))
    axs[1].yaxis.set_major_formatter(FuncFormatter(format_y_axis_distance))
    axs[1].xaxis.set_major_formatter(FuncFormatter(format_x_axis_distance))

    for ax in axs:
        ax.xaxis.set_major_locator(MultipleLocator(0.25))
        ax.xaxis.set_minor_locator(MultipleLocator(0.0625))
        ax.grid(which='major', linestyle='-', linewidth='0.5', color='gray')
        ax.grid(which='minor', linestyle=':', linewidth='0.5', color='gray')
    
    # axs[0].text(axs[0].get_xlim()[1] * 0.02, axs[0].get_ylim()[1] * 0.98, f'$P_{{iac}} ={capacity}$ MW', ha='left', va='top', fontsize=11)
    
    axs[1].set_xlabel('Distance (km)')
    axs[0].set_ylabel('Cost (M€)')
    axs[1].set_ylabel('Cost (M€)')

    # Get legend handles and labels
    lines, labels = axs[0].get_legend_handles_labels()
    
    # Specify the desired order of labels
    desired_order = ['Total Cost', 'Equipment Cost', 'Operating Cost', 'Installation Cost', 'Decommissioning Cost']
    
    # Rearrange lines and labels according to desired order
    ordered_lines = [lines[labels.index(label)] for label in desired_order]
    ordered_labels = [label for label in desired_order]

    fig.legend(ordered_lines, ordered_labels, bbox_to_anchor=(0.5, 1.05), loc='center', ncol=2, frameon=False)

    plt.tight_layout()
    plt.savefig(f'C:\\Users\\cflde\\Downloads\\iac_cost_vs_distance.png', dpi=400, bbox_inches='tight')
    plt.show()

def plot_costs_vs_capacity():
    distance = 6 * 240  # km
    capacities = np.linspace(0, 150, 1000)  # Capacities in MW

    total_costs, equip_costs, inst_costs, total_ope_costs, deco_costs = [], [], [], [], []

    for capacity in capacities:
        total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost = calc_total_cost_iac(distance, capacity)
        total_costs.append(total_cost)
        equip_costs.append(equip_cost)
        inst_costs.append(inst_cost)
        total_ope_costs.append(total_ope_cost)
        deco_costs.append(deco_cost)

    fig, axs = plt.subplots(2, 1, figsize=(6, 6), gridspec_kw={'height_ratios': [4, 1]}, sharex=True)

    # Get the color mapping
    colors = cost_colors()

    # Define custom formatting functions for this figure
    def format_x_axis_capacity(value, tick_position):
        return f'{value:.0f}' if value != 0 else '0'  # 0 decimal places for x-axis

    def format_y_axis_capacity(value, tick_position):
        return f'{value:.3f}' if value != 0 else '0'  # 3 decimal places for y-axis

    # Plotting the larger range
    axs[0].plot(capacities, total_costs, label='Total Cost', color=colors['Total Cost'])
    axs[0].plot(capacities, equip_costs, label='Equipment Cost', color=colors['Equipment Cost'])
    axs[0].plot(capacities, inst_costs, label='Installation Cost', color=colors['Installation Cost'])
    axs[0].plot(capacities, total_ope_costs, label='Operating Cost', color=colors['Operating Cost'])
    axs[0].plot(capacities, deco_costs, label='Decommissioning Cost', color=colors['Decommissioning Cost'])

    axs[0].set_xlim(0, 150)
    axs[0].set_ylim(0, 0.50)
    axs[0].yaxis.set_major_locator(MultipleLocator(0.50 / 4))
    axs[0].yaxis.set_minor_locator(MultipleLocator(0.50 / 4 / 4))
    axs[0].yaxis.set_major_formatter(FuncFormatter(format_y_axis_capacity))
    axs[0].xaxis.set_major_formatter(FuncFormatter(format_x_axis_capacity))

    # Plotting the smaller range
    axs[1].plot(capacities, total_costs, label='Total Cost', color=colors['Total Cost'])
    axs[1].plot(capacities, equip_costs, label='Equipment Cost', color=colors['Equipment Cost'])
    axs[1].plot(capacities, inst_costs, label='Installation Cost', color=colors['Installation Cost'])
    axs[1].plot(capacities, total_ope_costs, label='Operating Cost', color=colors['Operating Cost'])
    axs[1].plot(capacities, deco_costs, label='Decommissioning Cost', color=colors['Decommissioning Cost'])

    axs[1].set_xlim(0, 150)
    axs[1].set_ylim(0, 0.025)
    axs[1].yaxis.set_major_locator(MultipleLocator(0.025))
    axs[1].yaxis.set_minor_locator(MultipleLocator(0.025 / 4))
    axs[1].yaxis.set_major_formatter(FuncFormatter(format_y_axis_capacity))
    axs[1].xaxis.set_major_formatter(FuncFormatter(format_x_axis_capacity))

    for ax in axs:
        ax.xaxis.set_major_locator(MultipleLocator(25))
        ax.xaxis.set_minor_locator(MultipleLocator(6.25))
        ax.grid(which='major', linestyle='-', linewidth='0.5', color='gray')
        ax.grid(which='minor', linestyle=':', linewidth='0.5', color='gray')
        ax.minorticks_on()
    
    # axs[0].text(axs[0].get_xlim()[1] * 0.02, axs[0].get_ylim()[1] * 0.98, f'$S_{{wt}}={distance}$ m', ha='left', va='top', fontsize=11)
    
    axs[1].set_xlabel('Capacity (MW)')
    axs[0].set_ylabel('Cost (M€)')
    axs[1].set_ylabel('Cost (M€)')

    # Get legend handles and labels
    lines, labels = axs[0].get_legend_handles_labels()
    
    # Specify the desired order of labels
    desired_order = ['Total Cost', 'Equipment Cost', 'Operating Cost', 'Installation Cost', 'Decommissioning Cost']
    
    # Rearrange lines and labels according to desired order
    ordered_lines = [lines[labels.index(label)] for label in desired_order]
    ordered_labels = [label for label in desired_order]

    fig.legend(ordered_lines, ordered_labels, bbox_to_anchor=(0.5, 1.05), loc='center', ncol=2, frameon=False)

    plt.tight_layout()
    plt.savefig(f'C:\\Users\\cflde\\Downloads\\iac_cost_vs_capacity.png', dpi=400, bbox_inches='tight')
    plt.show()

if __name__ == "__main__":
    # Call the function to plot the costs for a given capacity
    plot_costs_vs_distance()

    # Call the function to plot the costs for a given distance
    plot_costs_vs_capacity()