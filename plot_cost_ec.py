import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import MultipleLocator
from scripts.ec_cost import ec2_cost_fun
import matplotlib.lines as mlines
from matplotlib.legend_handler import HandlerBase

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

# Custom legend handler to display solid and dashed lines stacked vertically, with the solid line on top
class HandlerStackedLines(HandlerBase):
    def create_artists(self, legend, orig_handle, xdescent, ydescent, width, height, fontsize, trans):
        # Set the gap between the two lines
        vertical_gap = height * 0.5

        # Draw solid line at the top
        solid_line = mlines.Line2D([xdescent, xdescent + width], [ydescent + height / 2 + vertical_gap, ydescent + height / 2 + vertical_gap],
                                color=orig_handle.get_color(), linestyle='-', lw=2, transform=trans)

        # Draw dashed line below the solid line
        dashed_line = mlines.Line2D([xdescent, xdescent + width], [ydescent + height / 2 - vertical_gap, ydescent + height / 2 - vertical_gap],
                                    color=orig_handle.get_color(), linestyle='--', lw=2, transform=trans)

        return [solid_line, dashed_line]

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

    # Use default colors
    default_colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
    
    # Define color assignments
    colors = {
        'Total Cost': default_colors[0],
        'Equipment Cost': default_colors[1],
        'Operating Cost': default_colors[3],
        'Installation Cost': default_colors[2],
        'Decommissioning Cost': default_colors[4]
    }

    # Plotting the larger range
    line1, = axs[0].plot(capacities, total_costs, label='Total Cost', color=colors['Total Cost'])
    line2, = axs[0].plot(capacities, equip_costs, label='Equipment Cost', color=colors['Equipment Cost'])
    line4, = axs[0].plot(capacities, total_ope_costs, label='Operating Cost', color=colors['Operating Cost'])
    line3, = axs[0].plot(capacities, inst_costs, label='Installation Cost', color=colors['Installation Cost'])
    line5, = axs[0].plot(capacities, deco_costs, label='Decommissioning Cost', color=colors['Decommissioning Cost'])

    # Plot the dashed lines using the same colors as the solid lines
    axs[0].plot(capacities, total_costs_lin, linestyle="--", color=line1.get_color())
    axs[0].plot(capacities, equip_costs_lin, linestyle="--", color=line2.get_color())
    axs[0].plot(capacities, total_ope_costs_lin, linestyle="--", color=line4.get_color())
    axs[0].plot(capacities, inst_costs_lin, linestyle="--", color=line3.get_color())
    axs[0].plot(capacities, deco_costs_lin, linestyle="--", color=line5.get_color())

    axs[0].set_xlim(0, 1500)
    axs[0].set_ylim(0, 500)
    axs[0].yaxis.set_major_locator(plt.MultipleLocator(500 / 4))
    axs[0].yaxis.set_minor_locator(plt.MultipleLocator(500 / 4 / 4))

    # Plotting the smaller range
    axs[1].plot(capacities, total_costs, label='Total Cost', color=colors['Total Cost'])
    axs[1].plot(capacities, equip_costs, label='Equipment Cost', color=colors['Equipment Cost'])
    axs[1].plot(capacities, total_ope_costs, label='Operating Cost', color=colors['Operating Cost'])
    axs[1].plot(capacities, inst_costs, label='Installation Cost', color=colors['Installation Cost'])
    axs[1].plot(capacities, deco_costs, label='Decommissioning Cost', color=colors['Decommissioning Cost'])

    axs[1].plot(capacities, total_costs_lin, linestyle="--", color=line1.get_color())
    axs[1].plot(capacities, equip_costs_lin, linestyle="--", color=line2.get_color())
    axs[1].plot(capacities, total_ope_costs_lin, linestyle="--", color=line4.get_color())
    axs[1].plot(capacities, inst_costs_lin, linestyle="--", color=line3.get_color())
    axs[1].plot(capacities, deco_costs_lin, linestyle="--", color=line5.get_color())

    axs[1].set_xlim(0, 1500)
    axs[1].set_ylim(0, 20)
    axs[1].yaxis.set_major_locator(plt.MultipleLocator(20))
    axs[1].yaxis.set_minor_locator(plt.MultipleLocator(20 / 4))

    for ax in axs:
        ax.xaxis.set_major_locator(plt.MultipleLocator(250))
        ax.xaxis.set_minor_locator(plt.MultipleLocator(50))
        ax.grid(which='major', linestyle='-', linewidth='0.5', color='gray')
        ax.grid(which='minor', linestyle=':', linewidth='0.5', color='gray')

    axs[0].text(axs[0].get_xlim()[1] * 0.02, axs[0].get_ylim()[1] * 0.99, f'$Distance = {distance}km$', ha='left', va='top', fontsize=11)

    axs[1].set_xlabel('Capacity (MW)')
    axs[0].set_ylabel('Cost (M€)')
    axs[1].set_ylabel('Cost (M€)')

    # Create custom legend handles with the desired order and standard colors
    custom_lines = [
        mlines.Line2D([], [], color=colors['Total Cost'], lw=2),
        mlines.Line2D([], [], color=colors['Equipment Cost'], lw=2),
        mlines.Line2D([], [], color=colors['Operating Cost'], lw=2),
        mlines.Line2D([], [], color=colors['Installation Cost'], lw=2),
        mlines.Line2D([], [], color=colors['Decommissioning Cost'], lw=2)
    ]

    labels = [
        'Total Cost',
        'Equipment Cost',
        'Operating Cost',
        'Installation Cost',
        'Decommissioning Cost'
    ]

    # Use custom handler to display solid and dashed lines stacked vertically with solid on top
    fig.legend(
        custom_lines,
        labels,
        handler_map={mlines.Line2D: HandlerStackedLines()},
        bbox_to_anchor=(0.5, 1.12), loc='upper center', ncol=2, frameon=False,
        handletextpad=1  # Increase spacing between symbols and text
    )

    plt.tight_layout()
    plt.savefig(f'C:\\Users\\cflde\\Downloads\\ec_cost_vs_capacity.png', dpi=400, bbox_inches='tight')
    plt.show()

if __name__ == "__main__":

    plot_cost_vs_distance()

    plot_cost_vs_capacity()