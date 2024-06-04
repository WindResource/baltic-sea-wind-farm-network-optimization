import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

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

def iac_cost_lin(distance, capacity):
    """
    Calculate the total cost of an inter array cable section for a given distance and desired capacity.

    Parameters:
        distance (float): The distance of the cable (in meters).
        capacity (float): Cable capacity (in MW).

    Returns:
        float: Total cost associated with the selected HVAC cables in millions of euros.
    """
    cable_length = 1.05 * distance
    cable_capacity = 80 # MW
    cable_equip_cost = 0.152 # MEU/km
    cable_inst_cost = 0.114 # MEU/km
    capacity_factor = 0.98
    
    parallel_cables = np.ceil(capacity / (cable_capacity * capacity_factor))
    
    equip_cost = parallel_cables * cable_length * cable_equip_cost
    inst_cost = parallel_cables * cable_length * cable_inst_cost

    return equip_cost, inst_cost

def calc_total_cost_iac(distance, capacity):
    
    equip_cost, inst_cost = iac_cost_lin(distance, capacity)
    
    ope_cost_yearly = 0.002 * equip_cost
    
    deco_cost = 0.5 * inst_cost

    # Calculate present value
    total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost = present_value(equip_cost, inst_cost, ope_cost_yearly, deco_cost)
    
    return total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost


def plot_costs_vs_distance(capacity):
    distances = np.linspace(0, 5, 100)  # Distances in km

    total_costs, equip_costs, inst_costs, total_ope_costs, deco_costs = [], [], [], [], []

    for distance in distances:
        total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost = calc_total_cost_iac(distance, capacity)
        total_costs.append(total_cost)
        equip_costs.append(equip_cost)
        inst_costs.append(inst_cost)
        total_ope_costs.append(total_ope_cost)
        deco_costs.append(deco_cost)

    plt.figure(figsize=(7.5, 5))
    plt.plot(distances, total_costs, label='Total Cost')
    plt.plot(distances, equip_costs, label='Equipment Cost')
    plt.plot(distances, inst_costs, label='Installation Cost')
    plt.plot(distances, total_ope_costs, label='Total Operational Cost')
    plt.plot(distances, deco_costs, label='Decommissioning Cost')

    plt.xlim(0, 5)
    plt.ylim(0, max(total_costs + equip_costs + inst_costs + total_ope_costs + deco_costs) * 1.1)

    x_major_locator = MultipleLocator(1)
    x_minor_locator = MultipleLocator(0.25)
    y_major_locator = MultipleLocator(0.5)
    y_minor_locator = MultipleLocator(0.25)

    plt.gca().xaxis.set_major_locator(x_major_locator)
    plt.gca().xaxis.set_minor_locator(x_minor_locator)
    plt.gca().yaxis.set_major_locator(y_major_locator)
    plt.gca().yaxis.set_minor_locator(y_minor_locator)

    plt.minorticks_on()
    plt.grid(which='major', linestyle='-', linewidth='0.5', color='gray')
    plt.grid(which='minor', linestyle=':', linewidth='0.5', color='gray')

    plt.xlabel('Distance (km)')
    plt.ylabel('Cost (M\u20AC)')
    plt.legend(bbox_to_anchor=(0, 1.25), loc='upper left', ncol=2, frameon=False)
    plt.savefig(f'C:\\Users\\cflde\\Downloads\\iac_cost_vs_distance.png', dpi=400, bbox_inches='tight')
    plt.show()

def plot_costs_vs_capacity(distance):
    capacities = np.linspace(0, 500, 1000)  # Capacities in MW

    total_costs, equip_costs, inst_costs, total_ope_costs, deco_costs = [], [], [], [], []

    for capacity in capacities:
        total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost = calc_total_cost_iac(distance, capacity)
        total_costs.append(total_cost)
        equip_costs.append(equip_cost)
        inst_costs.append(inst_cost)
        total_ope_costs.append(total_ope_cost)
        deco_costs.append(deco_cost)

    plt.figure(figsize=(7.5, 5))
    plt.plot(capacities, total_costs, label='Total PV')
    plt.plot(capacities, equip_costs, label='Equipment PV')
    plt.plot(capacities, inst_costs, label='Installation PV')
    plt.plot(capacities, total_ope_costs, label='Total Operating PV')
    plt.plot(capacities, deco_costs, label='Decommissioning PV')

    plt.xlim(0, 500)
    plt.ylim(0, max(total_costs + equip_costs + inst_costs + total_ope_costs + deco_costs) * 1.1)

    x_major_locator = MultipleLocator(100)
    x_minor_locator = MultipleLocator(25)
    y_major_locator = MultipleLocator(0.5)
    y_minor_locator = MultipleLocator(0.25)

    plt.gca().xaxis.set_major_locator(x_major_locator)
    plt.gca().xaxis.set_minor_locator(x_minor_locator)
    plt.gca().yaxis.set_major_locator(y_major_locator)
    plt.gca().yaxis.set_minor_locator(y_minor_locator)

    plt.minorticks_on()
    plt.grid(which='major', linestyle='-', linewidth='0.5', color='gray')
    plt.grid(which='minor', linestyle=':', linewidth='0.5', color='gray')

    plt.xlabel('Capacity (MW)')
    plt.ylabel('Cost (M\u20AC)')
    plt.legend(bbox_to_anchor=(0, 1.25), loc='upper left', ncol=2, frameon=False)
    plt.savefig(f'C:\\Users\\cflde\\Downloads\\iac_cost_vs_capacity.png', dpi=400, bbox_inches='tight')
    plt.show()


# Call the function to plot the costs for a given capacity
plot_costs_vs_distance(150)

# Call the function to plot the costs for a given distance
plot_costs_vs_capacity(1)