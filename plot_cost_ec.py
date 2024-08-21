import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import MultipleLocator
from scripts.ec_cost import ec2_cost_fun

# Define font parameters
font = {'family': 'serif',
        'weight': 'normal',
        'size': 12}

# Set font
plt.rc('font', **font)

def plot_cost_vs_distance():
    inst_year = 2040
    capacity = 750  # MW
    distances = np.linspace(0, 300, 500)  # Distances in km

    total_costs, equip_costs, inst_costs, total_ope_costs, deco_costs = [], [], [], [], []

    for distance in distances:
        total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost = ec2_cost_fun(inst_year, distance, capacity, "ceil")
        total_costs.append(total_cost)
        equip_costs.append(equip_cost)
        inst_costs.append(inst_cost)
        total_ope_costs.append(total_ope_cost)
        deco_costs.append(deco_cost)

    fig, axs = plt.subplots(2, 1, figsize=(6, 6), gridspec_kw={'height_ratios': [4, 1]}, sharex=True)

    # Plotting the larger range
    axs[0].plot(distances, total_costs, label='Total Cost')
    axs[0].plot(distances, equip_costs, label='Equipment Cost')
    axs[0].plot(distances, inst_costs, label='Installation Cost')
    axs[0].plot(distances, total_ope_costs, label='Total Operating Cost')
    axs[0].plot(distances, deco_costs, label='Decommissioning Cost')

    axs[0].set_xlim(0, 300)
    axs[0].set_ylim(0, 1800)
    axs[0].yaxis.set_major_locator(MultipleLocator(200))
    axs[0].yaxis.set_minor_locator(MultipleLocator(50))

    # Plotting the smaller range
    axs[1].plot(distances, total_costs, label='Total Cost')
    axs[1].plot(distances, equip_costs, label='Equipment Cost')
    axs[1].plot(distances, inst_costs, label='Installation Cost')
    axs[1].plot(distances, total_ope_costs, label='Total Operating Cost')
    axs[1].plot(distances, deco_costs, label='Decommissioning Cost')

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
    plt.savefig(f'C:\\Users\\cflde\\Downloads\\ec_cost_vs_distance.png', dpi=400, bbox_inches='tight')
    plt.show()

def plot_cost_vs_capacity():
    inst_year = 2040
    distance = 100  # km
    capacities = np.linspace(0, 1500, 500)  # Capacities in MW

    total_costs, equip_costs, inst_costs, total_ope_costs, deco_costs = [], [], [], [], []
    total_costs_lin, equip_costs_lin, inst_costs_lin, total_ope_costs_lin, deco_costs_lin = [], [], [], [], []

    for capacity in capacities:
        total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost = ec2_cost_fun(inst_year, distance, capacity, "ceil")
        total_cost_lin, equip_cost_lin, inst_cost_lin, total_ope_cost_lin, deco_cost_lin = ec2_cost_fun(inst_year, distance, capacity, "lin")

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
    line1, = axs[0].plot(capacities, total_costs, label='Total Cost')
    line2, = axs[0].plot(capacities, equip_costs, label='Equipment Cost')
    line3, = axs[0].plot(capacities, inst_costs, label='Installation Cost')
    line4, = axs[0].plot(capacities, total_ope_costs, label='Total Operating Cost')
    line5, = axs[0].plot(capacities, deco_costs, label='Decommissioning Cost')

    # Plot the dashed lines using colors from the solid lines
    axs[0].plot(capacities, total_costs_lin, linestyle="--", color=line1.get_color())
    axs[0].plot(capacities, equip_costs_lin, linestyle="--", color=line2.get_color())
    axs[0].plot(capacities, inst_costs_lin, linestyle="--", color=line3.get_color())
    axs[0].plot(capacities, total_ope_costs_lin, linestyle="--", color=line4.get_color())
    axs[0].plot(capacities, deco_costs_lin, linestyle="--", color=line5.get_color())

    axs[0].set_xlim(0, 1500)
    axs[0].set_ylim(0, 1000)
    axs[0].yaxis.set_major_locator(MultipleLocator(200))
    axs[0].yaxis.set_minor_locator(MultipleLocator(50))

    # Plotting the smaller range
    axs[1].plot(capacities, total_costs, label='Total Cost')
    axs[1].plot(capacities, equip_costs, label='Equipment Cost')
    axs[1].plot(capacities, inst_costs, label='Installation Cost')
    axs[1].plot(capacities, total_ope_costs, label='Total Operating Cost')
    axs[1].plot(capacities, deco_costs, label='Decommissioning Cost')

    axs[1].plot(capacities, total_costs_lin, linestyle="--", color=line1.get_color())
    axs[1].plot(capacities, equip_costs_lin, linestyle="--", color=line2.get_color())
    axs[1].plot(capacities, inst_costs_lin, linestyle="--", color=line3.get_color())
    axs[1].plot(capacities, total_ope_costs_lin, linestyle="--", color=line4.get_color())
    axs[1].plot(capacities, deco_costs_lin, linestyle="--", color=line5.get_color())

    axs[1].set_xlim(0, 1500)
    axs[1].set_ylim(0, 50)
    axs[1].yaxis.set_major_locator(MultipleLocator(50))
    axs[1].yaxis.set_minor_locator(MultipleLocator(12.5))

    for ax in axs:
        ax.xaxis.set_major_locator(MultipleLocator(250))
        ax.xaxis.set_minor_locator(MultipleLocator(50))
        ax.grid(which='major', linestyle='-', linewidth='0.5', color='gray')
        ax.grid(which='minor', linestyle=':', linewidth='0.5', color='gray')

    axs[0].text(axs[0].get_xlim()[1] * 0.02, axs[0].get_ylim()[1] * 0.99, f'$Distance = {distance}km$', ha='left', va='top', fontsize=11)

    axs[1].set_xlabel('Capacity (MW)')
    axs[0].set_ylabel('Cost (M€)')
    axs[1].set_ylabel('Cost (M€)')

    # Create custom legend handles
    custom_lines = [
        Line2D([0], [0], color=line1.get_color(), linestyle='-', lw=2),
        Line2D([0], [0], color=line1.get_color(), linestyle='--', lw=2),
        Line2D([0], [0], color=line2.get_color(), linestyle='-', lw=2),
        Line2D([0], [0], color=line2.get_color(), linestyle='--', lw=2),
        Line2D([0], [0], color=line3.get_color(), linestyle='-', lw=2),
        Line2D([0], [0], color=line3.get_color(), linestyle='--', lw=2),
        Line2D([0], [0], color=line4.get_color(), linestyle='-', lw=2),
        Line2D([0], [0], color=line4.get_color(), linestyle='--', lw=2),
        Line2D([0], [0], color=line5.get_color(), linestyle='-', lw=2),
        Line2D([0], [0], color=line5.get_color(), linestyle='--', lw=2),
    ]

    labels = [
        'Total Cost',
        'Total Cost (cont.)',
        'Equipment Cost',
        'Equipment Cost (cont.)',
        'Installation Cost',
        'Installation Cost (cont.)',
        'Total Operating Cost',
        'Total Operating Cost (cont.)',
        'Decommissioning Cost',
        'Decommissioning Cost (cont.)'
    ]

    # Combine solid and dashed lines into single legend entries
    fig.legend(
        [custom_lines[i] for i in range(0, len(custom_lines), 2)],
        [labels[i] for i in range(0, len(labels), 2)],
        bbox_to_anchor=(0.5, 1.10), loc='center', ncol=2, frameon=False
    )

    plt.tight_layout()
    plt.savefig(f'C:\\Users\\cflde\\Downloads\\ec_cost_vs_capacity.png', dpi=400, bbox_inches='tight')
    plt.show()

if __name__ == "__main__":

    plot_cost_vs_distance()

    plot_cost_vs_capacity()