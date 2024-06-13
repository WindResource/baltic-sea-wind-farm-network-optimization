"""
Wind Farm Optimization Model Setup

This script sets up and solves an optimization problem for selecting wind farms, energy hubs,
and their connections to minimize total cost while adhering to operational constraints. It considers
the cost of selecting wind farms and substations, plus the cost associated with connecting these
entities based on distances. It ensures configurations meet specified requirements, including
connection feasibility, capacity limitations, and distance constraints.

- generate_connections_and_cost(wind_farms, offshore_ss, onshore_ss, cost_per_distance_unit): Generates
    possible connections between entities and calculates associated cost based on distances.
    Parameters:
    - wind_farms (dict): Dictionary of wind farms with 'coordinates'.
    - offshore_ss (dict): Dictionary of energy hubs with 'coordinates'.
    - onshore_ss (dict): Dictionary of onshore substations with 'coordinates'.
    - cost_per_distance_unit (float): Cost factor per unit of distance (e.g., per kilometer).
    Returns:
    - tuple of (dict, dict): Two dictionaries, one for connection cost and one for distances, 
    with tuple ids representing connections (e.g., ('WF1', 'OSS1')).

- add_constraints(model, wind_farms, offshore_ss, onshore_ss, connections_cost, distances,
        min_total_capacity, max_wf_eh_dist, max_eh_ss_dist, universal_offshore_ss_max_capacity):
    Adds operational constraints to the optimization model, including capacity and distance limitations.
    Parameters:
    - model (ConcreteModel): The Pyomo model.
    - wind_farms (dict): Dictionary of wind farms.
    - offshore_ss (dict): Dictionary of energy hubs.
    - onshore_ss (dict): Dictionary of onshore substations.
    - connections_cost (dict): Dictionary of connection cost.
    - distances (dict): Dictionary of distances between entities.
    - min_total_capacity (float): Minimum total capacity requirement for selected wind farms.
    - max_wf_eh_dist (float): Maximum allowed distance from wind farms to energy hubs.
    - max_eh_ss_dist (float): Maximum allowed distance from energy hubs to onshore substations.
    - universal_offshore_ss_max_capacity (float): Maximum capacity for any energy hub.
    
The optimization model is solved using Pyomo with GLPK as the solver. The solution includes selected
wind farms, energy hubs, and connections between them, adhering to defined constraints.
"""

from pyomo.environ import *
import numpy as np
import os
from itertools import product
from scripts.present_value import PV

pv = PV()

def eh_cost_lin(water_depth, ice_cover, port_distance, eh_capacity):
    """
    Estimate the cost associated with an energy hub based on various parameters.

    Parameters:
    - water_depth (float): Water depth at the location of the energy hub.
    - ice_cover (int): Indicator of ice cover presence (1 for presence, 0 for absence).
    - port_distance (float): Distance from the offshore location to the nearest port.
    - eh_capacity (float): Capacity of the energy hub.
    - polarity (str, optional): Polarity of the substation ('AC' or 'DC'). Defaults to 'AC'.

    Returns:
    - float: Estimated total cost of the energy hub.
    """
    
    def supp_struct_cond(water_depth):
        """
        Determines the support structure type based on water depth.

        Returns:
        - str: Support structure type ('monopile', 'jacket', 'floating', or 'default').
        """
        # Define depth ranges for different support structures
        if water_depth < 150:
            return "jacket"
        elif 150 <= water_depth:
            return "floating"

    def equip_cost_lin(water_depth, support_structure, ice_cover, eh_capacity):
        """
        Calculates the energy hub equipment cost based on water depth, capacity, and export cable type.

        Returns:
        - float: Calculated equipment cost.
        """
        # Coefficients for equipment cost calculation based on the support structure and year
        support_structure_coeff = {
            'jacket': (233, 47, 309, 62),
            'floating': (87, 68, 116, 91)
        }

        equip_coeff = (22.87, 7.06)
        
        # Define parameters
        c1, c2, c3, c4 = support_structure_coeff[support_structure]
        
        c5, c6 = equip_coeff
        
        # Define equivalent electrical power
        equiv_capacity = 0.5 * eh_capacity

        # Calculate foundation cost for jacket/floating
        supp_cost = (c1 * water_depth + c2 * 1000) * equiv_capacity + (c3 * water_depth + c4 * 1000)
        
        # Add support structure cost for ice cover adaptation
        supp_cost = 1.10 * supp_cost if ice_cover == 1 else supp_cost
        
        # Power converter cost
        conv_cost = c5 * eh_capacity * int(1e3) + c6 * int(1e6) #* int(1e3)
        
        # Calculate equipment cost
        equip_cost = supp_cost + conv_cost
        
        return conv_cost, equip_cost

    def inst_deco_cost_lin(support_structure, port_distance, operation):
        """
        Calculate installation or decommissioning cost of offshore substations based on the water depth, and port distance.

        Returns:
        - float: Calculated installation or decommissioning cost.
        """
        # Installation coefficients for different vehicles
        inst_coeff = {
            ('jacket' 'PSIV'): (1, 18.5, 24, 96, 200),
            ('floating','HLCV'): (1, 22.5, 10, 0, 40),
            ('floating','AHV'): (3, 18.5, 30, 90, 40)
        }

        # Decommissioning coefficients for different vehicles
        deco_coeff = {
            ('jacket' 'PSIV'): (1, 18.5, 24, 96, 200),
            ('floating','HLCV'): (1, 22.5, 10, 0, 40),
            ('floating','AHV'): (3, 18.5, 30, 30, 40)
        }

        # Choose the appropriate coefficients based on the operation type
        coeff = inst_coeff if operation == 'inst' else deco_coeff
            
        if support_structure == 'jacket':
            c1, c2, c3, c4, c5 = coeff[('jacket' 'PSIV')]
            # Calculate installation cost for jacket
            total_cost = ((1 / c1) * ((2 * port_distance) / c2 + c3) + c4) * (c5 * 1000) / 24
        elif support_structure == 'floating':
            total_cost = 0
            
            # Iterate over the coefficients for floating (HLCV and AHV)
            for vessel_type in [('floating', 'HLCV'), ('floating', 'AHV')]:
                c1, c2, c3, c4, c5 = coeff[vessel_type]
                # Calculate installation cost for the current vessel type
                vessel_cost = ((1 / c1) * ((2 * port_distance) / c2 + c3) + c4) * (c5 * 1000) / 24
                # Add the cost for the current vessel type to the total cost
                total_cost += vessel_cost
        
        return total_cost

    # Determine support structure
    supp_structure = supp_struct_cond(water_depth)
    
    # Calculate equipment cost
    conv_cost, equip_cost = equip_cost_lin(water_depth, supp_structure, ice_cover, eh_capacity)

    # Calculate installation and decommissioning cost
    inst_cost = inst_deco_cost_lin(supp_structure, port_distance, "inst")
    deco_cost = inst_deco_cost_lin(supp_structure, port_distance, "deco")

    # Calculate yearly operational cost
    ope_cost_yearly = 0.03 * conv_cost
    
    # Calculate present value of cost    
    eh_cost = pv.present_value_single(equip_cost, inst_cost, ope_cost_yearly, deco_cost)
    
    # Offshore substation cost in million Euros
    eh_cost *= 1e-6
    
    return eh_cost

def onss_cost_lin(capacity, threshold):
    """
    Calculate the cost for ONSS expansion above a certain capacity.

    Parameters:
    - capacity (float): The total capacity for which the cost is to be calculated.
    - threshold (float): The capacity threshold specific to the ONSS above which cost are incurred.
    
    Returns:
    - (float) Cost of expanding the ONSS if the capacity exceeds the threshold.
    """
    
    overcap_cost = 0.050 # Million EU/ MW
    
    # Calculate the cost function: difference between capacity and threshold multiplied by the cost factor
    cost_function = (capacity - threshold) * overcap_cost
    
    return cost_function

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

    cable_length = 1.10 * distance
    cable_capacity = 348 # MW
    cable_equip_cost = 0.860 #Meu/km
    cable_inst_cost = 0.540 #Meu/km
    capacity_factor = 0.95
    
    parallel_cables = capacity / (cable_capacity * capacity_factor)
    
    equip_cost = parallel_cables * cable_length * cable_equip_cost
    inst_cost = parallel_cables * cable_length * cable_inst_cost
    
    ope_cost_yearly = 0.2 * 1e-2 * equip_cost
    
    deco_cost = 0.5 * inst_cost

    # Calculate present value
    total_cost = pv.present_value_single(equip_cost, inst_cost, ope_cost_yearly, deco_cost)

    return total_cost

def ec2_cost_lin(distance, capacity):
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

    cable_length = 1.10 * distance + 2 # km Accounting for the offshore to onshore transition
    cable_capacity = 348 # MW
    cable_equip_cost = 0.860 # Million EU/km
    cable_inst_cost = 0.540 # Million EU/km
    capacity_factor = 0.95
    
    parallel_cables = capacity / (cable_capacity * capacity_factor)
    
    equip_cost = parallel_cables * cable_length * cable_equip_cost
    inst_cost = parallel_cables * cable_length * cable_inst_cost
    
    ope_cost_yearly = 0.2 * 1e-2 * equip_cost
    
    deco_cost = 0.5 * inst_cost

    # Calculate present value
    total_cost = pv.present_value_single(equip_cost, inst_cost, ope_cost_yearly, deco_cost)

    return total_cost

def ec3_cost_lin(distance, capacity):
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

    cable_length = 1.10 * distance + 2 # km Accounting for the offshore to onshore transition
    cable_capacity = 348 # MW
    cable_equip_cost = 0.860 # Million EU/km
    cable_inst_cost = 0.540 # Million EU/km
    capacity_factor = 0.95
    
    parallel_cables = capacity / (cable_capacity * capacity_factor)
    
    equip_cost = parallel_cables * cable_length * cable_equip_cost
    inst_cost = parallel_cables * cable_length * cable_inst_cost
    
    ope_cost_yearly = 0.2 * 1e-2 * equip_cost
    
    deco_cost = 0.5 * inst_cost

    # Calculate present value
    total_cost = pv.present_value_single(equip_cost, inst_cost, ope_cost_yearly, deco_cost)

    return total_cost

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great-circle distance between two points
    on the Earth (specified in decimal degrees) using NumPy for calculations.
    """
    # Convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat/2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2.0)**2
    c = 2 * np.arcsin(np.sqrt(a))
    r = 6371  # Radius of Earth in kilometers
    return c * r

def find_viable_ec1(wf_lon, wf_lat, eh_lon, eh_lat, wf_iso, eh_iso):
    """
    Find all pairs of offshore wind farms and energy hubs within 150km,
    ensuring that they belong to the same country based on their ISO codes.
    
    Parameters are dictionaries indexed by IDs with longitude, latitude, and ISO codes.
    """
    connections = []
    for wf_id, eh_id in product(wf_lon.keys(), eh_lon.keys()):
        # Calculate the distance first to see if they are within the viable range
        distance = haversine(wf_lon[wf_id], wf_lat[wf_id], eh_lon[eh_id], eh_lat[eh_id])
        if distance <= 150:  # Check if the distance is within 150 km
            # Then check if the ISO codes match for the current wind farm and energy hub pair
            if wf_iso[wf_id] == eh_iso[eh_id]:
                connections.append((int(wf_id), int(eh_id)))
    return connections

def find_viable_ec2(eh_lon, eh_lat, onss_lon, onss_lat, eh_iso, onss_iso):
    """
    Find all pairs of offshore and onshore substations within 300km,
    ensuring that they belong to the same country based on their ISO codes.
    
    Parameters are dictionaries indexed by substation IDs with longitude, latitude, and ISO codes.
    """
    connections = []
    for eh_id, onss_id in product(eh_lon.keys(), onss_lon.keys()):
        # Calculate the distance first to see if they are within the viable range
        distance = haversine(eh_lon[eh_id], eh_lat[eh_id], onss_lon[onss_id], onss_lat[onss_id])
        if distance <= 300:  # Check if the distance is within 300 km
            # Then check if the ISO codes match for the current offshore and onshore substation pair
            if eh_iso[eh_id] == onss_iso[onss_id]:
                connections.append((int(eh_id), int(onss_id)))
    return connections

def find_viable_ec3(wf_lon, wf_lat, onss_lon, onss_lat, wf_iso, onss_iso):
    """
    Find all pairs of wind farms and onshore substations within 450km,
    ensuring that they belong to the same country based on their ISO codes.
    
    Parameters are dictionaries indexed by IDs with longitude, latitude, and ISO codes.
    """
    connections = []
    for wf_id, onss_id in product(wf_lon.keys(), onss_lon.keys()):
        distance = haversine(wf_lon[wf_id], wf_lat[wf_id], onss_lon[onss_id], onss_lat[onss_id])
        if distance <= 450:  # Check if the distance is within 450 km
            if wf_iso[wf_id] == onss_iso[onss_id]:
                connections.append((int(wf_id), int(onss_id)))
    return connections

def get_viable_entities(viable_ec1, viable_ec2, viable_ec3):
    """
    Identifies unique wind farm, energy hub, and onshore substation IDs
    based on their involvement in viable export and export cable connections.

    Parameters:
    - viable_ec1 (list of tuples): List of tuples, each representing a viable connection
        between a wind farm and an energy hub (wf_id, eh_id).
    - viable_ec2 (list of tuples): List of tuples, each representing a viable connection
        between an energy hub and an onshore substation (eh_id, onss_id).
    - viable_ec3 (list of tuples): List of tuples, each representing a viable direct connection
        between a wind farm and an onshore substation (wf_id, onss_id).

    Returns:
    - viable_wf (set): Set of wind farm IDs with at least one viable connection to an energy hub or onshore substation.
    - viable_eh (set): Set of energy hub IDs involved in at least one viable connection
        either to a wind farm or an onshore substation.
    - viable_onss (set): Set of onshore substation IDs with at least one viable connection to an energy hub or wind farm.
    """
    viable_wf = set()
    viable_eh = set()
    viable_onss = set()

    # Extract unique wind farm and energy hub IDs from export connections
    for wf_id, eh_id in viable_ec1:
        viable_wf.add(int(wf_id))
        viable_eh.add(int(eh_id))

    # Extract unique offshore and onshore substation IDs from export cable connections
    for eh_id, onss_id in viable_ec2:
        viable_eh.add(int(eh_id))
        viable_onss.add(int(onss_id))

    # Extract unique wind farm and onshore substation IDs from direct connections
    for wf_id, onss_id in viable_ec3:
        viable_wf.add(int(wf_id))
        viable_onss.add(int(onss_id))

    return viable_wf, viable_eh, viable_onss

def opt_model(workspace_folder):
    """
    Create an optimization model for offshore wind farm layout optimization.

    Parameters:
    - workspace_folder (str): The path to the workspace folder containing datasets.

    Returns:
    - model: Pyomo ConcreteModel object representing the optimization model.
    """
    
    """
    Initialise model
    """
    print("Initialising model...")
    
    # Create a Pyomo model
    model = ConcreteModel()

    """
    Process data
    """
    print("Processing data...")
    
    # Mapping ISO country codes of Baltic Sea countries to unique integers
    iso_to_int_mp = {
        'DE': 1,  # Germany
        'DK': 2,  # Denmark
        'EE': 3,  # Estonia
        'FI': 4,  # Finland
        'LV': 5,  # Latvia
        'LT': 6,  # Lithuania
        'PL': 7,  # Poland
        'SE': 8   # Sweden
    }

    # Load datasets
    wf_dataset_file = os.path.join(workspace_folder, 'wf_data.npy')
    eh_dataset_file = os.path.join(workspace_folder, 'eh_data.npy')
    onss_dataset_file = os.path.join(workspace_folder, 'onss_data.npy')
    
    wf_dataset = np.load(wf_dataset_file, allow_pickle=True)
    eh_dataset = np.load(eh_dataset_file, allow_pickle=True)
    onss_dataset = np.load(onss_dataset_file, allow_pickle=True)

    # Component identifiers
    wf_ids = [int(data[0]) for data in wf_dataset]
    eh_ids = [int(data[0]) for data in eh_dataset]
    onss_ids = [int(data[0]) for data in onss_dataset]

    # Wind farm data
    wf_iso, wf_lon, wf_lat, wf_cap, wf_cost = {}, {}, {}, {}, {}

    for data in wf_dataset:
        id = int(data[0])
        wf_iso[id] = iso_to_int_mp[data[1]]
        wf_lon[id] = float(data[2])
        wf_lat[id] = float(data[3])
        wf_cap[id] = float(data[4])
        wf_cost[id] = float(data[5])

    # Offshore substation data
    eh_iso, eh_lon, eh_lat, eh_wdepth, eh_icover, eh_pdist = {}, {}, {}, {}, {}, {}

    for data in eh_dataset:
        id = int(data[0])
        eh_iso[id] = iso_to_int_mp[data[1]]
        eh_lon[id] = float(data[2])
        eh_lat[id] = float(data[3])
        eh_wdepth[id] = int(data[4])
        eh_icover[id] = int(data[5])
        eh_pdist[id] = float(data[6])
    
    # Onshore substation data
    onss_iso, onss_lon, onss_lat, onss_thold = {}, {}, {}, {}

    for data in onss_dataset:
        id = int(data[0])
        onss_iso[id] = iso_to_int_mp[data[1]]
        onss_lon[id] = float(data[2])
        onss_lat[id] = float(data[3])
        onss_thold[id] = float(data[4])

    """
    Define model parameters
    """
    print("Defining model parameters...")
    
    # Identifiers model components
    model.wf_ids = Set(initialize=wf_ids)
    model.eh_ids = Set(initialize=eh_ids)
    model.onss_ids = Set(initialize=onss_ids)
    
    # Wind farm model parameters
    model.wf_iso = Param(model.wf_ids, initialize=wf_iso, within=NonNegativeIntegers)
    model.wf_lon = Param(model.wf_ids, initialize=wf_lon, within=NonNegativeReals)
    model.wf_lat = Param(model.wf_ids, initialize=wf_lat, within=NonNegativeReals)
    model.wf_cap = Param(model.wf_ids, initialize=wf_cap, within=NonNegativeIntegers)
    model.wf_cost = Param(model.wf_ids, initialize=wf_cost, within=NonNegativeReals)

    # Offshore substation model parameters
    model.eh_iso = Param(model.eh_ids, initialize=eh_iso, within=NonNegativeIntegers)
    model.eh_lon = Param(model.eh_ids, initialize=eh_lon, within=NonNegativeReals)
    model.eh_lat = Param(model.eh_ids, initialize=eh_lat, within=NonNegativeReals)
    model.eh_wdepth = Param(model.eh_ids, initialize=eh_wdepth, within=NonNegativeIntegers)
    model.eh_icover = Param(model.eh_ids, initialize=eh_icover, within=Binary)
    model.eh_pdist = Param(model.eh_ids, initialize=eh_pdist, within=NonNegativeIntegers)

    # Onshore substation model parameters
    model.onss_iso = Param(model.onss_ids, initialize=onss_iso, within=NonNegativeIntegers)
    model.onss_lon = Param(model.onss_ids, initialize=onss_lon, within=NonNegativeReals)
    model.onss_lat = Param(model.onss_ids, initialize=onss_lat, within=NonNegativeReals)
    model.onss_thold = Param(model.onss_ids, initialize=onss_thold, within=NonNegativeIntegers)

    """
    Define decision variables
    """
    print("Defining decision parameters...")
    
    # Calculate viable connections
    viable_ec1 = find_viable_ec1(wf_lon, wf_lat, eh_lon, eh_lat, wf_iso, eh_iso)
    viable_ec2 = find_viable_ec2(eh_lon, eh_lat, onss_lon, onss_lat, eh_iso, onss_iso)
    viable_ec3 = find_viable_ec3(wf_lon, wf_lat, onss_lon, onss_lat, wf_iso, onss_iso)

    model.viable_ec1_ids = Set(initialize=viable_ec1, dimen=2)
    model.viable_ec2_ids = Set(initialize=viable_ec2, dimen=2)
    model.viable_ec3_ids = Set(initialize=viable_ec3, dimen=2)
    
    # Calculate viable entities based on the viable connections
    model.viable_wf_ids, model.viable_eh_ids, model.viable_onss_ids = get_viable_entities(viable_ec1, viable_ec2, viable_ec3)
    
    # Initialize variables
    model.wf_bool_var = Var(model.viable_wf_ids, within=Binary)
    
    model.eh_cap_var = Var(model.viable_eh_ids, within=NonNegativeReals)
    model.onss_cap_var = Var(model.viable_onss_ids, within=NonNegativeReals)
    model.ec1_cap_var = Var(model.viable_ec1_ids, within=NonNegativeReals)
    model.ec2_cap_var = Var(model.viable_ec2_ids, within=NonNegativeReals)
    model.ec3_cap_var = Var(model.viable_ec3_ids, within=NonNegativeReals)
    
    model.onss_cost_var = Var(model.viable_onss_ids, within=NonNegativeReals)
    
    # Define a dictionary containing variable names and their respective lengths
    print_variables = {
        "select_wf": model.wf_bool_var,
        "select_eh": model.eh_cap_var,
        "select_onss": model.onss_cap_var,
        "select_ec1": model.ec1_cap_var,
        "select_ec2": model.ec2_cap_var,
        "select_ec3": model.ec3_cap_var
    }

    # Iterate over the dictionary and print variable ids and their lengths
    for name, var in print_variables.items():
        print(f"{name} ids:", list(var)[:20])  # Print variable ids
        print(f"Number of {name} indices:", len(var))  # Print number of indices

    """
    Define Expressions
    """
    print("Defining expressions...")

    """
    Define expressions for wind farms (WF)
    """
    def wf_cost_rule(model, wf):
        return model.wf_cost[wf] * model.wf_bool_var[wf]
    model.wf_cost_exp = Expression(model.viable_wf_ids, rule=wf_cost_rule)
    
    """
    Define distance and capacity expressions for Inter-Array Cables (IAC)
    """
    def ec1_distance_rule(model, wf, eh):
        return haversine(model.wf_lon[wf], model.wf_lat[wf], model.eh_lon[eh], model.eh_lat[eh])
    model.ec1_dist_exp = Expression(model.viable_ec1_ids, rule=ec1_distance_rule)

    def ec1_cost_rule(model, wf, eh):
        return ec1_cost_lin(model.ec1_dist_exp[wf, eh], model.ec1_cap_var[wf, eh])
    model.ec1_cost_exp = Expression(model.viable_ec1_ids, rule=ec1_cost_rule)

    """
    Define expressions for Offshore Substation (OSS) capacity
    """

    def eh_cost_rule(model, eh):
        return eh_cost_lin(model.eh_wdepth[eh], model.eh_icover[eh], model.eh_pdist[eh], model.eh_cap_var[eh])
    model.eh_cost_exp = Expression(model.viable_eh_ids, rule=eh_cost_rule)

    """
    Define distance and capacity expressions for Export Cables (EC)
    """
    def ec2_distance_rule(model, eh, onss):
        return haversine(model.eh_lon[eh], model.eh_lat[eh], model.onss_lon[onss], model.onss_lat[onss])
    model.ec2_dist_exp = Expression(model.viable_ec2_ids, rule=ec2_distance_rule)

    def ec2_cost_rule(model, eh, onss):
        return ec2_cost_lin(model.ec2_dist_exp[eh, onss], model.ec2_cap_var[eh, onss])
    model.ec2_cost_exp = Expression(model.viable_ec2_ids, rule=ec2_cost_rule)

    """
    Define distance and capacity expressions for direct connections (WF to ONSS)
    """
    def ec3_distance_rule(model, wf, onss):
        return haversine(model.wf_lon[wf], model.wf_lat[wf], model.onss_lon[onss], model.onss_lat[onss])
    model.ec3_dist_exp = Expression(model.viable_ec3_ids, rule=ec3_distance_rule)

    def ec3_cost_rule(model, wf, onss):
        return ec3_cost_lin(model.ec3_dist_exp[wf, onss], model.ec3_cap_var[wf, onss])
    model.ec3_cost_exp = Expression(model.viable_ec3_ids, rule=ec3_cost_rule)

    """
    Define expressions for Onshore Substation (ONSS) capacity
    """

    def onss_cost_rule(model, onss):
        return onss_cost_lin(model.onss_cap_var[onss], model.onss_thold[onss])
    model.onss_cost_exp = Expression(model.viable_onss_ids, rule=onss_cost_rule)

    """
    Define Objective function
    """
    print("Defining objective function...")

    def global_cost_rule(model):
        """
        Calculate the total cost of the energy system. This includes the cost of selecting
        and connecting wind farms, energy hubs, and onshore substations. The objective is to minimize this total cost.

        The total cost is computed by summing:
        - The cost of selected wind farms.
        - The operational cost of selected energy hubs.
        - The cost associated with export cables connecting wind farms to energy hubs.
        - The cost associated with export cables connecting energy hubs to onshore substations.
        - The cost associated with direct cables connecting wind farms to onshore substations.

        Parameters:
        - model: The Pyomo model object containing all necessary decision variables and parameters.

        Returns:
        - The computed total cost of the network configuration, which the optimization process seeks to minimize.
        """
        wf_total_cost = sum(model.wf_cost_exp[wf] for wf in model.viable_wf_ids)
        eh_total_cost = sum(model.eh_cost_exp[eh] for eh in model.viable_eh_ids)
        onss_total_cost = sum(model.onss_cost_var[onss] for onss in model.viable_onss_ids)
        ec1_total_cost = sum(model.ec1_cost_exp[wf, eh] for (wf, eh) in model.viable_ec1_ids)
        ec2_total_cost = sum(model.ec2_cost_exp[eh, onss] for (eh, onss) in model.viable_ec2_ids)
        ec3_total_cost = sum(model.ec3_cost_exp[wf, onss] for (wf, onss) in model.viable_ec3_ids)
        
        onss_total_cap_aux = sum(model.onss_cap_var[onss] for onss in model.viable_onss_ids) # Ensures that the onss capacity is zero when not connected
        
        return wf_total_cost + eh_total_cost + ec1_total_cost + ec2_total_cost + ec3_total_cost + onss_total_cost + onss_total_cap_aux

    # Set the objective in the model
    model.global_cost_obj = Objective(rule=global_cost_rule, sense=minimize)

    """
    Define Constraints
    """
    print("Defining total capacity constraint...")

    def tot_wf_cap_rule(model):
        """
        Ensure the selected wind farms collectively meet a minimum required capacity.
        This capacity is specified as a fraction of the total potential capacity of all considered wind farms.
        """
        min_req_cap = 1 * sum(model.wf_cap[wf] for wf in model.viable_wf_ids)
        return sum(model.wf_bool_var[wf] * model.wf_cap[wf] for wf in model.viable_wf_ids) >= min_req_cap
    model.tot_wf_cap_con = Constraint(rule=tot_wf_cap_rule)
    
    print("Defining capacity constraints...")
    
    def wf_connection_rule(model, wf):
        """
        Ensure each selected wind farm connects to at least one energy hub or at least one onshore substation.
        """
        connect_to_eh = sum(model.ec1_cap_var[wf, eh] for eh in model.viable_eh_ids if (wf, eh) in model.viable_ec1_ids)
        connect_to_onss = sum(model.ec3_cap_var[wf, onss] for onss in model.viable_onss_ids if (wf, onss) in model.viable_ec3_ids)
        return (connect_to_eh + connect_to_onss) >= model.wf_bool_var[wf]
    model.wf_connection_con = Constraint(model.viable_wf_ids, rule=wf_connection_rule)

    def ec1_cap_connect_rule(model, wf):
        """
        Ensure each selected wind farm is connected to either one energy hub or directly to one onshore substation.
        """
        connect_to_eh = sum(model.ec1_cap_var[wf, eh] for eh in model.viable_eh_ids if (wf, eh) in model.viable_ec1_ids)
        connect_to_onss = sum(model.ec3_cap_var[wf, onss] for onss in model.viable_onss_ids if (wf, onss) in model.viable_ec3_ids)
        return connect_to_eh + connect_to_onss >= model.wf_bool_var[wf] * model.wf_cap[wf]
    model.ec1_cap_connect_con = Constraint(model.viable_wf_ids, rule=ec1_cap_connect_rule)

    def eh_cap_connect_rule(model, eh):
        """
        Ensure the capacity of each energy hub matches or exceeds the total capacity of the connected wind farms.
        """
        connect_from_wf = sum(model.ec1_cap_var[wf, eh] for wf in model.viable_wf_ids if (wf, eh) in model.viable_ec1_ids)
        return model.eh_cap_var[eh] >= connect_from_wf
    model.eh_cap_connect_con = Constraint(model.viable_eh_ids, rule=eh_cap_connect_rule)

    def ec2_cap_connect_rule(model, eh):
        """
        Ensure the connection capacity from each energy hub to onshore substations matches the substation's capacity.
        """
        connect_to_onss = sum(model.ec2_cap_var[eh, onss] for onss in model.viable_onss_ids if (eh, onss) in model.viable_ec2_ids)
        return connect_to_onss >= model.eh_cap_var[eh]
    model.ec2_cap_connect_con = Constraint(model.viable_eh_ids, rule=ec2_cap_connect_rule)

    def onss_cap_connect_rule(model, onss):
        """
        Ensure the capacity of each onshore substation is at least the total incoming capacity from connected energy hubs or wind farms.
        """
        connect_from_eh = sum(model.ec2_cap_var[eh, onss] for eh in model.viable_eh_ids if (eh, onss) in model.viable_ec2_ids)
        connect_from_wf = sum(model.ec3_cap_var[wf, onss] for wf in model.viable_wf_ids if (wf, onss) in model.viable_ec3_ids)
        return model.onss_cap_var[onss] >= connect_from_eh + connect_from_wf
    model.onss_cap_connect_con = Constraint(model.viable_onss_ids, rule=onss_cap_connect_rule)
    
    print("Defining the cost variables...")
    
    def onss_cost_rule(model, onss):
        """
        Ensure the cost variable for each onshore substation meets or exceeds the calculated cost.
        """
        return model.onss_cost_var[onss] >= model.onss_cost_exp[onss]
    model.onss_cost_con = Constraint(model.viable_onss_ids, rule=onss_cost_rule)
    
    """
    Solve the model
    """
    print("Solving the model...")
    
    solver_options = {
        'numerics/scaling': 1,  # Enable scaling
        'tolerances/feasibility': 1e-5,  # Tolerance for feasibility checks
        'tolerances/optimality': 1e-5,   # Tolerance for optimality conditions
        'tolerances/integrality': 1e-5,  # Tolerance for integer variable constraints
        'presolving/maxrounds': -1,      # Max presolve iterations to simplify the model
        'propagating/maxrounds': -1,     # Max constraint propagation rounds
        'parallel/threads': -1,          # Use all CPU cores for parallel processing
        'nodeselection': 'hybrid',       # Hybrid node selection in branch and bound
        'branching/varsel': 'pscost',    # Pseudocost variable selection in branching
        'separating/aggressive': 1,      # Enable aggressive separation
        'conflict/enable': 1,            # Activate conflict analysis
        'heuristics/rens/freq': 10,      # Frequency of RENS heuristic
        'heuristics/diving/freq': 10,    # Frequency of diving heuristic
        'propagating/maxroundsroot': 15, # Propagation rounds at root node
        'limits/nodes': 1e5,             # Maximum nodes in search tree
        'limits/totalnodes': 1e5,        # Total node limit across threads
        'emphasis/optimality': 1,        # Emphasize optimality
        'emphasis/memory': 1,            # Emphasize memory
        'separating/maxrounds': 10,      # Limit cut rounds at non-root nodes
        'heuristics/feaspump/freq': 10,  # Frequency of feasibility pump heuristic
        'tol': 0.01,                     # Set the relative optimality gap tolerance to 1%
        'display/verblevel': 4           # Set verbosity level to display information about the solution
    }

    def save_results(model, workspace_folder):
        """
        Save the IDs of selected components of the optimization model along with all their corresponding parameters,
        including directly retrieved capacity and cost from the model expressions, into both .npy and .txt files as structured arrays.
        Headers are included in the .txt files for clarity.

        Parameters:
        - model: The optimized Pyomo model.
        - workspace_folder: The path to the directory where results will be saved.
        """
        def exp_f(e):
            return round(e.expr(), 3)
        
        def var_f(v):
            return round(v.value, 3)
        
        def par_f(p):
            return round(p, 3)
        
        # Mapping ISO country codes of Baltic Sea countries to unique integers
        int_to_iso_mp = {
            1 : 'DE',  # Germany
            2 : 'DK',  # Denmark
            3 : 'EE',  # Estonia
            4 : 'FI',  # Finland
            5 : 'LV',  # Latvia
            6 : 'LT',  # Lithuania
            7 : 'PL',  # Poland
            8 : 'SE'   # Sweden
        }
        
        selected_components = {
            'wf_ids': {
                'data': np.array([(wf, int_to_iso_mp[model.wf_iso[wf]], model.wf_lon[wf], model.wf_lat[wf], model.wf_cap[wf], model.wf_cost[wf]) 
                                for wf in model.viable_wf_ids if model.wf_bool_var[wf].value > 0], 
                                dtype=[('id', int), ('iso', 'U2'), ('lon', float), ('lat', float), ('capacity', int), ('cost', int)]),
                'headers': "ID, ISO, Longitude, Latitude, Capacity, Cost"
            },
            'eh_ids': {
                'data': np.array([(eh, int_to_iso_mp[model.eh_iso[eh]], model.eh_lon[eh], model.eh_lat[eh], model.eh_wdepth[eh], model.eh_icover[eh], model.eh_pdist[eh], var_f(model.eh_cap_var[eh]), exp_f(model.eh_cost_exp[eh])) 
                                for eh in model.viable_eh_ids if model.eh_cap_var[eh].value > 0], 
                                dtype=[('id', int), ('iso', 'U2'), ('lon', float), ('lat', float), ('water_depth', int), ('ice_cover', int), ('port_dist', int), ('capacity', float), ('cost', float)]),
                'headers': "ID, ISO, Longitude, Latitude, Water Depth, Ice Cover, Port Distance, Capacity, Cost"
            },
            'onss_ids': {
                'data': np.array([(onss, int_to_iso_mp[model.onss_iso[onss]], model.onss_lon[onss], model.onss_lat[onss], model.onss_thold[onss], var_f(model.onss_cap_var[onss]), var_f(model.onss_cost_var[onss])) 
                                for onss in model.viable_onss_ids if model.onss_cap_var[onss].value > 0], 
                                dtype=[('id', int), ('iso', 'U2'), ('lon', float), ('lat', float), ('threshold', int), ('capacity', float), ('cost', float)]),
                'headers': "ID, ISO, Longitude, Latitude, Threshold, Capacity, Cost"
            }
        }

        # Export cable ID counter
        ec_id_counter = 1

        # Create ec1_ids with export cable ID, single row for each cable
        ec1_data = []
        for wf, eh in model.viable_ec1_ids:
            if model.ec1_cap_var[wf, eh].value > 0:
                ec1_cap = var_f(model.ec1_cap_var[wf, eh])
                ec1_cost = exp_f(model.ec1_cost_exp[wf, eh])
                dist1 = par_f(haversine(model.wf_lon[wf], model.wf_lat[wf], model.eh_lon[eh], model.eh_lat[eh]))
                ec1_data.append((ec_id_counter, wf, eh, model.wf_lon[wf], model.wf_lat[wf], model.eh_lon[eh], model.eh_lat[eh], dist1, ec1_cap, ec1_cost))
                ec_id_counter += 1

        selected_components['ec1_ids'] = {
            'data': np.array(ec1_data, dtype=[('ec_id', int), ('comp_1_id', int), ('comp_2_id', int), ('lon_1', float), ('lat_1', float), ('lon_2', float), ('lat_2', float), ('distance', float), ('capacity', float), ('cost', float)]),
            'headers': "EC_ID, Comp_1_ID, Comp_2_ID, Lon_1, Lat_1, Lon_2, Lat_2, Distance, Capacity, Cost"
        }

        # Create ec2_ids with export cable ID, single row for each cable
        ec2_data = []
        ec_id_counter = 1
        for eh, onss in model.viable_ec2_ids:
            if model.ec2_cap_var[eh, onss].value > 0:
                ec2_cap = var_f(model.ec2_cap_var[eh, onss])
                ec2_cost = exp_f(model.ec2_cost_exp[eh, onss])
                dist2 = par_f(haversine(model.eh_lon[eh], model.eh_lat[eh], model.onss_lon[onss], model.onss_lat[onss]))
                ec2_data.append((ec_id_counter, eh, onss, model.eh_lon[eh], model.eh_lat[eh], model.onss_lon[onss], model.onss_lat[onss], dist2, ec2_cap, ec2_cost))
                ec_id_counter += 1

        selected_components['ec2_ids'] = {
            'data': np.array(ec2_data, dtype=[('ec_id', int), ('comp_1_id', int), ('comp_2_id', int), ('lon_1', float), ('lat_1', float), ('lon_2', float), ('lat_2', float), ('distance', float), ('capacity', float), ('cost', float)]),
            'headers': "EC_ID, Comp_1_ID, Comp_2_ID, Lon_1, Lat_1, Lon_2, Lat_2, Distance, Capacity, Cost"
        }

        # Create ec3_ids with export cable ID, single row for each cable
        ec3_data = []
        ec_id_counter = 1
        for wf, onss in model.viable_ec3_ids:
            if model.ec3_cap_var[wf, onss].value > 0:
                ec3_cap = var_f(model.ec3_cap_var[wf, onss])
                ec3_cost = exp_f(model.ec3_cost_exp[wf, onss])
                dist3 = par_f(haversine(model.wf_lon[wf], model.wf_lat[wf], model.onss_lon[onss], model.onss_lat[onss]))
                ec3_data.append((ec_id_counter, wf, onss, model.wf_lon[wf], model.wf_lat[wf], model.onss_lon[onss], model.onss_lat[onss], dist3, ec3_cap, ec3_cost))
                ec_id_counter += 1

        selected_components['ec3_ids'] = {
            'data': np.array(ec3_data, dtype=[('ec_id', int), ('comp_1_id', int), ('comp_2_id', int), ('lon_1', float), ('lat_1', float), ('lon_2', float), ('lat_2', float), ('distance', float), ('capacity', float), ('cost', float)]),
            'headers': "EC_ID, Comp_1_ID, Comp_2_ID, Lon_1, Lat_1, Lon_2, Lat_2, Distance, Capacity, Cost"
        }

        # Ensure the results directory exists
        results_dir = os.path.join(workspace_folder, "results", "combined")
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)

        total_capacity_cost = []

        for key, info in selected_components.items():
            npy_file_path = os.path.join(results_dir, f'{key}_c.npy')
            txt_file_path = os.path.join(results_dir, f'{key}_c.txt')

            # Save as .npy file
            np.save(npy_file_path, info['data'])

            # Save as .txt file for easier viewing
            with open(txt_file_path, 'w') as file:
                file.write(info['headers'] + '\n')  # Write the headers
                for entry in info['data']:
                    file.write(', '.join(map(str, entry)) + '\n')
            
            print(f'Saved {key} in {npy_file_path} and {txt_file_path}')

            # Calculate total capacity and cost for this component type
            total_capacity = sum(info['data']['capacity'])
            total_cost = sum(info['data']['cost'])
            total_capacity_cost.append((key, round(total_capacity), round(total_cost, 3)))

        # Calculate overall totals
        overall_capacity = sum(item[1] for item in total_capacity_cost)
        overall_cost = sum(item[2] for item in total_capacity_cost)
        total_capacity_cost.append(("overall", round(overall_capacity), round(overall_cost, 3)))

        # Create a structured array for total capacities and cost
        total_capacity_cost_array = np.array(total_capacity_cost, dtype=[('component', 'U10'), ('total_capacity', int), ('total_cost', float)])

        # Save the total capacities and cost in .npy and .txt files
        total_npy_file_path = os.path.join(results_dir, 'total_c.npy')
        total_txt_file_path = os.path.join(results_dir, 'total_c.txt')

        # Save as .npy file
        np.save(total_npy_file_path, total_capacity_cost_array)

        # Save as .txt file for easier viewing
        with open(total_txt_file_path, 'w') as file:
            file.write("Component, Total Capacity, Total Cost\n")
            for entry in total_capacity_cost_array:
                file.write(f'{entry[0]}, {entry[1]}, {entry[2]}\n')

        print(f'Saved total capacities and cost in {total_npy_file_path} and {total_txt_file_path}')

    # Set the path to the Scip solver executable
    scip_path = "C:\\Program Files\\SCIPOptSuite 9.0.0\\bin\\scip.exe"

    # Create a solver object and specify the solver executable path
    solver = SolverFactory('scip')
    solver.options['executable'] = scip_path

    # Define the path for the solver log
    solver_log_path = os.path.join(workspace_folder, "results", "combined", "solverlog_c.txt")

    # Solve the optimisation model
    results = solver.solve(model, tee=True, logfile=solver_log_path, options=solver_options)

    # Detailed checking of solver results
    if results.solver.status == SolverStatus.ok:
        if results.solver.termination_condition == TerminationCondition.optimal:
            print("Solver found an optimal solution.")
            print(f"Objective value: {round(model.global_cost_obj.expr(), 3)}")
            save_results(model, workspace_folder)
        elif results.solver.termination_condition == TerminationCondition.infeasible:
            print("Problem is infeasible. Check model constraints and data.")
        elif results.solver.termination_condition == TerminationCondition.unbounded:
            print("Problem is unbounded. Check objective function and constraints.")
        else:
            print(f"Solver terminated with condition: {results.solver.termination_condition}.")
    elif results.solver.status == SolverStatus.error:
        print("Solver error occurred. Check solver log for more details.")
    elif results.solver.status == SolverStatus.warning:
        print("Solver finished with warnings. Results may not be reliable.")
    else:
        print(f"Unexpected solver status: {results.solver.status}. Check solver log for details.")

    # Optionally, print a message about where the solver log was saved
    print(f"Solver log saved to {solver_log_path}")

    return None

# Define the main block
if __name__ == "__main__":
    # Specify the workspace folder
    workspace_folder = "C:\\Users\\cflde\\Documents\\Graduation Project\\ArcGIS Pro\\BalticSea\\Results\\datasets"

    # Call the optimization model function
    opt_model(workspace_folder)