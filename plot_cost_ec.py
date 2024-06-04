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

def ec1_cost_lin(distance, capacity):
    """
    Calculate the cost associated with selecting export cables for a given length, desired capacity,
    and desired voltage.

    Parameters:
        length (float): The length of the cable (in meters).
        desired_capacity (float): The desired capacity of the cable (in watts).
        desired_voltage (int): The desired voltage of the cable (in kilovolts).

    Returns:
        tuple: A tuple containing the equipment cost, installation cost, and total cost
                associated with the selected HVAC cables.
    """

    cable_length = 1.1 * distance
    cable_capacity = 348 # MW
    cable_equip_cost = 0.860 #Meu/km
    cable_inst_cost = 0.540 #Meu/km
    capacity_factor = 0.95
    
    parallel_cables = capacity / (cable_capacity * capacity_factor) + 0.5
    
    equip_cost = parallel_cables * cable_length * cable_equip_cost
    inst_cost = parallel_cables * cable_length * cable_inst_cost
    
    ope_cost_yearly = 0.2 * 1e-2 * equip_cost
    
    deco_cost = 0.5 * inst_cost

    # Calculate present value
    total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost = present_value(equip_cost, inst_cost, ope_cost_yearly, deco_cost)
    
    return total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost

def ec1_cost_ceil(distance, capacity):
    """
    Calculate the cost associated with selecting export cables for a given length, desired capacity,
    and desired voltage.

    Parameters:
        length (float): The length of the cable (in meters).
        desired_capacity (float): The desired capacity of the cable (in watts).
        desired_voltage (int): The desired voltage of the cable (in kilovolts).

    Returns:
        tuple: A tuple containing the equipment cost, installation cost, and total cost
                associated with the selected HVAC cables.
    """

    cable_length = 1.1 * distance
    cable_capacity = 348 # MW
    cable_equip_cost = 0.860 #Meu/km
    cable_inst_cost = 0.540 #Meu/km
    capacity_factor = 0.95
    
    parallel_cables = np.ceil(capacity / (cable_capacity * capacity_factor))
    
    equip_cost = parallel_cables * cable_length * cable_equip_cost
    inst_cost = parallel_cables * cable_length * cable_inst_cost
    
    ope_cost_yearly = 0.002 * equip_cost
    
    deco_cost = 0.5 * inst_cost

    # Calculate present value
    total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost = present_value(equip_cost, inst_cost, ope_cost_yearly, deco_cost)
    
    return total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost

def ec2_cost_lin(distance, capacity):
    """
    Calculate the cost associated with selecting export cables for a given length, desired capacity,
    and desired voltage.
    """

    cable_length = 1.2 * distance
    cable_capacity = 348 # MW
    cable_equip_cost = 0.860 # Million EU/km
    cable_inst_cost = 0.540 # Million EU/km
    capacity_factor = 0.90
    
    parallel_cables = capacity / (cable_capacity * capacity_factor) + 0.5
    
    equip_cost = parallel_cables * cable_length * cable_equip_cost
    inst_cost = parallel_cables * cable_length * cable_inst_cost

    ope_cost_yearly = 0.2 * 1e-2 * equip_cost
    
    deco_cost = 0.5 * inst_cost

    # Calculate present value
    total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost = present_value(equip_cost, inst_cost, ope_cost_yearly, deco_cost)
    
    return total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost

def ec2_cost_ceil(distance, capacity):
    """
    Calculate the cost associated with selecting export cables for a given length, desired capacity,
    and desired voltage.
    """

    cable_length = 1.2 * distance
    cable_capacity = 348 # MW
    cable_equip_cost = 0.860 # Million EU/km
    cable_inst_cost = 0.540 # Million EU/km
    capacity_factor = 0.90
    
    parallel_cables = np.ceil(capacity / (cable_capacity * capacity_factor))
    
    equip_cost = parallel_cables * cable_length * cable_equip_cost
    inst_cost = parallel_cables * cable_length * cable_inst_cost

    ope_cost_yearly = 0.2 * 1e-2 * equip_cost
    
    deco_cost = 0.5 * inst_cost

    # Calculate present value
    total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost = present_value(equip_cost, inst_cost, ope_cost_yearly, deco_cost)
    
    return total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost

def plot_cost_vs_distance(capacity, ec):
    distances = np.linspace(0, 300, 500)  # Distances in km

    total_costs, equip_costs, inst_costs, total_ope_costs, deco_costs = [], [], [], [], []

    for distance in distances:
        if ec == 1:
            total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost = ec1_cost_ceil(distance, capacity)
        else:
            total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost = ec2_cost_ceil(distance, capacity)

        total_costs.append(total_cost)
        equip_costs.append(equip_cost)
        inst_costs.append(inst_cost)
        total_ope_costs.append(total_ope_cost)
        deco_costs.append(deco_cost)

    plt.figure(figsize=(7, 5))
    plt.plot(distances, total_costs, label='Total PV')
    plt.plot(distances, equip_costs, label='Equipment PV')
    plt.plot(distances, inst_costs, label='Installation PV')
    plt.plot(distances, total_ope_costs, label='Total Operating PV')
    plt.plot(distances, deco_costs, label='Decommissioning PV')

    plt.xlim(0, 300)
    plt.ylim(0, max(total_costs + equip_costs + inst_costs + total_ope_costs + deco_costs) * 1.1)

    x_major_locator = MultipleLocator(50)
    x_minor_locator = MultipleLocator(12.5)
    y_major_locator = MultipleLocator(200)
    y_minor_locator = MultipleLocator(50)

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
    plt.savefig(f'C:\\Users\\cflde\\Downloads\\ec{ec}_cost_vs_distance.png', dpi=400, bbox_inches='tight')
    plt.show()

def plot_cost_vs_capacity(distance, ec):
    capacities = np.linspace(0, 2000, 500)  # Capacities in MW

    total_costs, equip_costs, inst_costs, total_ope_costs, deco_costs = [], [], [], [], []
    
    total_costs_lin, equip_costs_lin, inst_costs_lin, total_ope_costs_lin, deco_costs_lin = [], [], [], [], []

    for capacity in capacities:
        if ec == 1:
            total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost = ec1_cost_ceil(distance, capacity)
            total_cost_lin, equip_cost_lin, inst_cost_lin, total_ope_cost_lin, deco_cost_lin = ec1_cost_lin(distance, capacity)
        else:
            total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost = ec2_cost_ceil(distance, capacity)
            total_cost_lin, equip_cost_lin, inst_cost_lin, total_ope_cost_lin, deco_cost_lin = ec2_cost_lin(distance, capacity)
        
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

    plt.figure(figsize=(7, 5))
    # Plot the solid lines
    line1, = plt.plot(capacities, total_costs, label='Total PV')
    line2, = plt.plot(capacities, equip_costs, label='Equipment PV')
    line3, = plt.plot(capacities, inst_costs, label='Installation PV')
    line4, = plt.plot(capacities, total_ope_costs, label='Total Operating PV')
    line5, = plt.plot(capacities, deco_costs, label='Decommissioning PV')
    
    # Plot the dashed lines using colors from the solid lines
    plt.plot(capacities, total_costs_lin, label='Total PV (cont.)', color=line1.get_color(), linestyle="--")
    plt.plot(capacities, equip_costs_lin, label='Equipment PV (cont.)', color=line2.get_color(), linestyle="--")
    plt.plot(capacities, inst_costs_lin, label='Installation PV (cont.)', color=line3.get_color(), linestyle="--")
    plt.plot(capacities, total_ope_costs_lin, label='Total Operating PV (cont.)', color=line4.get_color(), linestyle="--")
    plt.plot(capacities, deco_costs_lin, label='Decommissioning PV (cont.)', color=line5.get_color(), linestyle="--")

    plt.xlim(0, 2000)
    plt.ylim(0, max(total_costs + equip_costs + inst_costs + total_ope_costs + deco_costs) * 1.1)

    x_major_locator = MultipleLocator(250)
    x_minor_locator = MultipleLocator(25)
    y_major_locator = MultipleLocator(200)
    y_minor_locator = MultipleLocator(50)

    plt.gca().xaxis.set_major_locator(x_major_locator)
    plt.gca().xaxis.set_minor_locator(x_minor_locator)
    plt.gca().yaxis.set_major_locator(y_major_locator)
    plt.gca().yaxis.set_minor_locator(y_minor_locator)

    plt.minorticks_on()
    plt.grid(which='major', linestyle='-', linewidth='0.5', color='gray')
    plt.grid(which='minor', linestyle=':', linewidth='0.5', color='gray')

    plt.xlabel('Capacity (MW)')
    plt.ylabel('Cost (M\u20AC)')
    plt.legend(bbox_to_anchor=(0, 1.4), loc='upper left', ncol=2, frameon=False)
    plt.savefig(f'C:\\Users\\cflde\\Downloads\\ec{ec}_cost_vs_capacity.png', dpi=400, bbox_inches='tight')
    plt.show()


# Call the function to plot the costs for a given capacity
plot_cost_vs_distance(1000, 1)  # Example capacity in MW
plot_cost_vs_distance(1000, 2)


# Call the function to plot the costs for a given distance
plot_cost_vs_capacity(100, 1)  # Example distance in km
plot_cost_vs_capacity(100, 2)