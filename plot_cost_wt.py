import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from scripts.cost_functions import present_value

# Define font parameters
font = {'family': 'serif',
        'weight': 'normal',
        'size': 12}

# Set font
plt.rc('font', **font)

def supp_struct_cond(water_depth):
    """
    Determines the support structure type based on water depth.

    Parameters:
        water_depth (float): Water depth at the turbine location.

    Returns:
        str: Support structure type ('monopile', 'jacket', 'floating').
    """
    if water_depth < 25:
        return "monopile"
    elif 25 <= water_depth < 55:
        return "jacket"
    elif 55 <= water_depth:
        return "floating"

def calc_equip_cost(water_depth, support_structure, ice_cover, turbine_capacity):
    """
    Calculates the equipment cost based on water depth, support structure, ice cover, and turbine capacity.

    Parameters:
        water_depth (float): Water depth at the turbine location.
        support_structure (str): Type of support structure.
        ice_cover (int): Indicator if the area is ice-covered (1 for Yes, 0 for No).
        turbine_capacity (float): Capacity of the turbine.

    Returns:
        tuple: Calculated support structure cost and turbine cost.
    """
    support_structure_coeff = {
        'monopile': (181, 552, 370),
        'jacket': (103, -2043, 478),
        'floating': (0, 697, 1223)
    }

    turbine_coeff = 1200 * 1e3  # Coefficient for turbine cost (EU/MW)

    c1, c2, c3 = support_structure_coeff[support_structure]  # Get coefficients for the support structure
    supp_cost = turbine_capacity * (c1 * (water_depth ** 2) + c2 * water_depth + c3 * 1e3)
    
    if ice_cover == 1:
        turbine_coeff *= 1.5714

    turbine_cost = turbine_capacity * turbine_coeff

    return supp_cost, turbine_cost

def calc_inst_deco_cost(water_depth, port_distance, turbine_capacity, operation):
    """
    Calculate installation or decommissioning cost based on the water depth, port distance,
    and rated power of the wind turbines.

    Parameters:
        water_depth (float): Water depth at the turbine location.
        port_distance (float): Distance to the port.
        turbine_capacity (float): Capacity of the turbine.
        operation (str): Type of operation ('installation' or 'decommissioning').

    Returns:
        float: Calculated cost in Euros.
    """
    inst_coeff = {
        'PSIV': ((40 / turbine_capacity), 18.5, 24, 144, 200),
        'Tug': ((1/3), 7.5, 5, 0, 2.5),
        'AHV': (7, 18.5, 30, 90, 40)
    }

    deco_coeff = {
        'PSIV': ((40 / turbine_capacity), 18.5, 24, 144, 200),
        'Tug': ((1/3), 7.5, 5, 0, 2.5),
        'AHV': (7, 18.5, 30, 30, 40)
    }

    coeff = inst_coeff if operation == 'inst' else deco_coeff  # Choose coefficients based on operation type

    support_structure = supp_struct_cond(water_depth)

    if support_structure in ['monopile', 'jacket']:
        c1, c2, c3, c4, c5 = coeff['PSIV']
        total_cost = ((1 / c1) * ((2 * port_distance)/c2 + c3) + c4) * ((c5 * 1e3) / 24)
    elif support_structure == 'floating':
        total_cost = 0
        for vessel_type in ['Tug', 'AHV']:
            c1, c2, c3, c4, c5 = coeff[vessel_type]
            vessel_cost = ((1 / c1) * ((2 * port_distance)/c2 + c3) + c4) * ((c5 * 1e3) / 24)
            total_cost += vessel_cost

    return total_cost

def calculate_costs(water_depth, ice_cover, port_distance, turbine_capacity):
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
    support_structure = supp_struct_cond(water_depth)  # Determine support structure

    supp_cost, turbine_cost = calc_equip_cost(water_depth, support_structure, ice_cover, turbine_capacity)  # Calculate equipment cost

    equip_cost = supp_cost + turbine_cost
    
    inst_cost = calc_inst_deco_cost(water_depth, port_distance, turbine_capacity, "inst")  # Calculate installation cost
    deco_cost = calc_inst_deco_cost(water_depth, port_distance, turbine_capacity, "deco")  # Calculate decommissioning cost

    ope_cost_yearly = 0.025 * turbine_cost  # Calculate yearly operational cost

    total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost = present_value(equip_cost, inst_cost, ope_cost_yearly, deco_cost)  # Calculate present value of cost

    total_cost *= 1e-6  # Convert cost to millions of Euros
    equip_cost *= 1e-6
    inst_cost *= 1e-6
    total_ope_cost *= 1e-6
    deco_cost *= 1e-6

    return total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost

def plot_costs_vs_water_depth():
    water_depths = np.linspace(0, 120, 500)
    ice_cover = 0  # Assuming no ice cover for simplicity
    port_distance = 100  # Assuming a constant port distance for simplicity
    turbine_capacity = 15  # Assuming a constant turbine capacity of 15 MW

    total_costs, equip_costs, inst_costs, total_ope_costs, deco_costs = [], [], [], [], []

    for wd in water_depths:
        total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost = calculate_costs(wd, ice_cover, port_distance, turbine_capacity)
        total_costs.append(total_cost)
        equip_costs.append(equip_cost)
        inst_costs.append(inst_cost)
        total_ope_costs.append(total_ope_cost)
        deco_costs.append(deco_cost)

    fig, axs = plt.subplots(2, 1, figsize=(6, 6), gridspec_kw={'height_ratios': [4, 1]}, sharex=True)
    
    # Plotting the larger range
    axs[0].plot(water_depths, total_costs, label='Total PV')
    axs[0].plot(water_depths, equip_costs, label='Equipment PV')
    axs[0].plot(water_depths, inst_costs, label='Installation PV')
    axs[0].plot(water_depths, total_ope_costs, label='Total Operating PV')
    axs[0].plot(water_depths, deco_costs, label='Decommissioning PV')

    axs[0].set_xlim(0, 120)
    axs[0].set_ylim(0, 50)
    axs[0].yaxis.set_major_locator(MultipleLocator(10))
    axs[0].yaxis.set_minor_locator(MultipleLocator(2.5))

    # Plotting the smaller range
    axs[1].plot(water_depths, total_costs, label='Total PV')
    axs[1].plot(water_depths, equip_costs, label='Equipment PV')
    axs[1].plot(water_depths, inst_costs, label='Installation PV')
    axs[1].plot(water_depths, total_ope_costs, label='Total Operating PV')
    axs[1].plot(water_depths, deco_costs, label='Decommissioning PV')

    axs[0].set_xlim(0, 120)
    axs[1].set_ylim(0, 2)
    axs[1].yaxis.set_major_locator(MultipleLocator(1))
    axs[1].yaxis.set_minor_locator(MultipleLocator(0.25))

    for ax in axs:
        ax.xaxis.set_major_locator(MultipleLocator(20))
        ax.xaxis.set_minor_locator(MultipleLocator(5))
        ax.grid(which='major', linestyle='-', linewidth='0.5', color='gray')
        ax.grid(which='minor', linestyle=':', linewidth='0.5', color='gray')
        ax.minorticks_on()
        
        ax.axvline(x=25, color='grey', linewidth='1.5', linestyle='--')
        ax.axvline(x=55, color='grey', linewidth='1.5', linestyle='--')
        
    axs[0].text(2, 2, 'Monopile', rotation=90)
    axs[0].text(27, 2, 'Jacket', rotation=90)
    axs[0].text(57, 2, 'Floating', rotation=90)

    axs[1].set_xlabel('Water Depth (m)')
    axs[0].set_ylabel('Cost (M€)')
    axs[1].set_ylabel('Cost (M€)')

    lines, labels = axs[0].get_legend_handles_labels()
    fig.legend(lines, labels, bbox_to_anchor=(0.5, 1.02), loc='center', ncol=2, frameon=False)
    
    plt.tight_layout()
    plt.savefig(f'C:\\Users\\cflde\\Downloads\\wt_total_cost_vs_water_depth.png', dpi=400, bbox_inches='tight')
    plt.show()

def plot_equip_costs_vs_water_depth():
    water_depths = np.linspace(0, 120, 500)
    ice_cover = 0  # Assuming no ice cover for simplicity
    turbine_capacity = 15  # Assuming a constant turbine capacity of 5 MW

    supp_costs, turbine_costs, equip_costs = [], [], []

    for wd in water_depths:
        support_structure = supp_struct_cond(wd)
        supp_cost, turbine_cost = calc_equip_cost(wd, support_structure, ice_cover, turbine_capacity)
        equip_cost = supp_cost + turbine_cost
        supp_costs.append(supp_cost * 1e-6)  # Convert to millions of Euros
        turbine_costs.append(turbine_cost * 1e-6)  # Convert to millions of Euros
        equip_costs.append(equip_cost * 1e-6)  # Convert to millions of Euros

    plt.figure(figsize=(6, 5))
    plt.plot(water_depths, equip_costs, label='Total Equipment Cost')
    plt.plot(water_depths, supp_costs, label='Support Structure Cost')
    plt.plot(water_depths, turbine_costs, label='Turbine Equipment Cost')
    plt.xlabel('Water Depth (m)')
    plt.ylabel('Cost (M\u20AC)')

    # Set domain and range
    plt.xlim(0, 120)
    plt.ylim(0, 50)

    x_major_locator = MultipleLocator(20)
    x_minor_locator = MultipleLocator(5)
    y_major_locator = MultipleLocator(10)
    y_minor_locator = MultipleLocator(2.5)

    plt.gca().xaxis.set_major_locator(x_major_locator)
    plt.gca().xaxis.set_minor_locator(x_minor_locator)
    plt.gca().yaxis.set_major_locator(y_major_locator)
    plt.gca().yaxis.set_minor_locator(y_minor_locator)

    plt.grid(which='major', linestyle='-', linewidth='0.5', color='gray')
    plt.grid(which='minor', linestyle=':', linewidth='0.5', color='gray')
    plt.minorticks_on()
    
    # Add vertical lines for support structure domains
    plt.axvline(x=25, color='grey', linewidth='1.5', linestyle='--')
    plt.axvline(x=55, color='grey', linewidth='1.5', linestyle='--')
    
    # Add vertical text annotations
    plt.text(2, 2, 'Monopile', rotation=90)
    plt.text(27, 2, 'Jacket', rotation=90)
    plt.text(57, 2, 'Floating', rotation=90)

    plt.legend(bbox_to_anchor=(0, 1.25), loc='upper left', ncol=1, frameon=False)
    plt.grid(True)
    plt.savefig(f'C:\\Users\\cflde\\Downloads\\wt_equip_cost_vs_water_depth.png', dpi=400, bbox_inches='tight')
    plt.show()

def plot_inst_deco_cost_vs_port_distance():
    port_distances = np.linspace(0, 200, 100)
    turbine_capacity = 15
    water_depths = [40, 80]

    fig, axs = plt.subplots(2, 1, figsize=(6, 6), gridspec_kw={'height_ratios': [1, 1]}, sharex=True)
    
    for i, water_depth in enumerate(water_depths):
        inst_costs, deco_costs = [], []

        for pd in port_distances:
            inst_cost = calc_inst_deco_cost(water_depth, pd, turbine_capacity, "inst")
            deco_cost = calc_inst_deco_cost(water_depth, pd, turbine_capacity, "deco")
            inst_costs.append(inst_cost * 1e-6)  # Convert to millions of Euros
            deco_costs.append(deco_cost * 1e-6)  # Convert to millions of Euros

        axs[i].plot(port_distances, inst_costs, label='Installation Cost')
        axs[i].plot(port_distances, deco_costs, label='Decommissioning Cost')
        
        # Set domain and range
        axs[i].set_xlim(0, 200)
        axs[i].set_ylim(0, 2)

        x_major_locator = MultipleLocator(20)
        x_minor_locator = MultipleLocator(5)
        y_major_locator = MultipleLocator(0.5)
        y_minor_locator = MultipleLocator(0.125)

        axs[i].xaxis.set_major_locator(x_major_locator)
        axs[i].xaxis.set_minor_locator(x_minor_locator)
        axs[i].yaxis.set_major_locator(y_major_locator)
        axs[i].yaxis.set_minor_locator(y_minor_locator)

        axs[i].grid(which='major', linestyle='-', linewidth='0.5', color='gray')
        axs[i].grid(which='minor', linestyle=':', linewidth='0.5', color='gray')
        axs[i].minorticks_on()

        axs[i].set_ylabel('Cost (M€)')
        
        supp_struct_str = f'Monopile/Jacket' if water_depth < 55 else f'Floating'
        axs[i].text(2, 0.05, supp_struct_str, rotation=90, ha='left', va='bottom')
        
        # Add horizontal text annotation in the top left of the figure
        axs[i].text(2, 1.95, f'$WD ={water_depth}m$', ha='left', va='top')
        
    axs[1].set_xlabel('Distance to Closest Port (km)')
    
    lines, labels = axs[0].get_legend_handles_labels()
    fig.legend(lines, labels, bbox_to_anchor=(0.5, 1.02), loc='center', ncol=2, frameon=False)
    
    plt.tight_layout()
    plt.savefig(f'C:\\Users\\cflde\\Downloads\\wt_cost_vs_port_distance_{supp_struct_str.replace("/","-")}.png', dpi=400, bbox_inches='tight')
    plt.show()

plot_costs_vs_water_depth()

plot_equip_costs_vs_water_depth()

plot_inst_deco_cost_vs_port_distance()