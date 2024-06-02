import numpy as np
import matplotlib.pyplot as plt

# Define font parameters
font = {'family': 'serif',
        'weight': 'normal',
        'size': 12}

# Set font
plt.rc('font', **font)

def present_value(equip_cost, inst_cost, ope_cost_yearly, deco_cost):
    """
    Calculate the total present value of cable cost.

    Parameters:
        equip_cost (float): Equipment cost.
        inst_cost (float): Installation cost.
        ope_cost_yearly (float): Yearly operational cost.
        deco_cost (float): Decommissioning cost.

    Returns:
        float: Total present value of cost.
    """
    # Define years for installation, operational, and decommissioning
    inst_year = 0  # First year (installation year)
    ope_year = inst_year + 5  # Operational costs start year
    dec_year = ope_year + 25  # Decommissioning year
    end_year = dec_year + 2  # End year

    # Discount rate
    discount_rate = 0.05

    # Initialize total operational cost
    total_ope_cost = 0

    # Adjust cost for each year
    for year in range(inst_year, end_year + 1):
        discount_factor = (1 + discount_rate) ** -year  # Calculate the discount factor for the year
        if year == inst_year:
            equip_cost *= discount_factor  # Discount equipment cost for the installation year
            inst_cost *= discount_factor  # Discount installation cost for the installation year
        elif ope_year <= year < dec_year:
            total_ope_cost += ope_cost_yearly * discount_factor  # Accumulate discounted operational cost for each year
        elif year == dec_year:
            deco_cost *= discount_factor  # Discount decommissioning cost for the decommissioning year

    # Calculate total present value of cost
    total_cost = equip_cost + inst_cost + total_ope_cost + deco_cost

    return total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost

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
        supp_cost *= 1.10  # Increase cost by 10% if ice cover is present

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
        'PSIV': (40 / turbine_capacity, 18.5, 24, 144, 200),
        'Tug': (0.3, 7.5, 5, 0, 2.5),
        'AHV': (7, 18.5, 30, 90, 40)
    }

    deco_coeff = {
        'PSIV': (40 / turbine_capacity, 18.5, 24, 144, 200),
        'Tug': (0.3, 7.5, 5, 0, 2.5),
        'AHV': (7, 18.5, 30, 30, 40)
    }

    coeff = inst_coeff if operation == 'inst' else deco_coeff  # Choose coefficients based on operation type

    support_structure = supp_struct_cond(water_depth)

    if support_structure in ['monopile', 'jacket']:
        c1, c2, c3, c4, c5 = coeff['PSIV']
        total_cost = ((1 / c1) * ((2 * port_distance) / c2 + c3) + c4) * ((c5 * 1e3) / 24)
    elif support_structure == 'floating':
        total_cost = 0
        for vessel_type in ['Tug', 'AHV']:
            c1, c2, c3, c4, c5 = coeff[vessel_type]
            vessel_cost = ((1 / c1) * ((2 * port_distance) / c2 + c3) + c4) * ((c5 * 1e3) / 24)
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

    plt.figure(figsize=(9, 6))
    plt.plot(water_depths, supp_costs, label='Support Structure Cost')
    plt.plot(water_depths, turbine_costs, label='Turbine Equipment Cost')
    plt.plot(water_depths, equip_costs, label='Total Equipment Cost')
    plt.xlabel('Water Depth (m)')
    plt.ylabel('Cost (M\u20AC)')

    # Set domain and range
    plt.xlim(0, 120)
    plt.ylim(0, max(max(supp_costs), max(turbine_costs), max(equip_costs)) * 1.1)

    plt.grid(which='major', linestyle='-', linewidth='0.5', color='gray')
    plt.grid(which='minor', linestyle=':', linewidth='0.5', color='gray')
    plt.minorticks_on()
    
    # Add vertical lines for support structure domains
    plt.axvline(x=25, color='grey', linewidth='1.5', linestyle='--')
    plt.axvline(x=55, color='grey', linewidth='1.5', linestyle='--')
    
    # Add vertical text annotations
    plt.text(1, plt.ylim()[1] * 0.05, 'Monopile', rotation=90)
    plt.text(26, plt.ylim()[1] * 0.05, 'Jacket', rotation=90)
    plt.text(56, plt.ylim()[1] * 0.05, 'Floating', rotation=90)

    plt.legend()
    plt.grid(True)
    plt.savefig(r'C:\\Users\\cflde\\Downloads\\plot_equip_costs_vs_water_depth.png', dpi=400)
    plt.show()

def plot_inst_deco_cost_vs_port_distance():
    port_distances = np.linspace(0, 200, 100)
    water_depth = 50  # Assuming a constant water depth
    turbine_capacity = 5  # Assuming a constant turbine capacity of 5 MW

    inst_costs, deco_costs = [], []

    for pd in port_distances:
        inst_cost = calc_inst_deco_cost(water_depth, pd, turbine_capacity, "inst")
        deco_cost = calc_inst_deco_cost(water_depth, pd, turbine_capacity, "deco")
        inst_costs.append(inst_cost * 1e-6)  # Convert to millions of Euros
        deco_costs.append(deco_cost * 1e-6)  # Convert to millions of Euros

    plt.figure(figsize=(9, 6))
    plt.plot(port_distances, inst_costs, label='Installation Cost')
    plt.plot(port_distances, deco_costs, label='Decommissioning Cost')
    
    # Set domain and range
    plt.xlim(0, 200)
    plt.ylim(0, max(max(inst_costs), max(deco_costs)) * 1.5)

    plt.grid(which='major', linestyle='-', linewidth='0.5', color='gray')
    plt.grid(which='minor', linestyle=':', linewidth='0.5', color='gray')
    plt.minorticks_on()

    supp_struct_str = 'Monopile/Jacket' if water_depth < 55 else 'Floating'
    
    # Add vertical text annotations
    plt.text(1, plt.ylim()[1] * 0.05, supp_struct_str, rotation=90)

    plt.xlabel('Distance to Closest Port (km)')
    plt.ylabel('Cost (M\u20AC)')
    plt.legend()
    plt.grid(True)
    plt.savefig(r'C:\\Users\\cflde\\Downloads\\plot_inst_deco_cost_vs_port_distance.png', dpi=400)
    plt.show()

plot_equip_costs_vs_water_depth()
plot_inst_deco_cost_vs_port_distance()