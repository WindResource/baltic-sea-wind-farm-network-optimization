import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from scripts.ec_cost import EC_cost

ec_cost = EC_cost()

# Define font parameters
font = {'family': 'serif',
        'weight': 'normal',
        'size': 12}

# Set font
plt.rc('font', **font)

def plot_cost_vs_distance(ec):
    capacity = 750 # MW
    distances = np.linspace(0, 300, 500)  # Distances in km

    total_costs, equip_costs, inst_costs, total_ope_costs, deco_costs = [], [], [], [], []

    for distance in distances:
        if ec == 1:
            total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost = ec_cost.ec1_cost_ceil(distance, capacity)
        else:
            total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost = ec_cost.ec2_cost_ceil(distance, capacity)

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
    axs[0].plot(distances, total_ope_costs, label='Total Operating PV')
    axs[0].plot(distances, deco_costs, label='Decommissioning PV')

    axs[0].set_xlim(0, 300)
    axs[0].set_ylim(0, 1800)
    axs[0].yaxis.set_major_locator(MultipleLocator(200))
    axs[0].yaxis.set_minor_locator(MultipleLocator(50))

    # Plotting the smaller range
    axs[1].plot(distances, total_costs, label='Total PV')
    axs[1].plot(distances, equip_costs, label='Equipment PV')
    axs[1].plot(distances, inst_costs, label='Installation PV')
    axs[1].plot(distances, total_ope_costs, label='Total Operating PV')
    axs[1].plot(distances, deco_costs, label='Decommissioning PV')

    axs[1].set_xlim(0, 300)
    axs[1].set_ylim(0, 100)
    axs[1].yaxis.set_major_locator(MultipleLocator(50))
    axs[1].yaxis.set_minor_locator(MultipleLocator(12.5))

    for ax in axs:
        ax.xaxis.set_major_locator(MultipleLocator(50))
        ax.xaxis.set_minor_locator(MultipleLocator(12.5))
        ax.grid(which='major', linestyle='-', linewidth='0.5', color='gray')
        ax.grid(which='minor', linestyle=':', linewidth='0.5', color='gray')

    axs[0].text(axs[0].get_xlim()[1] * 0.02, axs[0].get_ylim()[1] * 0.99, f'$Capacity ={capacity}MW$', ha='left', va='top', fontsize=11)

    axs[1].set_xlabel('Distance (km)')
    axs[0].set_ylabel('Cost (M€)')
    axs[1].set_ylabel('Cost (M€)')

    lines, labels = axs[0].get_legend_handles_labels()
    fig.legend(lines, labels, bbox_to_anchor=(0.5, 1.05), loc='center', ncol=2, frameon=False)

    plt.tight_layout()
    plt.savefig(f'C:\\Users\\cflde\\Downloads\\ec{ec}_cost_vs_distance.png', dpi=400, bbox_inches='tight')
    plt.show()

def plot_cost_vs_capacity(ec):
    distance = 100 #km
    capacities = np.linspace(0, 1500, 500)  # Capacities in MW

    total_costs, equip_costs, inst_costs, total_ope_costs, deco_costs = [], [], [], [], []
    
    total_costs_lin, equip_costs_lin, inst_costs_lin, total_ope_costs_lin, deco_costs_lin = [], [], [], [], []

    for capacity in capacities:
        if ec == 1:
            total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost = ec_cost.ec1_cost_ceil(distance, capacity)
            total_cost_lin, equip_cost_lin, inst_cost_lin, total_ope_cost_lin, deco_cost_lin = ec_cost.ec1_cost_lin(distance, capacity)
        else:
            total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost = ec_cost.ec2_cost_ceil(distance, capacity)
            total_cost_lin, equip_cost_lin, inst_cost_lin, total_ope_cost_lin, deco_cost_lin = ec_cost.ec2_cost_lin(distance, capacity)
        
        total_costs.append(total_cost)
        equip_costs.append(equip_cost)
        inst_costs.append(inst_cost)
        total_ope_costs.append(total_ope_cost)
        deco_costs.append(deco_cost)
        
        total_costs_lin.append(total_cost_lin)
        equip_costs_lin.append(equip_cost_lin)
        inst_costs_lin.append(inst_cost_lin)
        total_ope_costs_lin.append(total_ope_cost_lin)
        deco_costs_lin.append(deco_cost_lin)

    fig, axs = plt.subplots(2, 1, figsize=(6, 6), gridspec_kw={'height_ratios': [4, 1]}, sharex=True)

    # Plotting the larger range
    line1, = axs[0].plot(capacities, total_costs, label='Total PV')
    line2, = axs[0].plot(capacities, equip_costs, label='Equipment PV')
    line3, = axs[0].plot(capacities, inst_costs, label='Installation PV')
    line4, = axs[0].plot(capacities, total_ope_costs, label='Total Operating PV')
    line5, = axs[0].plot(capacities, deco_costs, label='Decommissioning PV')
    
    # Plot the dashed lines using colors from the solid lines
    axs[0].plot(capacities, total_costs_lin, label='Total PV (cont.)', color=line1.get_color(), linestyle="--")
    axs[0].plot(capacities, equip_costs_lin, label='Equipment PV (cont.)', color=line2.get_color(), linestyle="--")
    axs[0].plot(capacities, inst_costs_lin, label='Installation PV (cont.)', color=line3.get_color(), linestyle="--")
    axs[0].plot(capacities, total_ope_costs_lin, label='Total Operating PV (cont.)', color=line4.get_color(), linestyle="--")
    axs[0].plot(capacities, deco_costs_lin, label='Decommissioning PV (cont.)', color=line5.get_color(), linestyle="--")

    axs[0].set_xlim(0, 1500)
    axs[0].set_ylim(0, 1000)
    axs[0].yaxis.set_major_locator(MultipleLocator(200))
    axs[0].yaxis.set_minor_locator(MultipleLocator(50))

    # Plotting the smaller range
    axs[1].plot(capacities, total_costs, label='Total PV')
    axs[1].plot(capacities, equip_costs, label='Equipment PV')
    axs[1].plot(capacities, inst_costs, label='Installation PV')
    axs[1].plot(capacities, total_ope_costs, label='Total Operating PV')
    axs[1].plot(capacities, deco_costs, label='Decommissioning PV')
    
    axs[1].plot(capacities, total_costs_lin, label='Total PV (cont.)', color=line1.get_color(), linestyle="--")
    axs[1].plot(capacities, equip_costs_lin, label='Equipment PV (cont.)', color=line2.get_color(), linestyle="--")
    axs[1].plot(capacities, inst_costs_lin, label='Installation PV (cont.)', color=line3.get_color(), linestyle="--")
    axs[1].plot(capacities, total_ope_costs_lin, label='Total Operating PV (cont.)', color=line4.get_color(), linestyle="--")
    axs[1].plot(capacities, deco_costs_lin, label='Decommissioning PV (cont.)', color=line5.get_color(), linestyle="--")

    axs[1].set_xlim(0, 1500)
    axs[1].set_ylim(0, 50)
    axs[1].yaxis.set_major_locator(MultipleLocator(50))
    axs[1].yaxis.set_minor_locator(MultipleLocator(12.5))

    for ax in axs:
        ax.xaxis.set_major_locator(MultipleLocator(250))
        ax.xaxis.set_minor_locator(MultipleLocator(50))
        ax.grid(which='major', linestyle='-', linewidth='0.5', color='gray')
        ax.grid(which='minor', linestyle=':', linewidth='0.5', color='gray')

    axs[0].text(axs[0].get_xlim()[1] * 0.02, axs[0].get_ylim()[1] * 0.99, f'$Distance ={distance}km$', ha='left', va='top', fontsize=11)
    
    axs[1].set_xlabel('Capacity (MW)')
    axs[0].set_ylabel('Cost (M€)')
    axs[1].set_ylabel('Cost (M€)')

    lines, labels = axs[0].get_legend_handles_labels()
    fig.legend(lines, labels, bbox_to_anchor=(0.5, 1.10), loc='center', ncol=2, frameon=False)

    plt.tight_layout()
    plt.savefig(f'C:\\Users\\cflde\\Downloads\\ec{ec}_cost_vs_capacity.png', dpi=400, bbox_inches='tight')
    plt.show()

if __name__ == "__main__":
    # Call the function to plot the costs for a given capacity
    for n in (1,2):
        plot_cost_vs_distance(n)  # Example capacity in MW


    # Call the function to plot the costs for a given distance
    for n in (1,2):
        plot_cost_vs_capacity(n)  # Example distance in km