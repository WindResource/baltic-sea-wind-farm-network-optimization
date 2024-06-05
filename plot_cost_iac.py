import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

from scripts.present_value import present_value
from scripts.iac_cost import iac_cost_ceil

# Define font parameters
font = {'family': 'serif',
        'weight': 'normal',
        'size': 12}

# Set font
plt.rc('font', **font)


def calc_total_cost_iac(distance, capacity):
    
    equip_cost, inst_cost = iac_cost_ceil(distance, capacity)
    
    ope_cost_yearly = 0.002 * equip_cost
    
    deco_cost = 0.5 * inst_cost

    # Calculate present value
    total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost = present_value(equip_cost, inst_cost, ope_cost_yearly, deco_cost)
    
    return total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost


def plot_costs_vs_distance():
    capacity = 120 # MW
    distances = np.linspace(0, 1.5, 100)  # Distances in km

    total_costs, equip_costs, inst_costs, total_ope_costs, deco_costs = [], [], [], [], []

    for distance in distances:
        total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost = calc_total_cost_iac(distance, capacity)
        total_costs.append(total_cost)
        equip_costs.append(equip_cost)
        inst_costs.append(inst_cost)
        total_ope_costs.append(total_ope_cost)
        deco_costs.append(deco_cost)

    fig, axs = plt.subplots(2, 1, figsize=(6, 6), gridspec_kw={'height_ratios': [4, 1]}, sharex=True)

    # Plotting the larger range
    axs[0].plot(distances, total_costs, label='Total PV')
    axs[0].plot(distances, equip_costs, label='Equipment PV')
    axs[0].plot(distances, inst_costs, label='Installation PV')
    axs[0].plot(distances, total_ope_costs, label='Total Operational PV')
    axs[0].plot(distances, deco_costs, label='Decommissioning PV')

    axs[0].set_xlim(0, 1.5)
    axs[0].set_ylim(0,1)
    axs[0].yaxis.set_major_locator(MultipleLocator(0.25))
    axs[0].yaxis.set_minor_locator(MultipleLocator(0.0625))

    # Plotting the smaller range
    axs[1].plot(distances, total_costs, label='Total Cost')
    axs[1].plot(distances, equip_costs, label='Equipment Cost')
    axs[1].plot(distances, inst_costs, label='Installation Cost')
    axs[1].plot(distances, total_ope_costs, label='Total Operational Cost')
    axs[1].plot(distances, deco_costs, label='Decommissioning Cost')

    axs[1].set_xlim(0, 1.5)
    axs[1].set_ylim(0, 0.05)
    axs[1].yaxis.set_major_locator(MultipleLocator(0.05))
    axs[1].yaxis.set_minor_locator(MultipleLocator(0.0125))

    for ax in axs:
        ax.xaxis.set_major_locator(MultipleLocator(0.25))
        ax.xaxis.set_minor_locator(MultipleLocator(0.0625))
        ax.grid(which='major', linestyle='-', linewidth='0.5', color='gray')
        ax.grid(which='minor', linestyle=':', linewidth='0.5', color='gray')
    
    axs[0].text(axs[0].get_xlim()[1] * 0.02, axs[0].get_ylim()[1] * 0.99, f'$Capacity ={capacity}MW$', ha='left', va='top', fontsize=11)
    
    axs[1].set_xlabel('Distance (km)')
    axs[0].set_ylabel('Cost (M€)')
    axs[1].set_ylabel('Cost (M€)')

    lines, labels = axs[0].get_legend_handles_labels()
    fig.legend(lines, labels, bbox_to_anchor=(0.5, 1.04), loc='center', ncol=2, frameon=False)

    plt.tight_layout()
    plt.savefig(f'C:\\Users\\cflde\\Downloads\\iac_cost_vs_distance.png', dpi=400, bbox_inches='tight')
    plt.show()

def plot_costs_vs_capacity():
    distance = 1.680 # km
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

    # Plotting the larger range
    axs[0].plot(capacities, total_costs, label='Total PV')
    axs[0].plot(capacities, equip_costs, label='Equipment PV')
    axs[0].plot(capacities, inst_costs, label='Installation PV')
    axs[0].plot(capacities, total_ope_costs, label='Total Operating PV')
    axs[0].plot(capacities, deco_costs, label='Decommissioning PV')

    axs[0].set_xlim(0, 150)
    axs[0].set_ylim(0, 1.25)
    axs[0].yaxis.set_major_locator(MultipleLocator(0.25))
    axs[0].yaxis.set_minor_locator(MultipleLocator(0.0625))

    # Plotting the smaller range
    axs[1].plot(capacities, total_costs, label='Total PV')
    axs[1].plot(capacities, equip_costs, label='Equipment PV')
    axs[1].plot(capacities, inst_costs, label='Installation PV')
    axs[1].plot(capacities, total_ope_costs, label='Total Operating PV')
    axs[1].plot(capacities, deco_costs, label='Decommissioning PV')

    axs[1].set_xlim(0, 150)
    axs[1].set_ylim(0, 0.075)
    axs[1].yaxis.set_major_locator(MultipleLocator(0.075))
    axs[1].yaxis.set_minor_locator(MultipleLocator(0.025))

    for ax in axs:
        ax.xaxis.set_major_locator(MultipleLocator(25))
        ax.xaxis.set_minor_locator(MultipleLocator(6.25))
        ax.grid(which='major', linestyle='-', linewidth='0.5', color='gray')
        ax.grid(which='minor', linestyle=':', linewidth='0.5', color='gray')
        ax.minorticks_on()

    axs[0].text(axs[0].get_xlim()[1] * 0.02, axs[0].get_ylim()[1] * 0.99, f'$Distance ={distance}km$', ha='left', va='top', fontsize=11)
    
    axs[1].set_xlabel('Capacity (MW)')
    axs[0].set_ylabel('Cost (M€)')
    axs[1].set_ylabel('Cost (M€)')

    lines, labels = axs[0].get_legend_handles_labels()
    fig.legend(lines, labels, bbox_to_anchor=(0.5, 1.04), loc='center', ncol=2, frameon=False)

    plt.tight_layout()
    plt.savefig(f'C:\\Users\\cflde\\Downloads\\iac_cost_vs_capacity.png', dpi=400, bbox_inches='tight')
    plt.show()


if __name__ == "__main__":
    # Call the function to plot the costs for a given capacity
    plot_costs_vs_distance()

    # Call the function to plot the costs for a given distance
    plot_costs_vs_capacity()