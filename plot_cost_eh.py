import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from scripts.present_value import present_value
from scripts.eh_cost import check_supp, equip_cost_lin, inst_deco_cost_lin

from matplotlib.ticker import MultipleLocator, FuncFormatter
from scripts.colors import cost_colors

# Define font parameters
font = {'family': 'serif',
        'weight': 'normal',
        'size': 12}

# Set font
plt.rc('font', **font)


def eh_cost_lin(water_depth, ice_cover, port_distance, eh_capacity):
    """
    """
    inst_year = 2040
    
    # Determine support structure
    supp_structure = check_supp(water_depth)
    
    # Calculate equipment cost
    supp_cost, conv_cost = equip_cost_lin(water_depth, supp_structure, ice_cover, eh_capacity)

    equip_cost = supp_cost + conv_cost
    
    # Calculate installation and decommissioning cost
    inst_cost = inst_deco_cost_lin(supp_structure, port_distance, "inst")
    deco_cost = inst_deco_cost_lin(supp_structure, port_distance, "deco")

    # Calculate yearly operational cost
    ope_cost_yearly = 0.03 * conv_cost
    
    total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost = present_value(inst_year, equip_cost, inst_cost, ope_cost_yearly, deco_cost)  # Calculate present value of cost

    return total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost

def plot_total_cost_vs_water_depth():
    water_depths = np.linspace(0, 300, 500)
    ice_cover = 0
    port_distance = 50
    eh_capacity = 1000

    total_costs, equip_costs, inst_costs, total_ope_costs, deco_costs = [], [], [], [], []

    for wd in water_depths:
        total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost = eh_cost_lin(wd, ice_cover, port_distance, eh_capacity)
        total_costs.append(total_cost)
        equip_costs.append(equip_cost)
        inst_costs.append(inst_cost)
        total_ope_costs.append(total_ope_cost)
        deco_costs.append(deco_cost)

    fig, axs = plt.subplots(2, 1, figsize=(6, 6), gridspec_kw={'height_ratios': [4, 1]}, sharex=True)

    # Get the color mapping
    colors = cost_colors()

    # Inline formatter functions
    y_axis_formatter_large = FuncFormatter(lambda y, pos: '0' if y == 0 else f'{y:.0f}')
    y_axis_formatter_small = FuncFormatter(lambda y, pos: '0' if y == 0 else f'{y:.2f}')

    # Plotting the larger range
    axs[0].plot(water_depths, total_costs, label='Total Cost', color=colors['Total Cost'])
    axs[0].plot(water_depths, equip_costs, label='Equipment Cost', color=colors['Equipment Cost'])
    axs[0].plot(water_depths, inst_costs, label='Installation Cost', color=colors['Installation Cost'])
    axs[0].plot(water_depths, total_ope_costs, label='Operating Cost', color=colors['Operating Cost'])
    axs[0].plot(water_depths, deco_costs, label='Decommissioning Cost', color=colors['Decommissioning Cost'])

    axs[0].set_xlim(0, 300)
    axs[0].set_ylim(0, 50)
    axs[0].yaxis.set_major_locator(MultipleLocator(50 / 5))
    axs[0].yaxis.set_minor_locator(MultipleLocator(50 / 4 / 4))
    axs[0].yaxis.set_major_formatter(y_axis_formatter_large)

    # Plotting the smaller range
    axs[1].plot(water_depths, total_costs, label='Total Cost', color=colors['Total Cost'])
    axs[1].plot(water_depths, equip_costs, label='Equipment Cost', color=colors['Equipment Cost'])
    axs[1].plot(water_depths, inst_costs, label='Installation Cost', color=colors['Installation Cost'])
    axs[1].plot(water_depths, total_ope_costs, label='Operating Cost', color=colors['Operating Cost'])
    axs[1].plot(water_depths, deco_costs, label='Decommissioning Cost', color=colors['Decommissioning Cost'])

    axs[1].set_ylim(0, 0.75)
    axs[1].yaxis.set_major_locator(MultipleLocator(0.75))
    axs[1].yaxis.set_minor_locator(MultipleLocator(0.25))
    axs[1].yaxis.set_major_formatter(y_axis_formatter_small)

    for ax in axs:
        ax.xaxis.set_major_locator(MultipleLocator(50))
        ax.xaxis.set_minor_locator(MultipleLocator(5))
        ax.grid(which='major', linestyle='-', linewidth='0.5', color='gray')
        ax.grid(which='minor', linestyle=':', linewidth='0.5', color='gray')
        ax.minorticks_on()
        
        ax.axvline(x=120, color='grey', linewidth='1.5', linestyle='--')

    axs[0].text(4, 1, 'Jacket', rotation=90, verticalalignment='bottom')
    axs[0].text(124, 1, 'Floating', rotation=90, verticalalignment='bottom')

    axs[1].set_xlabel('Water Depth (m)')
    axs[0].set_ylabel('Cost (M€)')
    axs[1].set_ylabel('Cost (M€)')

    # Get legend handles and labels
    lines, labels = axs[0].get_legend_handles_labels()
    
    # Define desired order for the legend
    desired_order = ['Total Cost', 'Equipment Cost', 'Operating Cost', 'Installation Cost', 'Decommissioning Cost']
    
    # Rearrange lines and labels according to desired order
    ordered_lines = [lines[labels.index(label)] for label in desired_order]
    ordered_labels = [label for label in desired_order]

    fig.legend(ordered_lines, ordered_labels, bbox_to_anchor=(0.5, 1.05), loc='center', ncol=2, frameon=False)
    
    plt.tight_layout()
    plt.savefig(f'C:\\Users\\cflde\\Downloads\\eh_total_cost_vs_water_depth.png', dpi=400, bbox_inches='tight')
    plt.show()

def plot_inst_deco_cost_vs_port_distance():
    wd_jacket = 80
    wd_floating = 150
    water_depths = [wd_jacket, wd_floating]
    port_distances = np.linspace(0, 300, 500)

    fig, axs = plt.subplots(2, 1, figsize=(6, 6), gridspec_kw={'height_ratios': [1, 1]}, sharex=True)

    # Get the color mapping
    colors = cost_colors()

    # Inline formatter functions
    y_axis_formatter = FuncFormatter(lambda y, pos: '0' if y == 0 else f'{y:.2f}')
    x_axis_formatter = FuncFormatter(lambda x, pos: f'{x:.0f}' if x % 100 == 0 else f'{x:.0f}')

    for i, water_depth in enumerate(water_depths):
        inst_costs, deco_costs = [], []

        for pd in port_distances:
            support_structure = check_supp(water_depth)
            inst_cost = inst_deco_cost_lin(support_structure, 1e3 * pd, "inst")
            deco_cost = inst_deco_cost_lin(support_structure, 1e3 * pd, "deco")
            inst_costs.append(inst_cost)
            deco_costs.append(deco_cost)

        axs[i].plot(port_distances, inst_costs, label='Installation Cost', color=colors['Installation Cost'], linestyle='-')
        axs[i].plot(port_distances, deco_costs, label='Decommissioning Cost', color=colors['Decommissioning Cost'], linestyle='--')
        
        # Set domain and range
        axs[i].set_xlim(0, 300)
        axs[i].set_ylim(0, 1.5)
        axs[i].yaxis.set_major_locator(MultipleLocator(1.5 / 2))
        axs[i].yaxis.set_minor_locator(MultipleLocator(1.5 / 4 / 4))
        axs[i].yaxis.set_major_formatter(y_axis_formatter)
        axs[i].xaxis.set_major_locator(MultipleLocator(50))
        axs[i].xaxis.set_minor_locator(MultipleLocator(10))
        axs[i].xaxis.set_major_formatter(x_axis_formatter)

        axs[i].grid(which='major', linestyle='-', linewidth='0.5', color='gray')
        axs[i].grid(which='minor', linestyle=':', linewidth='0.5', color='gray')
        axs[i].minorticks_on()

        supp_struct_str = 'Jacket' if water_depth < 120 else 'Floating'
        axs[i].text(5, 0.08, supp_struct_str, rotation=90)
        axs[i].text(5, axs[i].get_ylim()[1] * 0.98, f'$H_{{w}} = {water_depth}$ m', ha='left', va='top')
        axs[i].set_ylabel('Cost (M€)')

    axs[1].set_xlabel('Port Distance (km)')

    # Get legend handles and labels from the first subplot
    lines, labels = axs[0].get_legend_handles_labels()
    
    # Define desired order for the legend
    desired_order = ['Installation Cost', 'Decommissioning Cost']
    
    # Rearrange lines and labels according to desired order
    ordered_lines = [lines[labels.index(label)] for label in desired_order]
    ordered_labels = [label for label in desired_order]

    fig.legend(ordered_lines, ordered_labels, bbox_to_anchor=(0.35, 1.03), loc='center', ncol=1, frameon=False)
        
    plt.tight_layout()
    plt.savefig(f'C:\\Users\\cflde\\Downloads\\eh_inst_deco_cost_vs_port_distance.png', dpi=400, bbox_inches='tight')
    plt.show()

if __name__ == "__main__":

    plot_total_cost_vs_water_depth()

    plot_inst_deco_cost_vs_port_distance()
