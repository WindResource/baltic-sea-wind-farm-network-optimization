"""
Wind Farm Optimization Model Setup

This script sets up and solves an optimization problem for selecting wind farms, offshore substations,
and their connections to minimize total costs while adhering to operational constraints. It considers
the costs of selecting wind farms and substations, plus the costs associated with connecting these
entities based on distances. It ensures configurations meet specified requirements, including
connection feasibility, capacity limitations, and distance constraints.

- generate_connections_and_costs(wind_farms, offshore_ss, onshore_ss, cost_per_distance_unit): Generates
    possible connections between entities and calculates associated costs based on distances.
    Parameters:
    - wind_farms (dict): Dictionary of wind farms with 'coordinates'.
    - offshore_ss (dict): Dictionary of offshore substations with 'coordinates'.
    - onshore_ss (dict): Dictionary of onshore substations with 'coordinates'.
    - cost_per_distance_unit (float): Cost factor per unit of distance (e.g., per kilometer).
    Returns:
    - tuple of (dict, dict): Two dictionaries, one for connection costs and one for distances, 
    with tuple keys representing connections (e.g., ('WF1', 'OSS1')).

- add_constraints(model, wind_farms, offshore_ss, onshore_ss, connections_costs, distances,
        min_total_capacity, max_wf_oss_dist, max_oss_ss_dist, universal_offshore_ss_max_capacity):
    Adds operational constraints to the optimization model, including capacity and distance limitations.
    Parameters:
    - model (ConcreteModel): The Pyomo model.
    - wind_farms (dict): Dictionary of wind farms.
    - offshore_ss (dict): Dictionary of offshore substations.
    - onshore_ss (dict): Dictionary of onshore substations.
    - connections_costs (dict): Dictionary of connection costs.
    - distances (dict): Dictionary of distances between entities.
    - min_total_capacity (float): Minimum total capacity requirement for selected wind farms.
    - max_wf_oss_dist (float): Maximum allowed distance from wind farms to offshore substations.
    - max_oss_ss_dist (float): Maximum allowed distance from offshore substations to onshore substations.
    - universal_offshore_ss_max_capacity (float): Maximum capacity for any offshore substation.
    
The optimization model is solved using Pyomo with GLPK as the solver. The solution includes selected
wind farms, offshore substations, and connections between them, adhering to defined constraints.
"""

import math
from pyomo.environ import *
import numpy as np

def present_value(equip_costs, inst_costs, ope_costs_yearly, deco_costs):
    """
    Calculate the total present value of cable costs.

    Parameters:
        equip_costs (float): Equipment costs.
        inst_costs (float): Installation costs.
        ope_costs_yearly (float): Yearly operational costs.
        deco_costs (float): Decommissioning costs.

    Returns:
        tuple: A tuple containing the equipment costs, installation costs, and total present value of costs.
    """
    # Define years for installation, operational, and decommissioning
    inst_year = 0  # First year
    ope_year = inst_year + 5
    dec_year = ope_year + 25  
    end_year = dec_year + 2  # End year

    # Discount rate
    discount_rate = 0.05

    # Define the years as a function of inst_year and end_year
    years = range(inst_year, end_year + 1)

    # Initialize total operational costs
    ope_costs = 0
    
    # Adjust costs for each year
    for year in years:
        # Adjust installation costs
        if year == inst_year:
            equip_costs *= (1 + discount_rate) ** -year
            inst_costs *= (1 + discount_rate) ** -year
        # Adjust operational costs
        if year >= inst_year and year < ope_year:
            inst_costs *= (1 + discount_rate) ** -year
        elif year >= ope_year and year < dec_year:
            ope_costs_yearly *= (1 + discount_rate) ** -year
            ope_costs += ope_costs_yearly  # Accumulate yearly operational costs
        # Adjust decommissioning costs
        if year >= dec_year and year <= end_year:
            deco_costs *= (1 + discount_rate) ** -year

    # Calculate total present value of costs
    total_costs = equip_costs + inst_costs + ope_costs + deco_costs

    return total_costs

def haversine_distance_scalar(lon1, lat1, lon2, lat2):
    """
    Calculate the Haversine distance between two sets of coordinates.

    Parameters:
        lon1 (float): Longitude of the first coordinate.
        lat1 (float): Latitude of the first coordinate.
        lon2 (float): Longitude of the second coordinate.
        lat2 (float): Latitude of the second coordinate.

    Returns:
        float: Haversine distance in meters.
    """
    # Radius of the Earth in meters
    r = 6371 * 1e3
    
    # Convert latitude and longitude from degrees to radians
    lon1, lat1, lon2, lat2 = np.radians(lon1), np.radians(lat1), np.radians(lon2), np.radians(lat2)

    # Calculate differences in coordinates
    dlon = lon2 - lon1
    dlat = lat2 - lat1

    # Apply Haversine formula
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))

    # Calculate the distance
    distance = c * r 

    return distance

def export_cable_costs(distance, required_active_power, polarity = "AC"):
    """
    Calculate the costs associated with selecting export cables for a given length, desired capacity,
    and desired voltage.

    Parameters:
        length (float): The length of the cable (in meters).
        desired_capacity (float): The desired capacity of the cable (in watts).
        desired_voltage (int): The desired voltage of the cable (in kilovolts).

    Returns:
        tuple: A tuple containing the equipment costs, installation costs, and total costs
                associated with the selected HVAC cables.
    """

    length = 1.2 * distance
    
    required_active_power *= 1e6 # (MW > W)
    required_voltage = 400
    
    # Define data_tuples where each column represents (tension, section, resistance, capacitance, ampacity, cost, inst_cost)
    cable_data = [
        (132, 630, 39.5, 209, 818, 406, 335),
        (132, 800, 32.4, 217, 888, 560, 340),
        (132, 1000, 27.5, 238, 949, 727, 350),
        (220, 500, 48.9, 136, 732, 362, 350),
        (220, 630, 39.1, 151, 808, 503, 360),
        (220, 800, 31.9, 163, 879, 691, 370),
        (220, 1000, 27.0, 177, 942, 920, 380),
        (400, 800, 31.4, 130, 870, 860, 540),
        (400, 1000, 26.5, 140, 932, 995, 555),
        (400, 1200, 22.1, 170, 986, 1130, 570),
        (400, 1400, 18.9, 180, 1015, 1265, 580),
        (400, 1600, 16.6, 190, 1036, 1400, 600),
        (400, 2000, 13.2, 200, 1078, 1535, 615)
    ]

    # Convert data_tuples to a NumPy array
    data_array = np.array(cable_data)
    
    # Filter data based on desired voltage
    data_array = data_array[data_array[:, 0] >= required_voltage]

    # Define the scaling factors for each column: 
    """
    Voltage (kV) > (V)
    Section (mm^2) > (m^2)
    Resistance (mΩ/km) > (Ω/m)
    Capacitance (nF/km) > (F/m)
    Ampacity (A)
    Equipment cost (eu/m)
    Installation cost (eu/m)
    """
    scaling_factors = np.array([1e3, 1e-6, 1e-6, 1e-12, 1, 1, 1])

    # Apply scaling to each column in data_array
    data_array *= scaling_factors

    power_factor = 0.90
    cable_count = []  # To store the number of cables and corresponding cable data

    for cable in data_array:
        voltage, resistance, capacitance, ampacity = cable[0], cable[2], cable[3], cable[4]
        nominal_power_per_cable = voltage * ampacity
        if polarity == "AC": # Three phase AC
            ac_apparent_power = required_active_power / power_factor
            # Determine number of cables needed based on required total apparent power
            n_cables = np.ceil(ac_apparent_power / nominal_power_per_cable)
            
            current = ac_apparent_power / voltage
            
        else:  # Assuming polarity == "DC"
            # Determine number of cables needed based on required power
            n_cables = np.ceil(required_active_power / nominal_power_per_cable)
            
            current = required_active_power / voltage
        
        resistive_losses = current ** 2 * resistance * length / n_cables
        power_eff = (resistive_losses / required_active_power)
        
        # Add the calculated data to the list
        cable_count.append((cable, n_cables))

    # Calculate the total costs for each cable combination
    equip_costs_array = [(cable[5] * length * n_cables) for cable, n_cables in cable_count]
    inst_costs_array = [(cable[6] * length * n_cables) for cable, n_cables in cable_count]
    
    # Calculate total costs
    total_costs_array = np.add(equip_costs_array, inst_costs_array)
    
    # Find the cable combination with the minimum total cost
    min_cost_index = np.argmin(total_costs_array)

    # Initialize costs
    equip_costs = equip_costs_array[min_cost_index]
    inst_costs = inst_costs_array[min_cost_index]
    ope_costs_yearly = 0.2 * 1e-2 * equip_costs
    deco_costs = 0.5 * inst_costs
    
    # Calculate present value
    total_costs = present_value(equip_costs, inst_costs, ope_costs_yearly, deco_costs)

    return total_costs, power_eff

def offshore_substation_costs(water_depth, ice_cover, port_distance, oss_capacity, polarity = "AC"):
    """
    Estimate the costs associated with an offshore substation based on various parameters.

    Parameters:
    - water_depth (float): Water depth at the location of the offshore substation.
    - ice_cover (int): Indicator of ice cover presence (1 for presence, 0 for absence).
    - port_distance (float): Distance from the offshore location to the nearest port.
    - oss_capacity (float): Capacity of the offshore substation.
    - polarity (str, optional): Polarity of the substation ('AC' or 'DC'). Defaults to 'AC'.

    Returns:
    - float: Estimated total costs of the offshore substation.
    """
    
    def support_structure(water_depth):
        """
        Determines the support structure type based on water depth.

        Returns:
        - str: Support structure type ('monopile', 'jacket', 'floating', or 'default').
        """
        # Define depth ranges for different support structures
        if water_depth < 30:
            return "sandisland"
        elif 30 <= water_depth < 150:
            return "jacket"
        elif 150 <= water_depth:
            return "floating"

    def equip_costs(water_depth, support_structure, ice_cover, oss_capacity, polarity):
        """
        Calculates the offshore substation equipment costs based on water depth, capacity, and export cable type.

        Returns:
        - float: Calculated equipment costs.
        """
        # Coefficients for equipment cost calculation based on the support structure and year
        support_structure_coeff = {
            'sandisland': (3.26, 804, 0, 0),
            'jacket': (233, 47, 309, 62),
            'floating': (87, 68, 116, 91)
        }

        equip_coeff = {
            'AC': (22.87, 7.06),
            'DC': (102.93, 31.75)
        }
        
        # Define parameters
        c1, c2, c3, c4 = support_structure_coeff[support_structure]
        
        c5, c6 = equip_coeff[polarity]
        
        # Define equivalent electrical power
        equiv_capacity = 0.5 * oss_capacity if polarity == "AC" else oss_capacity

        if support_structure == 'sandisland':
            # Calculate foundation costs for sand island
            area_island = (equiv_capacity * 5)
            slope = 0.75
            r_hub = np.sqrt(area_island/np.pi)
            r_seabed = r_hub + (water_depth + 3) / slope
            volume_island = (1/3) * slope * np.pi * (r_seabed ** 3 - r_hub ** 3)
            
            supp_costs = c1 * volume_island + c2 * area_island
        else:
            # Calculate foundation costs for jacket/floating
            supp_costs = (c1 * water_depth + c2 * 1000) * equiv_capacity + (c3 * water_depth + c4 * 1000)
        
        # Add support structure costs for ice cover adaptation
        supp_costs = 1.10 * supp_costs if ice_cover == 1 else supp_costs
        
        # Power converter costs
        conv_costs = c5 * oss_capacity * int(1e3) + c6 * int(1e6) #* int(1e3)
        
        # Calculate equipment costs
        equip_costs = supp_costs + conv_costs
        
        return supp_costs, conv_costs, equip_costs

    def inst_deco_costs(water_depth, support_structure, port_distance, oss_capacity, polarity, operation):
        """
        Calculate installation or decommissioning costs of offshore substations based on the water depth, and port distance.

        Returns:
        - float: Calculated installation or decommissioning costs.
        """
        # Installation coefficients for different vehicles
        inst_coeff = {
            ('sandisland','SUBV'): (20000, 25, 2000, 6000, 15),
            ('jacket' 'PSIV'): (1, 18.5, 24, 96, 200),
            ('floating','HLCV'): (1, 22.5, 10, 0, 40),
            ('floating','AHV'): (3, 18.5, 30, 90, 40)
        }

        # Decommissioning coefficients for different vehicles
        deco_coeff = {
            ('sandisland','SUBV'): (20000, 25, 2000, 6000, 15),
            ('jacket' 'PSIV'): (1, 18.5, 24, 96, 200),
            ('floating','HLCV'): (1, 22.5, 10, 0, 40),
            ('floating','AHV'): (3, 18.5, 30, 30, 40)
        }

        # Choose the appropriate coefficients based on the operation type
        coeff = inst_coeff if operation == 'inst' else deco_coeff

        if support_structure == 'sandisland':
            c1, c2, c3, c4, c5 = coeff[('sandisland','SUBV')]
            # Define equivalent electrical power
            equiv_capacity = 0.5 * oss_capacity if polarity == "AC" else oss_capacity
            
            # Calculate installation costs for sand island
            water_depth = max(0, water_depth)
            area_island = (equiv_capacity * 5)
            slope = 0.75
            r_hub = np.sqrt(area_island/np.pi)
            r_seabed = r_hub + (water_depth + 3) / slope
            volume_island = (1/3) * slope * np.pi * (r_seabed ** 3 - r_hub ** 3)
            
            total_costs = ((volume_island / c1) * ((2 * port_distance) / c2) + (volume_island / c3) + (volume_island / c4)) * (c5 * 1000) / 24
            
        elif support_structure == 'jacket':
            c1, c2, c3, c4, c5 = coeff[('jacket' 'PSIV')]
            # Calculate installation costs for jacket
            total_costs = ((1 / c1) * ((2 * port_distance) / c2 + c3) + c4) * (c5 * 1000) / 24
        elif support_structure == 'floating':
            total_costs = 0
            
            # Iterate over the coefficients for floating (HLCV and AHV)
            for vessel_type in [('floating', 'HLCV'), ('floating', 'AHV')]:
                c1, c2, c3, c4, c5 = coeff[vessel_type]
                
                # Calculate installation costs for the current vessel type
                vessel_costs = ((1 / c1) * ((2 * port_distance) / c2 + c3) + c4) * (c5 * 1000) / 24
                
                # Add the costs for the current vessel type to the total costs
                total_costs += vessel_costs
        else:
            total_costs = None
            
        return inst_deco_costs

    def oper_costs(support_structure, supp_costs, conv_costs):
        
        ope_exp = 0.03 * conv_costs + 0.015 * supp_costs if support_structure == "sandisland" else 0.03 * conv_costs
        
        return ope_exp

    # Determine support structure
    supp_structure = support_structure(water_depth)
    
    # Calculate equipment costs
    supp_costs, conv_costs, equip_costs =  equip_costs(water_depth, supp_structure, ice_cover, oss_capacity, polarity)

    # Calculate installation and decommissioning costs
    inst_costs = inst_deco_costs(water_depth, supp_structure, port_distance, oss_capacity, polarity, "inst")
    deco_costs = inst_deco_costs(water_depth, supp_structure, port_distance, oss_capacity, polarity, "deco")

    # Calculate yearly operational costs
    ope_costs_yearly = oper_costs(support_structure, supp_costs, conv_costs)
    
    # Calculate present value of costs    
    oss_costs = present_value(equip_costs, inst_costs, ope_costs_yearly, deco_costs)
    
    return oss_costs






# Define entities with costs, coordinates, and capacities
wind_farms = {
    'WF1': {'cost': 1000, 'coordinates': (10, 20), 'capacity': 150},
    'WF2': {'cost': 1500, 'coordinates': (15, 25), 'capacity': 200},
    'WF3': {'cost': 1100, 'coordinates': (10, 30), 'capacity': 100},
}

offshore_ss = {
    'OSS1': {'cost': 500, 'coordinates': (12, 22)},
    'OSS2': {'cost': 700, 'coordinates': (14, 26)},
}

onshore_ss = {
    'SS1': {'coordinates': (20, 40)},
    'SS2': {'coordinates': (25, 45)},
}

# Functions
def generate_connections_and_costs(wind_farms, offshore_ss, onshore_ss, cost_per_km_per_MW=0.5):
    """
    Generates all possible connections between wind farms, offshore substations, and onshore substations,
    along with their associated costs based on distance and capacity.
    """
    # Helper function to calculate Euclidean distance
    def calculate_distance(coord1, coord2):
        return math.sqrt((coord1[0] - coord2[0])**2 + (coord1[1] - coord2[1])**2)

    # Helper function to calculate connection cost
    def calculate_connection_cost(distance, capacity):
        return distance * capacity * cost_per_km_per_MW

    connections_costs = {}
    distances = {}
    total_capacity_per_oss = {oss: 0 for oss in offshore_ss}  # Track total capacity connected to each OSS

    # Calculate Wind Farm to Offshore Substation Connections
    for wf, wf_info in wind_farms.items():
        for oss, oss_info in offshore_ss.items():
            distance = calculate_distance(wf_info['coordinates'], oss_info['coordinates'])
            cost = calculate_connection_cost(distance, wf_info['capacity'])
            distances[(wf, oss)] = distance
            connections_costs[(wf, oss)] = cost
            total_capacity_per_oss[oss] += wf_info['capacity']  # Sum capacities for later calculation

    # Calculate Offshore Substation to Onshore Substation Connections
    for oss, oss_info in offshore_ss.items():
        for ss, ss_info in onshore_ss.items():
            distance = calculate_distance(oss_info['coordinates'], ss_info['coordinates'])
            capacity = total_capacity_per_oss[oss]  # Use total connected capacity for this connection
            cost = calculate_connection_cost(distance, capacity)
            distances[(oss,ss)] = distance
            connections_costs[(oss, ss)] = cost

    return distances, connections_costs

def create_decision_variables(model, wind_farms, offshore_ss, connections_costs):
    """
    Creates decision variables for the model.
    """
    model.select_wf = Var(wind_farms.keys(), within=Binary, initialize=0)  # Selection of Wind Farms
    model.select_oss = Var(offshore_ss.keys(), within=Binary, initialize=0)  # Selection of Offshore Substations
    model.select_conn = Var(connections_costs.keys(), within=Binary, initialize=0)  # Selection of Connections
    
def create_objective_function(model, wind_farms, offshore_ss, connections_costs):
    """
    Creates the objective function for the model.
    """
    model.total_cost = Objective(
        expr=sum(wind_farms[wf]['cost'] * model.select_wf[wf] for wf in wind_farms) +
        sum(offshore_ss[oss]['cost'] * model.select_oss[oss] for oss in offshore_ss) +
        sum(connections_costs[conn] * model.select_conn[conn] for conn in connections_costs),
        sense=minimize
    )
    
def add_constraints(model, wind_farms, offshore_ss, onshore_ss, connections_costs, distances, min_total_capacity, max_wf_oss_dist, max_oss_ss_dist, universal_offshore_ss_max_capacity):
    """
    Adds constraints to the model, including constraints for maximum distances.
    """
    
    # Constraint 1: If a wind farm is selected, it must connect to at least one offshore substation
    def wf_must_connect_to_oss_rule(model, wf):
        return sum(model.select_conn[(wf, oss)] for oss in offshore_ss if (wf, oss) in connections_costs) >= 1 * model.select_wf[wf]
    model.wf_must_connect_to_oss_constraint = Constraint(wind_farms.keys(), rule=wf_must_connect_to_oss_rule)

    # Constraint 2: If an offshore substation is selected, it must connect to at least one onshore substation
    def oss_connection_rule(model, oss):
        return sum(model.select_conn[(oss, ss)] for ss in onshore_ss if (oss, ss) in connections_costs) >= model.select_oss[oss]
    model.oss_connection_constraint = Constraint(offshore_ss.keys(), rule=oss_connection_rule)

    # Constraint 3: Connectivity between a wind farm and an offshore substation implies selection of both
    def wf_oss_selection_rule(model, wf, oss):
        if (wf, oss) in connections_costs:
            return model.select_conn[(wf, oss)] <= model.select_wf[wf]
        else:
            return Constraint.Skip
    model.wf_oss_selection_constraint = Constraint(wind_farms.keys(), offshore_ss.keys(), rule=wf_oss_selection_rule)

    # Constraint 4: Connectivity between an offshore substation and an onshore substation implies selection of the offshore substation
    def oss_ss_selection_rule(model, oss, ss):
        if (oss, ss) in connections_costs:
            return model.select_conn[(oss, ss)] <= model.select_oss[oss]
        else:
            return Constraint.Skip
    model.oss_ss_selection_constraint = Constraint(offshore_ss.keys(), onshore_ss.keys(), rule=oss_ss_selection_rule)

    # Constraint 5: Minimum total wind farm capacity
    def min_capacity_rule(model):
        return sum(wind_farms[wf]['capacity'] * model.select_wf[wf] for wf in wind_farms) >= min_total_capacity
    model.min_capacity_constraint = Constraint(rule=min_capacity_rule)

    # Constraint 6: Maximum distance from wind farms to offshore substations
    def max_wf_oss_distance_rule(model, wf, oss):
        if (wf, oss) in connections_costs:
            return distances[(wf, oss)] <= max_wf_oss_dist * model.select_conn[(wf, oss)]
        else:
            return Constraint.Skip
    model.max_wf_oss_distance_constraint = Constraint(wind_farms.keys(), offshore_ss.keys(), rule=max_wf_oss_distance_rule)

    # Constraint 7: Maximum distance from offshore substations to onshore substations
    def max_oss_ss_distance_rule(model, oss, ss):
        if (oss, ss) in connections_costs:
            return distances[(oss, ss)] <= max_oss_ss_dist * model.select_conn[(oss, ss)]
        else:
            return Constraint.Skip
    model.max_oss_ss_distance_constraint = Constraint(offshore_ss.keys(), onshore_ss.keys(), rule=max_oss_ss_distance_rule)

    # Constraint 8: If an offshore substation is connected to an onshore substation, it must be connected to at least one wind farm
    def oss_must_connect_to_wf_rule(model, oss):
        connected_to_ss = sum(model.select_conn[(oss, ss)] for ss in onshore_ss if (oss, ss) in connections_costs)
        connected_to_wf = sum(model.select_conn[(wf, oss)] for wf in wind_farms if (wf, oss) in connections_costs)
        return connected_to_wf >= connected_to_ss
    model.oss_must_connect_to_wf_constraint = Constraint(offshore_ss.keys(), rule=oss_must_connect_to_wf_rule)

    # Constraint 9: for Universal Maximum Capacity of an Offshore Substation
    def oss_max_capacity_rule(model, oss):
        return sum(wind_farms[wf]['capacity'] * model.select_conn[(wf, oss)] for wf in wind_farms if (wf, oss) in connections_costs) <= universal_offshore_ss_max_capacity
    model.oss_max_capacity_constraint = Constraint(offshore_ss.keys(), rule=oss_max_capacity_rule)


universal_offshore_ss_max_capacity = 400  # Maximum capacity in MW for any offshore substation

# Define cost per kilometer per MW for connection cost calculation
cost_per_km_per_MW = 0.5  # Example value, adjust based on actual cost factors

# Generate connections and their costs using the function
distances, connections_costs = generate_connections_and_costs(wind_farms, offshore_ss, onshore_ss, cost_per_km_per_MW)

min_total_capacity = 300  # Example: minimum total capacity in MW
max_wf_oss_dist = 10  # Example: maximum distance from wind farms to offshore substations in km
max_oss_ss_dist = 20  # Example: maximum distance from offshore substations to onshore substations in km

# Initialize the model
model = ConcreteModel()

# Create decision variables
create_decision_variables(model, wind_farms, offshore_ss, connections_costs)

# Create the objective function
create_objective_function(model, wind_farms, offshore_ss, connections_costs)

# Add constraints, including the new universal maximum capacity constraint
add_constraints(model, wind_farms, offshore_ss, onshore_ss, connections_costs, distances, min_total_capacity, max_wf_oss_dist, max_oss_ss_dist, universal_offshore_ss_max_capacity)

# Solve the model
solver = SolverFactory('glpk')
solver.solve(model)

# Output the solution
print("Selected Wind Farms:")
for wf in wind_farms:
    if model.select_wf[wf].value == 1:
        print(f"  {wf}")

print("\nSelected Offshore Substations:")
for oss in offshore_ss:
    if model.select_oss[oss].value == 1:
        print(f"  {oss}")

print("\nSelected Connections:")
for conn in connections_costs:
    if model.select_conn[conn].value == 1:
        print(f"  {conn} with cost {connections_costs[conn]:.2f}")
