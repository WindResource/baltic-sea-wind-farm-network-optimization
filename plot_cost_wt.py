import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, FuncFormatter

from scripts.present_value import present_value
from scripts.wt_cost import check_supp, calc_equip_cost, calc_inst_deco_cost
from scripts.colors import cost_colors


# Define font parameters
font = {'family': 'serif',
        'weight': 'normal',
        'size': 12}

# Set font
plt.rc('font', **font)


def calc_total_cost(water_depth, ice_cover, port_distance, turbine_capacity):
    """
    Calculate various costs for a given set of parameters.

    Parameters:
        water_depth (float): Water depth at the turbine location.
        ice_cover (int): Indicator if the area is ice-covered (1 for Yes, 0 for No).
        port_distance (float): Distance to the port.
        turbine_capacity (float): Capacity of the turbine.

    Returns:
        tuple: Total cost, equipment cost, installation cost, total operational cost, decommissioning cost in millions of Euros.
    """
    global first_year
    first_year = 2040
    
    support_structure = check_supp(water_depth)  # Determine support structure

    supp_cost, turbine_cost = calc_equip_cost(first_year, water_depth, support_structure, ice_cover, turbine_capacity)  # Calculate equipment cost

    equip_cost = supp_cost + turbine_cost
    
    inst_cost = calc_inst_deco_cost(water_depth, port_distance, turbine_capacity, "inst")  # Calculate installation cost
    deco_cost = calc_inst_deco_cost(water_depth, port_distance, turbine_capacity, "deco")  # Calculate decommissioning cost

    ope_cost_yearly = 0.025 * turbine_cost  # Calculate yearly operational cost

    total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost = present_value(first_year, equip_cost, inst_cost, ope_cost_yearly, deco_cost)  # Calculate present value of cost

    return total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost

def plot_costs_vs_water_depth():
    water_depths = np.linspace(0, 120, 500)
    ice_cover = 0  # Assuming no ice cover for simplicity
    port_distance = 100  # Assuming a constant port distance for simplicity
    turbine_capacity = 15  # Assuming a constant turbine capacity of 15 MW

    # Define labels and initialize lists for costs
    cost_labels = {
        'Total Cost': [],
        'Equipment Cost': [],
        'Installation Cost': [],
        'Operating Cost': [],
        'Decommissioning Cost': []
    }

    # Get the color mapping
    colors = cost_colors()

    # Calculate costs
    for wd in water_depths:
        total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost = calc_total_cost(wd, ice_cover, port_distance, turbine_capacity)
        cost_labels['Total Cost'].append(total_cost)
        cost_labels['Equipment Cost'].append(equip_cost)
        cost_labels['Installation Cost'].append(inst_cost)
        cost_labels['Operating Cost'].append(total_ope_cost)
        cost_labels['Decommissioning Cost'].append(deco_cost)

    fig, axs = plt.subplots(2, 1, figsize=(6, 6), gridspec_kw={'height_ratios': [4, 1]}, sharex=True)

    # Inline formatter functions
    y_axis_formatter_large = FuncFormatter(lambda y, pos: '0' if y == 0 else f'{y:.0f}')
    y_axis_formatter_small = FuncFormatter(lambda y, pos: '0' if y == 0 else f'{y:.2f}')

    # Plotting the larger range
    for label, costs in cost_labels.items():
        axs[0].plot(water_depths, costs, label=label, color=colors[label])

    axs[0].set_xlim(0, 120)
    axs[0].set_ylim(0, 20)
    axs[0].yaxis.set_major_locator(MultipleLocator(20/5))
    axs[0].yaxis.set_minor_locator(MultipleLocator(20/4))
    axs[0].yaxis.set_major_formatter(y_axis_formatter_large)

    # Plotting the smaller range
    for label, costs in cost_labels.items():
        axs[1].plot(water_depths, costs, label=label, color=colors[label])

    axs[1].set_xlim(0, 120)
    axs[1].set_ylim(0, 1)
    axs[1].yaxis.set_major_locator(MultipleLocator(1/2))
    axs[1].yaxis.set_minor_locator(MultipleLocator(1/2/2))
    axs[1].yaxis.set_major_formatter(y_axis_formatter_small)

    for ax in axs:
        ax.xaxis.set_major_locator(MultipleLocator(20))
        ax.xaxis.set_minor_locator(MultipleLocator(5))
        ax.grid(which='major', linestyle='-', linewidth='0.5', color='gray')
        ax.grid(which='minor', linestyle=':', linewidth='0.5', color='gray')
        ax.minorticks_on()
        
        ax.axvline(x=25, color='grey', linewidth='1.5', linestyle='--')
        ax.axvline(x=55, color='grey', linewidth='1.5', linestyle='--')

    axs[0].text(2, plt.ylim()[1], 'Monopile', rotation=90)
    axs[0].text(27, plt.ylim()[1], 'Jacket', rotation=90)
    axs[0].text(57, plt.ylim()[1], 'Floating', rotation=90)

    axs[1].set_xlabel('Water Depth (m)')
    axs[0].set_ylabel('Cost (M€)')
    axs[1].set_ylabel('Cost (M€)')

    # Create legend with desired order
    handles, labels = axs[0].get_legend_handles_labels()
    order = ['Total Cost', 'Equipment Cost', 'Operating Cost', 'Installation Cost', 'Decommissioning Cost']
    
    # Create a dictionary to map labels to handles
    handle_dict = dict(zip(labels, handles))
    
    # Reorder handles and labels
    ordered_handles = [handle_dict[label] for label in order]
    
    fig.legend(ordered_handles, order, bbox_to_anchor=(0.5, 1.05), loc='center', ncol=2, frameon=False)
    
    plt.tight_layout()
    plt.savefig(f'C:\\Users\\cflde\\Downloads\\wt_total_cost_vs_water_depth.png', dpi=400, bbox_inches='tight')
    plt.show()

def plot_inst_deco_cost_vs_port_distance():
    port_distances = np.linspace(0, 400, 500)
    turbine_capacity = 15
    water_depths = [40, 80]

    # Get the color mapping
    colors = cost_colors()

    fig, axs = plt.subplots(2, 1, figsize=(6, 6), gridspec_kw={'height_ratios': [1, 1]}, sharex=True)

    # Inline formatter functions
    x_axis_formatter = FuncFormatter(lambda x, pos: '0' if x == 0 else f'{x:.0f}')
    y_axis_formatter = FuncFormatter(lambda y, pos: '0' if y == 0 else f'{y:.2f}')

    for i, water_depth in enumerate(water_depths):
        inst_costs, deco_costs = [], []

        for pd in port_distances:
            inst_cost = calc_inst_deco_cost(water_depth, 1e3 * pd, turbine_capacity, "inst")
            deco_cost = calc_inst_deco_cost(water_depth, 1e3 * pd, turbine_capacity, "deco")
            inst_costs.append(inst_cost)
            deco_costs.append(deco_cost)

        axs[i].plot(port_distances, inst_costs, label='Installation Cost', color=colors['Installation Cost'])
        axs[i].plot(port_distances, deco_costs, label='Decommissioning Cost', linestyle='--', color=colors['Decommissioning Cost'])
        
        # Set domain and range
        axs[i].set_xlim(0, 400)
        axs[i].set_ylim(0, 2)

        x_major_locator = MultipleLocator(400/4)
        x_minor_locator = MultipleLocator(400/4/4)
        y_major_locator = MultipleLocator(2/4)
        y_minor_locator = MultipleLocator(2/4/4)

        axs[i].xaxis.set_major_locator(x_major_locator)
        axs[i].xaxis.set_minor_locator(x_minor_locator)
        axs[i].yaxis.set_major_locator(y_major_locator)
        axs[i].yaxis.set_minor_locator(y_minor_locator)

        axs[i].grid(which='major', linestyle='-', linewidth='0.5', color='gray')
        axs[i].grid(which='minor', linestyle=':', linewidth='0.5', color='gray')
        axs[i].minorticks_on()

        # Apply custom formatters to x and y axes
        axs[i].xaxis.set_major_formatter(x_axis_formatter)
        axs[i].yaxis.set_major_formatter(y_axis_formatter)
        
        axs[i].set_ylabel('Cost (M€)')
        
        supp_struct_str = f'Monopile/Jacket' if water_depth < 55 else f'Floating'
        axs[i].text(5, 0.1, supp_struct_str, rotation=90, ha='left', va='bottom')
        
        # Add horizontal text annotation in the top left of the figure
        axs[i].text(5, 1.95, f'$H_{{w}} = {water_depth}$ m', ha='left', va='top')
        
    axs[1].set_xlabel('Distance to Closest Port (km)')
    
    lines, labels = axs[0].get_legend_handles_labels()
    fig.legend(lines, labels, bbox_to_anchor=(0.32, 1.05), loc='center', ncol=1, frameon=False)
    
    plt.tight_layout()
    plt.savefig(f'C:\\Users\\cflde\\Downloads\\wt_cost_vs_port_distance.png', dpi=400, bbox_inches='tight')
    plt.show()

if __name__ == "__main__":

    plot_costs_vs_water_depth()

    plot_inst_deco_cost_vs_port_distance()