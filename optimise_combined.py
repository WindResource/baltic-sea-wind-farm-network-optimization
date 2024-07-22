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
from scripts.present_value import present_value_single
from scripts.eh_cost import check_supp, equip_cost_lin, inst_deco_cost_lin

def eh_cost_lin(first_year, water_depth, ice_cover, port_distance, eh_capacity):
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
    # Determine support structure
    supp_structure = check_supp(water_depth)
    
    # Calculate equipment cost
    conv_cost, equip_cost = equip_cost_lin(water_depth, supp_structure, ice_cover, eh_capacity)

    # Calculate installation and decommissioning cost
    inst_cost = inst_deco_cost_lin(supp_structure, port_distance, "inst")
    deco_cost = inst_deco_cost_lin(supp_structure, port_distance, "deco")

    # Calculate yearly operational cost
    ope_cost_yearly = 0.03 * conv_cost
    
    # Calculate present value of cost    
    eh_cost = present_value_single(first_year, equip_cost, inst_cost, ope_cost_yearly, deco_cost)
    
    return eh_cost

def onss_cost_lin(first_year, capacity, threshold):
    """
    Calculate the cost for ONSS expansion above a certain capacity.

    Parameters:
    - capacity (float): The total capacity in MW for which the cost is to be calculated.
    - threshold (float): The capacity threshold in MW specific to the ONSS above which cost are incurred.
    
    Returns:
    - (float) Cost of expanding the ONSS if the capacity exceeds the threshold.
    """
    
    threshold_equip_cost = 0.02287 # Million EU/ MW
    
    # Calculate the cost function: difference between capacity and threshold multiplied by the cost factor
    equip_cost = (capacity - threshold) * threshold_equip_cost
    
    ope_cost_yearly = 0.015 * equip_cost
    
    inst_cost, deco_cost = 0, 0
    
    # Calculate present value
    total_cost = present_value_single(first_year, equip_cost, inst_cost, ope_cost_yearly, deco_cost)
    
    return total_cost

def ec1_cost_fun(first_year, distance, capacity, function="lin"):
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
    
    if function == "lin":
        parallel_cables = capacity / (cable_capacity * capacity_factor)
    elif function == "ceil":
        parallel_cables = np.ceil(capacity / (cable_capacity * capacity_factor))
    
    equip_cost = parallel_cables * cable_length * cable_equip_cost
    inst_cost = parallel_cables * cable_length * cable_inst_cost
    
    ope_cost_yearly = 0.2 * 1e-2 * equip_cost
    
    deco_cost = 0.5 * inst_cost

    # Calculate present value
    total_cost = present_value_single(first_year, equip_cost, inst_cost, ope_cost_yearly, deco_cost)

    return total_cost

def ec2_cost_fun(first_year, distance, capacity, function="lin"):
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
    
    if function == "lin":
        parallel_cables = capacity / (cable_capacity * capacity_factor)
    elif function == "ceil":
        parallel_cables = np.ceil(capacity / (cable_capacity * capacity_factor))
    
    equip_cost = parallel_cables * cable_length * cable_equip_cost
    inst_cost = parallel_cables * cable_length * cable_inst_cost
    
    ope_cost_yearly = 0.2 * 1e-2 * equip_cost
    
    deco_cost = 0.5 * inst_cost

    # Calculate present value
    total_cost = present_value_single(first_year, equip_cost, inst_cost, ope_cost_yearly, deco_cost)

    return total_cost

def ec3_cost_fun(first_year, distance, capacity, function="lin"):
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
    
    if function == "lin":
        parallel_cables = capacity / (cable_capacity * capacity_factor)
    elif function == "ceil":
        parallel_cables = np.ceil(capacity / (cable_capacity * capacity_factor))
    
    equip_cost = parallel_cables * cable_length * cable_equip_cost
    inst_cost = parallel_cables * cable_length * cable_inst_cost
    
    ope_cost_yearly = 0.2 * 1e-2 * equip_cost
    
    deco_cost = 0.5 * inst_cost

    # Calculate present value
    total_cost = present_value_single(first_year, equip_cost, inst_cost, ope_cost_yearly, deco_cost)

    return total_cost

def onc_cost_fun(first_year, distance, capacity, function="lin"):
    """
    Calculate the cost associated with selecting onshore substation cables for a given length and desired capacity.

    Parameters:
        distance (float): The length of the cable (in kilometers).
        capacity (float): The desired capacity of the cable (in MW).

    Returns:
        float: The total cost associated with the selected onshore substation cables.
    """
    cable_length = 1.10 * distance
    cable_capacity = 348  # MW (assuming same as export cable capacity)
    cable_equip_cost = 0.860  # Million EU/km
    cable_inst_cost = 0.540  # Million EU/km
    capacity_factor = 0.95
    
    if function == "lin":
        parallel_cables = capacity / (cable_capacity * capacity_factor)
    elif function == "ceil":
        parallel_cables = np.ceil(capacity / (cable_capacity * capacity_factor))
    
    equip_cost = parallel_cables * cable_length * cable_equip_cost
    inst_cost = parallel_cables * cable_length * cable_inst_cost
    
    ope_cost_yearly = 0.2 * 1e-2 * equip_cost
    deco_cost = 0.5 * inst_cost

    # Assuming a placeholder for present value calculation (to be defined)
    total_cost = present_value_single(first_year, equip_cost, inst_cost, ope_cost_yearly, deco_cost)

    return total_cost

def wf_cost_lin(wf_cost, wf_total_cap, wf_cap):
    """
    Calculate the cost of selecting and operating each wind farm based on the selected capacity.
    The cost is proportional to the selected capacity.
    
    Parameters:
    - wf_cost (float): The cost of the wind farm.
    - wf_total_cap (float): The total available capacity of the wind farm.
    - wf_cap (float): The selected capacity of the wind farm.
    
    Returns:
    - float: The calculated cost for the selected capacity.
    """
    return value(wf_cost) * (wf_cap / wf_total_cap)

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great-circle distance between two points in kilometers
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

def find_viable_ec1(wf_lon, wf_lat, eh_lon, eh_lat):
    """
    Find all pairs of offshore wind farms and energy hubs within 150km,
    ensuring that they belong to the same country based on their ISO codes.
    
    Parameters are dictionaries indexed by IDs with longitude, latitude, and ISO codes.
    """
    connections = []
    for wf_id, eh_id in product(wf_lon.keys(), eh_lon.keys()):
        # Calculate the distance first to see if they are within the viable range
        distance = haversine(wf_lon[wf_id], wf_lat[wf_id], eh_lon[eh_id], eh_lat[eh_id])
        if distance <= 250:  # Check if the distance is within 150 km
            connections.append((int(wf_id), int(eh_id)))
    return connections

def find_viable_ec2(eh_lon, eh_lat, onss_lon, onss_lat):
    """
    Find all pairs of offshore and onshore substations within 300km,
    ensuring that they belong to the same country based on their ISO codes.
    
    Parameters are dictionaries indexed by substation IDs with longitude, latitude, and ISO codes.
    """
    connections = []
    for eh_id, onss_id in product(eh_lon.keys(), onss_lon.keys()):
        # Calculate the distance first to see if they are within the viable range
        distance = haversine(eh_lon[eh_id], eh_lat[eh_id], onss_lon[onss_id], onss_lat[onss_id])
        if distance <= 250:  # Check if the distance is within 300 km
            connections.append((int(eh_id), int(onss_id)))
    return connections

def find_viable_ec3(wf_lon, wf_lat, onss_lon, onss_lat):
    """
    Find all pairs of wind farms and onshore substations within 450km,
    ensuring that they belong to the same country based on their ISO codes.
    
    Parameters are dictionaries indexed by IDs with longitude, latitude, and ISO codes.
    """
    connections = []
    for wf_id, onss_id in product(wf_lon.keys(), onss_lon.keys()):
        distance = haversine(wf_lon[wf_id], wf_lat[wf_id], onss_lon[onss_id], onss_lat[onss_id])
        if distance <= 500:  # Check if the distance is within 450 km
            connections.append((int(wf_id), int(onss_id)))
    return connections

def find_viable_onc(onss_lon, onss_lat):
    """
    Find all pairs of onshore substations within 100km,
    ensuring that they belong to the same country based on their ISO codes.
    
    Parameters are dictionaries indexed by IDs with longitude, latitude, and ISO codes.
    """
    connections = []
    for onss_id1, onss_id2 in product(onss_lon.keys(), repeat=2):
        if onss_id1 != onss_id2:  # Prevent self-connections
            distance = haversine(onss_lon[onss_id1], onss_lat[onss_id1], onss_lon[onss_id2], onss_lat[onss_id2])
            if distance <= 250:  # Check if the distance is within 100 km
                connections.append((int(onss_id1), int(onss_id2)))
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

def opt_model(workspace_folder, model_type=0, cross_border=0, multi_stage=0):
    """
    Create an optimization model for offshore wind farm layout optimization.

    Parameters:
    - workspace_folder (str): The path to the workspace folder containing datasets.
    - model_type (int): The type of the model (0, 1, or 2).
    - cross_border (int): Whether to allow cross-border connections (0 or 1).
    - multi_stage (int): 0 for a single stage optimization for 2050, 1 for a multistage optimization for 2030, 2040, 2050.

    Returns:
    - model: Pyomo ConcreteModel object representing the optimization model.
    """
    """
    Initialise model
    """
    print("Initialising model...")
    
    # Create a Pyomo model
    model = ConcreteModel()
    
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
    
    "Define General Parameters"
    
    zero_th = 1e-2 # Define the zero threshold parameter
    
    wt_cap = 15  # Define the wind turbine capacity (MW)
    eh_cap_lim = 2500 # Define the energy hub capacity limit (MW)
    onss_cap_lim_fac= 2.5 # Define the onshore substation capacity limit factor
    
    # Select countries to be included in the optimization
    select_countries = {
        'DE': 1,  # Germany
        'DK': 1,  # Denmark
        'EE': 1,  # Estonia
        'FI': 1,  # Finland
        'LV': 1,  # Latvia
        'LT': 1,  # Lithuania
        'PL': 1,  # Poland
        'SE': 1   # Sweden
    }
    
    solver_options = {
        'limits/gap': 0,                  # Stop when the relative optimality gap is 0.6%
        'limits/nodes': 1e5,                 # Maximum number of nodes in the search tree
        'limits/solutions': -1,             # Limit on the number of solutions found
        'limits/time': 3600,                 # Set a time limit of 3600 seconds (1 hour)
        'numerics/feastol': 1e-5,           # Feasibility tolerance for constraints
        'numerics/dualfeastol': 1e-5,       # Tolerance for dual feasibility conditions
        'presolving/maxrounds': -1,          # Maximum number of presolve iterations (-1 for no limit)
        'propagating/maxrounds': -1,         # Maximum number of propagation rounds (-1 for no limit)
        'propagating/maxroundsroot': -1,     # Propagation rounds at the root node
        'separating/maxrounds': -1,          # Maximum cut rounds at non-root nodes
        'display/verblevel': 4               # Verbosity level to display detailed information about the solution process
    }
    
    "Define Single Stage Optimization Parameters"
    
    # Define the year to be optimized for single stage
    first_year_sf = 2040
    
    # Define the base capacity fractions for the final year
    base_country_cf_sf = {
        'DE': 1,  # Germany
        'DK': 1,  # Denmark
        'EE': 1,  # Estonia
        'FI': 1,  # Finland
        'LV': 1,  # Latvia
        'LT': 1,  # Lithuania
        'PL': 1,  # Poland
        'SE': 1   # Sweden
    }
    
    # Adjust base capacity fractions for each country based on a selection parameter (select_countries)
    adj_country_cf_sf = {iso: base_country_cf_sf[iso] * select_countries[iso] for iso in base_country_cf_sf}

    # Convert adjusted country capacity fractions to use integer keys instead of ISO country codes
    country_cf_sf = {int(iso_to_int_mp[iso]): adj_country_cf_sf[iso] for iso in adj_country_cf_sf}
    
    "Define Multi Stage Optimization Parameters"
    
    # Define the years to be optimized for multi-stage
    first_year_mf_1 = 2030
    first_year_mf_2 = 2040
    first_year_mf_3 = 2050

    # Define the development fractions for each year
    dev_frac_mf_1 = 0.3056
    dev_frac_mf_2 = 0.7115
    dev_frac_mf_3 = 1.00

    # Define the base capacity fractions for the final year
    base_country_cf_mf = {
        'DE': 1,  # Germany
        'DK': 1,  # Denmark
        'EE': 1,  # Estonia
        'FI': 1,  # Finland
        'LV': 1,  # Latvia
        'LT': 1,  # Lithuania
        'PL': 1,  # Poland
        'SE': 1   # Sweden
    }

    # Calculate base capacity fractions for 2030 and 2040 using development fractions
    base_country_cf_mf_1 = {country: dev_frac_mf_1 * cf for country, cf in base_country_cf_mf.items()}
    base_country_cf_mf_2 = {country: dev_frac_mf_2 * cf for country, cf in base_country_cf_mf.items()}
    base_country_cf_mf_3 = {country: dev_frac_mf_3 * cf for country, cf in base_country_cf_mf.items()}

    # Adjust base capacity fractions for each country based on a selection parameter (select_countries)
    adj_country_cf_mf_1 = {iso: base_country_cf_mf_1[iso] * select_countries[iso] for iso in base_country_cf_mf_1}
    adj_country_cf_mf_2 = {iso: base_country_cf_mf_2[iso] * select_countries[iso] for iso in base_country_cf_mf_2}
    adj_country_cf_mf_3 = {iso: base_country_cf_mf_3[iso] * select_countries[iso] for iso in base_country_cf_mf_3}

    # Convert adjusted country capacity fractions to use integer keys instead of ISO country codes
    country_cf_mf_1 = {int(iso_to_int_mp[iso]): adj_country_cf_mf_1[iso] for iso in adj_country_cf_mf_1}
    country_cf_mf_2 = {int(iso_to_int_mp[iso]): adj_country_cf_mf_2[iso] for iso in adj_country_cf_mf_2}
    country_cf_mf_3 = {int(iso_to_int_mp[iso]): adj_country_cf_mf_3[iso] for iso in adj_country_cf_mf_3}

    """
    Process data
    """
    print("Processing data...")
    
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
    wf_iso, wf_lon, wf_lat, wf_cap, wf_cost_1, wf_cost_2, wf_cost_3 = {}, {}, {}, {}, {}, {}, {}

    for data in wf_dataset:
        id = int(data[0])
        wf_iso[id] = iso_to_int_mp[data[1]]
        wf_lon[id] = float(data[2])
        wf_lat[id] = float(data[3])
        wf_cap[id] = float(data[4])
        wf_cost_1[id] = float(data[5])
        wf_cost_2[id] = float(data[6])
        wf_cost_3[id] = float(data[7])

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
    
    # Define the set of countries based on the ISO codes
    model.country_ids = Set(initialize=iso_to_int_mp.values())
    
    # Wind farm model parameters
    model.wf_iso = Param(model.wf_ids, initialize=wf_iso, within=NonNegativeIntegers)
    model.wf_lon = Param(model.wf_ids, initialize=wf_lon, within=NonNegativeReals)
    model.wf_lat = Param(model.wf_ids, initialize=wf_lat, within=NonNegativeReals)
    model.wf_cap = Param(model.wf_ids, initialize=wf_cap, within=NonNegativeIntegers)

    model.wf_cost = Param(model.wf_ids, initialize=wf_cost_1, within=NonNegativeReals, mutable=True)
    model.wf_cost_1 = Param(model.wf_ids, initialize=wf_cost_1, within=NonNegativeReals)
    model.wf_cost_2 = Param(model.wf_ids, initialize=wf_cost_2, within=NonNegativeReals)
    model.wf_cost_3 = Param(model.wf_ids, initialize=wf_cost_3, within=NonNegativeReals)

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

    # Define parameters for capacity fractions for each year
    model.country_cf = Param(model.country_ids, initialize=country_cf_sf, within=NonNegativeReals, mutable=True)
    # Single stage
    model.country_cf_sf = Param(model.country_ids, initialize=country_cf_sf, within=NonNegativeReals)
    # Multi stage
    model.country_cf_mf_1 = Param(model.country_ids, initialize=country_cf_mf_1, within=NonNegativeReals)
    model.country_cf_mf_2 = Param(model.country_ids, initialize=country_cf_mf_2, within=NonNegativeReals)
    model.country_cf_mf_3 = Param(model.country_ids, initialize=country_cf_mf_3, within=NonNegativeReals)
    
    # Define the first years
    model.first_year = Param(initialize=first_year_sf, within=NonNegativeIntegers, mutable=True)
    # Single stage
    model.first_year_sf = Param(initialize=first_year_sf, within=NonNegativeIntegers)
    # Multi stage
    model.first_year_mf_1 = Param(initialize=first_year_mf_1, within=NonNegativeIntegers)
    model.first_year_mf_2 = Param(initialize=first_year_mf_2, within=NonNegativeIntegers)
    model.first_year_mf_3 = Param(initialize=first_year_mf_3, within=NonNegativeIntegers)

    """
    Define decision variables
    """
    print("Defining decision variables...")
    
    # Calculate viable connections
    viable_ec1 = find_viable_ec1(wf_lon, wf_lat, eh_lon, eh_lat)
    viable_ec2 = find_viable_ec2(eh_lon, eh_lat, onss_lon, onss_lat)
    viable_ec3 = find_viable_ec3(wf_lon, wf_lat, onss_lon, onss_lat)
    viable_onc = find_viable_onc(onss_lon, onss_lat)
    
    model.viable_ec1_ids = Set(initialize=viable_ec1, dimen=2)
    model.viable_ec2_ids = Set(initialize=viable_ec2, dimen=2)
    model.viable_ec3_ids = Set(initialize=viable_ec3, dimen=2)
    model.viable_onc_ids = Set(initialize=viable_onc, dimen=2)
    
    # Calculate viable entities based on the viable connections
    model.viable_wf_ids, model.viable_eh_ids, model.viable_onss_ids = get_viable_entities(viable_ec1, viable_ec2, viable_ec3)
    
    # Initialize variables without time index for capacity
    model.wf_cap_var = Var(model.viable_wf_ids, within=NonNegativeReals)
    model.onss_cap_var = Var(model.viable_onss_ids, within=NonNegativeReals)
    model.onc_cap_var = Var(model.viable_onc_ids, within=NonNegativeReals)
    
    if model_type == 0: # Point-to-point connections
        model.eh_cap_var = Var(model.viable_eh_ids, within=NonNegativeReals, bounds=(0, 0))
        model.ec1_cap_var = Var(model.viable_ec1_ids, within=NonNegativeReals, bounds=(0, 0))
        model.ec2_cap_var = Var(model.viable_ec2_ids, within=NonNegativeReals, bounds=(0, 0))
        model.ec3_cap_var = Var(model.viable_ec3_ids, within=NonNegativeReals)
    elif model_type == 1: # Hub-and-spoke connections
        model.eh_cap_var = Var(model.viable_eh_ids, within=NonNegativeReals)
        model.ec1_cap_var = Var(model.viable_ec1_ids, within=NonNegativeReals)
        model.ec2_cap_var = Var(model.viable_ec2_ids, within=NonNegativeReals)
        model.ec3_cap_var = Var(model.viable_ec3_ids, within=NonNegativeReals, bounds=(0, 0))
    elif model_type == 2: # Combined connections
        model.eh_cap_var = Var(model.viable_eh_ids, within=NonNegativeReals)
        model.ec1_cap_var = Var(model.viable_ec1_ids, within=NonNegativeReals)
        model.ec2_cap_var = Var(model.viable_ec2_ids, within=NonNegativeReals)
        model.ec3_cap_var = Var(model.viable_ec3_ids, within=NonNegativeReals)

    # Initialize variables with time index for costs
    model.wf_cost_var = Var(model.viable_wf_ids, within=NonNegativeReals)
    model.eh_cost_var = Var(model.viable_eh_ids, within=NonNegativeReals)
    model.onss_cost_var = Var(model.viable_onss_ids, within=NonNegativeReals)
    model.ec1_cost_var = Var(model.viable_ec1_ids, within=NonNegativeReals)
    model.ec2_cost_var = Var(model.viable_ec2_ids, within=NonNegativeReals)
    model.ec3_cost_var = Var(model.viable_ec3_ids, within=NonNegativeReals)
    model.onc_cost_var = Var(model.viable_onc_ids, within=NonNegativeReals)
    
    model.wf_country_alloc_var = Var(model.viable_wf_ids, model.country_ids, within=NonNegativeReals)
    
    # Define the binary variable for each energy hub
    model.eh_active_bin_var = Var(model.viable_eh_ids, within=Binary)
    
    # Print total available wind farm capacity per country
    print("Total available wind farm capacity per country:")
    for country, country_code in iso_to_int_mp.items():
        total_capacity = sum(wf_cap[wf] for wf in wf_ids if wf_iso[wf] == country_code)
        print(f"{country}: {total_capacity} MW")
    
    # Define a dictionary containing variable names and their respective lengths
    print_variables = {
        "select_wf": model.wf_cap_var,
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
        return wf_cost_lin(model.wf_cost[wf], model.wf_cap[wf], model.wf_cap_var[wf])
    model.wf_cost_exp = Expression(model.viable_wf_ids, rule=wf_cost_rule)

    """
    Define distance and capacity expressions for Inter-Array Cables (IAC)
    """
    def ec1_distance_rule(model, wf, eh):
        return haversine(model.wf_lon[wf], model.wf_lat[wf], model.eh_lon[eh], model.eh_lat[eh])
    model.ec1_dist_exp = Expression(model.viable_ec1_ids, rule=ec1_distance_rule)

    def ec1_cost_rule(model, wf, eh):
        return ec1_cost_fun(value(model.first_year), model.ec1_dist_exp[wf, eh], model.ec1_cap_var[wf, eh])
    model.ec1_cost_exp = Expression(model.viable_ec1_ids, rule=ec1_cost_rule)

    """
    Define expressions for the Energy Hub (EH) capacity
    """
    def eh_cost_rule_with_binary(model, eh):
        return model.eh_active_bin_var[eh] * eh_cost_lin(value(model.first_year), model.eh_wdepth[eh], model.eh_icover[eh], model.eh_pdist[eh], model.eh_cap_var[eh])
    model.eh_cost_exp = Expression(model.viable_eh_ids, rule=eh_cost_rule_with_binary)

    """
    Define distance and capacity expressions for Export Cables (EC)
    """
    def ec2_distance_rule(model, eh, onss):
        return haversine(model.eh_lon[eh], model.eh_lat[eh], model.onss_lon[onss], model.onss_lat[onss])
    model.ec2_dist_exp = Expression(model.viable_ec2_ids, rule=ec2_distance_rule)

    def ec2_cost_rule(model, eh, onss):
        return ec2_cost_fun(value(model.first_year), model.ec2_dist_exp[eh, onss], model.ec2_cap_var[eh, onss])
    model.ec2_cost_exp = Expression(model.viable_ec2_ids, rule=ec2_cost_rule)

    """
    Define distance and capacity expressions for direct connections (WF to ONSS)
    """
    def ec3_distance_rule(model, wf, onss):
        return haversine(model.wf_lon[wf], model.wf_lat[wf], model.onss_lon[onss], model.onss_lat[onss])
    model.ec3_dist_exp = Expression(model.viable_ec3_ids, rule=ec3_distance_rule)

    def ec3_cost_rule(model, wf, onss):
        return ec3_cost_fun(value(model.first_year), model.ec3_dist_exp[wf, onss], model.ec3_cap_var[wf, onss])
    model.ec3_cost_exp = Expression(model.viable_ec3_ids, rule=ec3_cost_rule)

    """
    Define expressions for Onshore Substation (ONSS) capacity
    """
    def onss_cost_rule(model, onss):
        return onss_cost_lin(value(model.first_year), model.onss_cap_var[onss], model.onss_thold[onss])
    model.onss_cost_exp = Expression(model.viable_onss_ids, rule=onss_cost_rule)

    """
    Define expressions for Onshore Substation Cables (ONC)
    """
    def onc_distance_rule(model, onss1, onss2):
        return haversine(model.onss_lon[onss1], model.onss_lat[onss1], model.onss_lon[onss2], model.onss_lat[onss2])
    model.onc_dist_exp = Expression(model.viable_onc_ids, rule=onc_distance_rule)

    def onc_cost_rule(model, onss1, onss2):
        return onc_cost_fun(value(model.first_year), model.onc_dist_exp[onss1, onss2], model.onc_cap_var[onss1, onss2])
    model.onc_cost_exp = Expression(model.viable_onc_ids, rule=onc_cost_rule)

    """
    Define Constraints
    """
    print("Defining capacity allocation constraints...")

    if cross_border == 1:
        def wf_country_cap_rule(model, country):
            """
            Ensure the selected wind farms collectively meet a minimum required capacity for each country.
            This capacity is specified as a fraction of the total potential capacity of all considered wind farms.
            """
            min_req_cap_country = model.country_cf[country] * sum(model.wf_cap[wf] for wf in model.viable_wf_ids if model.wf_iso[wf] == country)
            cap_country = sum(model.wf_country_alloc_var[wf, country] for wf in model.viable_wf_ids)
            return cap_country >= min_req_cap_country
        model.wf_country_cap_con = Constraint(model.country_ids, rule=wf_country_cap_rule)
    elif cross_border == 0:
        def wf_country_cap_rule(model, country):
            """
            Ensure the selected wind farms collectively meet a minimum required capacity for each country.
            This capacity is specified as a fraction of the total potential capacity of all considered wind farms.
            """
            min_req_cap_country = model.country_cf[country] * sum(model.wf_cap[wf] for wf in model.viable_wf_ids if model.wf_iso[wf] == country)
            cap_country = sum(model.wf_country_alloc_var[wf, country] for wf in model.viable_wf_ids if model.wf_iso[wf] == country)
            return cap_country >= min_req_cap_country
        model.wf_country_cap_con = Constraint(model.country_ids, rule=wf_country_cap_rule)
    
    def wf_alloc_rule(model, wf):
        """
        Ensure the allocated capacity of each wind farm equals the total capacity based on the selected capacity.
        Each wind farm's capacity allocation must match the selected capacity.
        """
        return sum(model.wf_country_alloc_var[wf, country] for country in model.country_ids) == model.wf_cap_var[wf]
    model.wf_alloc_con = Constraint(model.viable_wf_ids, rule=wf_alloc_rule)

    def wf_cap_rule(model, wf):
        """
        Ensure the capacity of each wind farm does not exceed the wind farm's total available capacity.
        """
        return model.wf_cap_var[wf] <= model.wf_cap[wf]
    model.wf_cap_con = Constraint(model.viable_wf_ids, rule=wf_cap_rule)

    print("Defining network constraints...")
    
    def wf_connection_rule(model, wf, country):
        """
        Ensure the allocated capacity of each wind farm is properly connected to the energy hub or onshore substation 
        of the corresponding country. The capacity connected must be at least the allocated capacity for the country.
        """
        connect_to_eh = sum(model.ec1_cap_var[wf, eh] for eh in model.viable_eh_ids if (wf, eh) in model.viable_ec1_ids and model.eh_iso[eh] == country)
        connect_to_onss = sum(model.ec3_cap_var[wf, onss] for onss in model.viable_onss_ids if (wf, onss) in model.viable_ec3_ids and model.onss_iso[onss] == country)
        return connect_to_eh + connect_to_onss >= model.wf_country_alloc_var[wf, country]
    model.wf_connection_con = Constraint(model.viable_wf_ids, model.country_ids, rule=wf_connection_rule)

    def eh_cap_connect_rule(model, eh):
        """
        Ensure the capacity of each energy hub matches or exceeds the total capacity of the connected wind farms.
        """
        connect_from_wf = sum(model.ec1_cap_var[wf, eh] for wf in model.viable_wf_ids if (wf, eh) in model.viable_ec1_ids)
        return model.eh_cap_var[eh] >= connect_from_wf
    model.eh_cap_connect_con = Constraint(model.viable_eh_ids, rule=eh_cap_connect_rule)

    def eh_active_rule(model, eh):
        """
        Ensures that the capacity of the energy hub (eh_cap_var) can only be greater than zero if the energy hub is active (eh_active_var is 1). 
        A small value (zero_th) is added to account for potential rounding errors, allowing for numerical stability in the constraint.
        """
        return model.eh_cap_var[eh] <= model.eh_active_bin_var[eh] * eh_cap_lim + zero_th
    model.eh_cap_to_active_con = Constraint(model.viable_eh_ids, rule=eh_active_rule)

    def eh_inactive_rule(model, eh):
        """
        Ensures that the capacity of the energy hub (eh_cap_var) is zero when the energy hub is inactive (eh_active_var is 0). 
        A small value (zero_th) is added to account for potential rounding errors, allowing for numerical stability in the constraint.
        """
        return model.eh_cap_var[eh] + zero_th >= model.eh_active_bin_var[eh]
    model.eh_inactive_cap_zero_con = Constraint(model.viable_eh_ids, rule=eh_inactive_rule)

    def eh_to_onss_connection_rule(model, eh):
        """
        Ensure the capacity of each energy hub is connected to an onshore substation of the corresponding country.
        """
        country = model.eh_iso[eh]
        connect_to_onss = sum(model.ec2_cap_var[eh, onss] for onss in model.viable_onss_ids if (eh, onss) in model.viable_ec2_ids and model.onss_iso[onss] == country)
        return connect_to_onss >= model.eh_cap_var[eh]
    model.eh_to_onss_connect_con = Constraint(model.viable_eh_ids, rule=eh_to_onss_connection_rule)

    def onss_cap_connect_rule(model, onss):
        """
        Ensure the capacity of each onshore substation is at least the total incoming capacity from connected energy hubs or wind farms,
        considering only national connections for transfers to and from other onshore substations.
        """
        country = model.onss_iso[onss]
        connect_from_eh = sum(model.ec2_cap_var[eh, onss] for eh in model.viable_eh_ids if (eh, onss) in model.viable_ec2_ids)
        connect_from_wf = sum(model.ec3_cap_var[wf, onss] for wf in model.viable_wf_ids if (wf, onss) in model.viable_ec3_ids)
        distribute_to_others = sum(model.onc_cap_var[onss, other_onss] for other_onss in model.viable_onss_ids if (onss, other_onss) in model.viable_onc_ids and model.onss_iso[other_onss] == country)
        receive_from_others = sum(model.onc_cap_var[other_onss, onss] for other_onss in model.viable_onss_ids if (other_onss, onss) in model.viable_onc_ids and model.onss_iso[other_onss] == country)
        
        return model.onss_cap_var[onss] >= connect_from_eh + connect_from_wf + receive_from_others - distribute_to_others
    model.onss_cap_connect_con = Constraint(model.viable_onss_ids, rule=onss_cap_connect_rule)

    print("Defining capacity limit constraints...")
    
    def max_eh_cap_rule(model, eh):
        """
        Ensure the capacity of each energy hub does not exceed a certain capacity in MW.
        """
        return model.eh_cap_var[eh] <= eh_cap_lim
    model.max_eh_cap_con = Constraint(model.viable_eh_ids, rule=max_eh_cap_rule)

    def max_onss_cap_rule(model, onss):
        """
        Ensure the capacity of each onshore substation does not exceed twice the threshold value.
        """
        return model.onss_cap_var[onss] <= onss_cap_lim_fac * model.onss_thold[onss]
    model.max_onss_cap_con = Constraint(model.viable_onss_ids, rule=max_onss_cap_rule)
    
    print("Defining cost constraints...")
    
    def onss_cost_rule(model, onss):
        """
        Ensure the cost variable for each onshore substation meets or exceeds the calculated cost.
        """
        return model.onss_cost_var[onss] >= model.onss_cost_exp[onss]
    model.onss_cost_con = Constraint(model.viable_onss_ids, rule=onss_cost_rule)
    
    """
    Define Objective function
    """
    print("Defining objective function...")

    def global_cost_rule(model):
        """
        Calculate the total cost of the energy system for a specific year.
        This includes the cost of selecting and connecting wind farms, energy hubs, and onshore substations.
        The objective is to minimize this total cost for each year separately.
        """
        wf_total_cost = sum(model.wf_cost_exp[wf] for wf in model.viable_wf_ids)
        eh_total_cost = sum(model.eh_cost_exp[eh] for eh in model.viable_eh_ids)
        onss_total_cost = sum(model.onss_cost_var[onss] for onss in model.viable_onss_ids)
        ec1_total_cost = sum(model.ec1_cost_exp[wf, eh] for (wf, eh) in model.viable_ec1_ids)
        ec2_total_cost = sum(model.ec2_cost_exp[eh, onss] for (eh, onss) in model.viable_ec2_ids)
        ec3_total_cost = sum(model.ec3_cost_exp[wf, onss] for (wf, onss) in model.viable_ec3_ids)
        onc_total_cost = sum(model.onc_cost_exp[onss1, onss2] for (onss1, onss2) in model.viable_onc_ids)
        
        onss_total_cap_aux = sum(model.onss_cap_var[onss] for onss in model.viable_onss_ids) # Ensures that the onss capacity is zero when not connected
        
        total_cost = wf_total_cost + eh_total_cost + ec1_total_cost + ec2_total_cost + ec3_total_cost + onss_total_cost + onc_total_cost + onss_total_cap_aux

        return total_cost
    model.global_cost_obj = Objective(rule=global_cost_rule, sense=minimize)

    """
    Solve the model
    """
    print("Solving the model...")
    
    # Set the path to the SCIP solver executable
    scip_path = "C:\\Program Files\\SCIPOptSuite 9.0.0\\bin\\scip.exe"
    
    # Write options to a parameter file
    param_file_path = os.path.join(workspace_folder, "scip_params.set")
    
    # Create solver object and specify the solver executable path
    solver = SolverFactory('scip', executable=scip_path)
    
    with open(param_file_path, 'w') as param_file:
        for key, val in solver_options.items():
            param_file.write(f"{key} = {val}\n")

    def rnd_f(e):
            return round(value(e), 3)
    
    def nearest_wt_cap(cap):
        """
        Round up the capacity to the nearest multiple of the wind turbine capacity.
        """
        return int(np.ceil(value(cap) / wt_cap)) * wt_cap
    
    def save_results(model, workspace_folder, year, prev_capacity):
        """
        Save the IDs of selected components of the optimization model along with all their corresponding parameters,
        including directly retrieved capacity and cost from the model expressions, into both .npy and .txt files as structured arrays.
        Headers are included in the .txt files for clarity.

        Parameters:
        - model: The optimized Pyomo model.
        - workspace_folder: The path to the directory where results will be saved.
        - year: The year for which the results are being saved.
        """

        # Mapping ISO country codes of Baltic Sea countries to unique integers
        int_to_iso_mp = {
            1: 'DE',  # Germany
            2: 'DK',  # Denmark
            3: 'EE',  # Estonia
            4: 'FI',  # Finland
            5: 'LV',  # Latvia
            6: 'LT',  # Lithuania
            7: 'PL',  # Poland
            8: 'SE'   # Sweden
        }

        selected_components = {}
        
        if model_type == 0:
            tpe = "d"
        if model_type == 1:
            tpe = "hs"
        if model_type == 2:
            tpe = "c"
        
        if cross_border == 0:
            crb = "n"
        if cross_border == 1:
            crb = "in"
        
        if multi_stage == 0:
            stg = "sf"
        if multi_stage == 1:
            stg = "mf"
        
        # Define and aggregate data for wind farms
        wf_data = []
        for wf in model.viable_wf_ids:
            if value(model.wf_cap_var[wf]) > zero_th:
                wf_id = wf
                wf_iso = int_to_iso_mp[int(model.wf_iso[wf])]
                wf_lon = model.wf_lon[wf]
                wf_lat = model.wf_lat[wf]
                wf_capacity = rnd_f(model.wf_cap_var[wf])
                wf_rate = rnd_f(value(wf_capacity) / value(model.wf_cap[wf]))
                wf_cost = rnd_f(nearest_wt_cap(wf_capacity) / value(model.wf_cap[wf]) * value(model.wf_cost[wf]))
                wf_data.append((wf_id, wf_iso, wf_lon, wf_lat, wf_capacity, wf_cost, wf_rate))

        selected_components['wf_ids'] = {
            'data': np.array(wf_data, dtype=[('id', int), ('iso', 'U2'), ('lon', float), ('lat', float), ('capacity', int), ('cost', float), ('rate', float)]),
            'headers': "ID, ISO, Longitude, Latitude, Capacity, Cost, Rate"
        }

        # Define and aggregate data for energy hubs
        eh_data = []
        for eh in model.viable_eh_ids:
            if value(model.eh_cap_var[eh]) > zero_th:
                eh_id = eh
                eh_iso = int_to_iso_mp[int(model.eh_iso[eh])]
                eh_lon = model.eh_lon[eh]
                eh_lat = model.eh_lat[eh]
                eh_water_depth = model.eh_wdepth[eh]
                eh_ice_cover = model.eh_icover[eh]
                eh_port_dist = model.eh_pdist[eh]
                eh_capacity = rnd_f(model.eh_cap_var[eh])
                eh_cost = rnd_f(model.eh_cost_exp[eh])
                eh_data.append((eh_id, eh_iso, eh_lon, eh_lat, eh_water_depth, eh_ice_cover, eh_port_dist, eh_capacity, eh_cost))

        selected_components['eh_ids'] = {
            'data': np.array(eh_data, dtype=[('id', int), ('iso', 'U2'), ('lon', float), ('lat', float), ('water_depth', int), ('ice_cover', int), ('port_dist', int), ('capacity', float), ('cost', float)]),
            'headers': "ID, ISO, Longitude, Latitude, Water Depth, Ice Cover, Port Distance, Capacity, Cost"
        }

        # Define and aggregate data for onshore substations
        onss_data = []
        for onss in model.viable_onss_ids:
            if value(model.onss_cap_var[onss]) > zero_th:
                onss_id = onss
                onss_iso = int_to_iso_mp[int(model.onss_iso[onss])]
                onss_lon = model.onss_lon[onss]
                onss_lat = model.onss_lat[onss]
                onss_threshold = model.onss_thold[onss]
                onss_cap = rnd_f(model.onss_cap_var[onss])
                onss_cap_diff = onss_cap - prev_capacity.get('onss_ids', {}).get(onss, 0)
                onss_cost = rnd_f(max(0, onss_cost_lin(value(model.first_year), onss_cap_diff, model.onss_thold[onss])))
                onss_data.append((onss_id, onss_iso, onss_lon, onss_lat, onss_threshold, onss_cap, onss_cost))

        selected_components['onss_ids'] = {
            'data': np.array(onss_data, dtype=[('id', int), ('iso', 'U2'), ('lon', float), ('lat', float), ('threshold', int), ('capacity', float), ('cost', float)]),
            'headers': "ID, ISO, Longitude, Latitude, Threshold, Capacity, Cost"
        }

        # Export cable ID counter
        ec_id_counter = 1

        # Create ec1_ids with export cable ID, single row for each cable
        ec1_data = []
        for wf, eh in model.viable_ec1_ids:
            if value(model.ec1_cap_var[wf, eh]) > zero_th:
                ec1_cap = rnd_f(model.ec1_cap_var[wf, eh])
                dist1 = rnd_f(haversine(model.wf_lon[wf], model.wf_lat[wf], model.eh_lon[eh], model.eh_lat[eh]))
                ec1_cost = rnd_f(ec1_cost_fun(value(model.first_year), dist1, ec1_cap, "ceil"))
                ec1_data.append((ec_id_counter, int_to_iso_mp[int(model.eh_iso[eh])], wf, eh, model.wf_lon[wf], model.wf_lat[wf], model.eh_lon[eh], model.eh_lat[eh], dist1, ec1_cap, ec1_cost))
                ec_id_counter += 1

        selected_components['ec1_ids'] = {
            'data': np.array(ec1_data, dtype=[('ec_id', int), ('iso', 'U2'), ('comp_1_id', int), ('comp_2_id', int), ('lon_1', float), ('lat_1', float), ('lon_2', float), ('lat_2', float), ('distance', float), ('capacity', float), ('cost', float)]),
            'headers': "EC_ID, ISO, Comp_1_ID, Comp_2_ID, Lon_1, Lat_1, Lon_2, Lat_2, Distance, Capacity, Cost"
        }

        # Create ec2_ids with export cable ID, single row for each cable
        ec2_data = []
        ec_id_counter = 1
        for eh, onss in model.viable_ec2_ids:
            if value(model.ec2_cap_var[eh, onss]) > zero_th:
                ec2_cap = rnd_f(model.ec2_cap_var[eh, onss])
                dist2 = rnd_f(haversine(model.eh_lon[eh], model.eh_lat[eh], model.onss_lon[onss], model.onss_lat[onss]))
                ec2_cost = rnd_f(ec2_cost_fun(value(model.first_year), dist2, ec2_cap, "ceil"))
                ec2_data.append((ec_id_counter, int_to_iso_mp[int(model.onss_iso[onss])], eh, onss, model.eh_lon[eh], model.eh_lat[eh], model.onss_lon[onss], model.onss_lat[onss], dist2, ec2_cap, ec2_cost))
                ec_id_counter += 1

        selected_components['ec2_ids'] = {
            'data': np.array(ec2_data, dtype=[('ec_id', int), ('iso', 'U2'), ('comp_1_id', int), ('comp_2_id', int), ('lon_1', float), ('lat_1', float), ('lon_2', float), ('lat_2', float), ('distance', float), ('capacity', float), ('cost', float)]),
            'headers': "EC_ID, ISO, Comp_1_ID, Comp_2_ID, Lon_1, Lat_1, Lon_2, Lat_2, Distance, Capacity, Cost"
        }

        # Create ec3_ids with export cable ID, single row for each cable
        ec3_data = []
        ec_id_counter = 1
        for wf, onss in model.viable_ec3_ids:
            if value(model.ec3_cap_var[wf, onss]) > zero_th:
                ec3_cap = rnd_f(model.ec3_cap_var[wf, onss])
                dist3 = rnd_f(haversine(model.wf_lon[wf], model.wf_lat[wf], model.onss_lon[onss], model.onss_lat[onss]))
                ec3_cost = rnd_f(ec3_cost_fun(value(model.first_year), dist3, ec3_cap, "ceil"))
                ec3_data.append((ec_id_counter, int_to_iso_mp[int(model.onss_iso[onss])], wf, onss, model.wf_lon[wf], model.wf_lat[wf], model.onss_lon[onss], model.onss_lat[onss], dist3, ec3_cap, ec3_cost))
                ec_id_counter += 1

        selected_components['ec3_ids'] = {
            'data': np.array(ec3_data, dtype=[('ec_id', int), ('iso', 'U2'), ('comp_1_id', int), ('comp_2_id', int), ('lon_1', float), ('lat_1', float), ('lon_2', float), ('lat_2', float), ('distance', float), ('capacity', float), ('cost', float)]),
            'headers': "EC_ID, ISO, Comp_1_ID, Comp_2_ID, Lon_1, Lat_1, Lon_2, Lat_2, Distance, Capacity, Cost"
        }

        # Create onc_ids with onshore cable ID, single row for each cable
        onc_data = []
        onc_id_counter = 1
        for onss1, onss2 in model.viable_onc_ids:
            if value(model.onc_cap_var[onss1, onss2]) is not None and value(model.onc_cap_var[onss1, onss2]) > zero_th:
                onc_cap = rnd_f(model.onc_cap_var[onss1, onss2])
                onc_cap_diff = onc_cap - prev_capacity.get('onc_ids', {}).get((onss1, onss2), 0)
                dist4 = rnd_f(haversine(model.onss_lon[onss1], model.onss_lat[onss1], model.onss_lon[onss2], model.onss_lat[onss2]))
                onc_cost = rnd_f(onc_cost_fun(value(model.first_year), dist4, onc_cap_diff, "ceil"))
                onc_data.append((onc_id_counter, int_to_iso_mp[int(model.onss_iso[onss1])], onss1, onss2, model.onss_lon[onss1], model.onss_lat[onss1], model.onss_lon[onss2], model.onss_lat[onss2], dist4, onc_cap, onc_cost))
                onc_id_counter += 1

        selected_components['onc_ids'] = {
            'data': np.array(onc_data, dtype=[('ec_id', int), ('iso', 'U2'), ('comp_1_id', int), ('comp_2_id', int), ('lon_1', float), ('lat_1', float), ('lon_2', float), ('lat_2', float), ('distance', float), ('capacity', float), ('cost', float)]),
            'headers': "ONC_ID, ISO, Comp_1_ID, Comp_2_ID, Lon_1, Lat_1, Lon_2, Lat_2, Distance, Capacity, Cost"
        }

        # Ensure the results directory exists
        results_dir = os.path.join(workspace_folder, "results", "combined")
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)

        # Save the .npy and .txt files for each component
        for component, data in selected_components.items():
            # Save as .npy file
            npy_file_path = os.path.join(results_dir, f'r_{stg}_{tpe}_{crb}_{component}_{year}.npy')
            np.save(npy_file_path, data['data'])
            print(f'Saved {component} data in {npy_file_path}')
            
            # Save as .txt file
            txt_file_path = os.path.join(results_dir, f'r_{stg}_{tpe}_{crb}_{component}_{year}.txt')
            with open(txt_file_path, 'w') as file:
                file.write(data['headers'] + "\n")
                for entry in data['data']:
                    file.write(", ".join(map(str, entry)) + "\n")
            print(f'Saved {component} data in {txt_file_path}')

        # Initialize dictionary to hold per-country data
        country_data = {country: {'wf_ids': {'capacity': 0, 'cost': 0},
                                'eh_ids': {'capacity': 0, 'cost': 0},
                                'onss_ids': {'capacity': 0, 'cost': 0},
                                'ec1_ids': {'capacity': 0, 'cost': 0},
                                'ec2_ids': {'capacity': 0, 'cost': 0},
                                'ec3_ids': {'capacity': 0, 'cost': 0},
                                'onc_ids': {'capacity': 0, 'cost': 0},
                                'overall': {'capacity': 0, 'cost': 0}}
                        for country in int_to_iso_mp.values()}

        # Aggregate data per country for each component
        for component, data in selected_components.items():
            for entry in data['data']:
                country = entry['iso']
                country_data[country][component]['capacity'] += entry['capacity']
                country_data[country][component]['cost'] += entry['cost']
                country_data[country]['overall']['capacity'] += entry['capacity']
                country_data[country]['overall']['cost'] += entry['cost']

        # Save the aggregated data per country
        for country, data in country_data.items():
            country_txt_file_path = os.path.join(results_dir, f'r_{stg}_{tpe}_{crb}_country_{country}_{year}.txt')
            with open(country_txt_file_path, 'w') as file:
                file.write("Component, Total Capacity, Total Cost\n")
                for component, values in data.items():
                    file.write(f"{component}, {rnd_f(values['capacity'])}, {rnd_f(values['cost'])}\n")
            print(f'Saved total capacity and cost for {country} in {country_txt_file_path}')

        # Calculate overall totals
        overall_totals = {'wf_ids': {'capacity': 0, 'cost': 0},
                        'eh_ids': {'capacity': 0, 'cost': 0},
                        'onss_ids': {'capacity': 0, 'cost': 0},
                        'ec1_ids': {'capacity': 0, 'cost': 0},
                        'ec2_ids': {'capacity': 0, 'cost': 0},
                        'ec3_ids': {'capacity': 0, 'cost': 0},
                        'onc_ids': {'capacity': 0, 'cost': 0},
                        'overall': {'capacity': 0, 'cost': 0}}

        for component, data in selected_components.items():
            for entry in data['data']:
                overall_totals[component]['capacity'] += entry['capacity']
                overall_totals[component]['cost'] += entry['cost']
            overall_totals['overall']['capacity'] += overall_totals[component]['capacity']
            overall_totals['overall']['cost'] += overall_totals[component]['cost']

        # Save the overall totals in the c_total file
        total_txt_file_path = os.path.join(results_dir, f'r_{stg}_{tpe}_{crb}_global_{year}.txt')
        with open(total_txt_file_path, 'w') as file:
            file.write("Component, Total Capacity, Total Cost\n")
            for component, values in overall_totals.items():
                file.write(f"{component}, {rnd_f(values['capacity'])}, {rnd_f(values['cost'])}\n")
        print(f'Saved overall total capacities and cost in {total_txt_file_path}')

    def enforce_increase_variables(model, prev_capacity):
        """
        Ensure that the capacities of onshore substations (onss) and onshore cables (onc) 
        only increase and not decrease between stages by adding constraints.
        """
        # Add constraints to ensure onss capacities do not decrease if above the zero threshold
        for onss in model.viable_onss_ids:
            prev_cap = prev_capacity['onss_ids'].get(onss, 0)
            if prev_cap > zero_th:
                model.onss_cap_var[onss].setlb(prev_cap)
        
        # Add constraints to ensure onc capacities do not decrease if above the zero threshold
        for onss1, onss2 in model.viable_onc_ids:
            prev_cap = prev_capacity['onc_ids'].get((onss1, onss2), 0)
            if prev_cap > zero_th:
                model.onc_cap_var[onss1, onss2].setlb(prev_cap)

    def update_and_fix_variables(model):
        """
        Fix decision variables if their values are above 0.1.
        """
        for var in [model.wf_cap_var, model.eh_cap_var, model.ec1_cap_var, model.ec2_cap_var, model.ec3_cap_var]:
            for index in var:
                if var[index].value > zero_th:
                    var[index].fix(round(var[index].value))
    
    def solve_single_stage(model, workspace_folder):
        # Use country_cf_2050 for the single stage optimization
        country_cf_param = model.country_cf_sf
        year_param = value(model.first_year_sf)
        
        if year_param == 2030:
            wf_cost_param = model.wf_cost_1
        if year_param == 2040:     
            wf_cost_param = model.wf_cost_2
        if year_param == 2050:
            wf_cost_param = model.wf_cost_3     
        
        model.country_cf.store_values(country_cf_param)  # Update country_cf for the single stage optimization for 2050
        model.first_year.store_values(year_param)  # Update first_year
        model.wf_cost.store_values(wf_cost_param)
        
        # Initialize previous capacities dictionary with zero capacities (needed for save_results function)
        prev_capacity = {
            'onss_ids': {onss: 0 for onss in model.viable_onss_ids},
            'onc_ids': {(onss1, onss2): 0 for onss1, onss2 in model.viable_onc_ids}
        }

        # Path to the log file
        logfile_path = os.path.join(workspace_folder, "results", "combined", f"c_solverlog_{year_param}.txt")
        
        # Solve the model, passing the parameter file as an option
        results = solver.solve(model, tee=True, logfile=logfile_path, options=solver_options)
            
        # Detailed checking of solver results
        if results.solver.status == SolverStatus.ok:
            if results.solver.termination_condition == TerminationCondition.optimal:
                print(f"Solver found an optimal solution for {year_param}.")
                print(f"Objective value: {rnd_f(model.global_cost_obj.expr())}")
            else:
                print(f"Solver stopped due to limit for {year_param}.")
                print(f"Objective value: {rnd_f(model.global_cost_obj.expr())}")
            save_results(model, workspace_folder, year_param, prev_capacity)
        elif results.solver.status == SolverStatus.error:
            print(f"Solver error occurred for {year_param}. Check solver log for more details.")
        elif results.solver.status == SolverStatus.warning:
            print(f"Solver finished with warnings for {year_param}. Results may not be reliable.")
        else:
            print(f"Unexpected solver status for {year_param}: {results.solver.status}. Check solver log for details.")

        print(f"Solver log for {year_param} saved to {os.path.join(workspace_folder, 'results', 'combined', 'c_solverlog_2050.txt')}")

    def solve_multi_stage(model, workspace_folder):
        # Define the country_cf parameters for each stage
        country_cf_params = {
            first_year_mf_1: model.country_cf_mf_1,
            first_year_mf_2: model.country_cf_mf_2,
            first_year_mf_3: model.country_cf_mf_3
        }
        
        # Define the wf_cost parameters for each stage
        wf_cost_params = {
            first_year_mf_1: model.wf_cost_1,
            first_year_mf_2: model.wf_cost_2,
            first_year_mf_3: model.wf_cost_3
        }
        
        # Initialize previous capacities dictionary
        prev_capacity = {
            'onss_ids': {onss: 0 for onss in model.viable_onss_ids},
            'onc_ids': {(onss1, onss2): 0 for onss1, onss2 in model.viable_onc_ids}
        }
        
        for year in [first_year_mf_1, first_year_mf_2, first_year_mf_3]:
            print(f"Solving for {year}...")
            
            model.country_cf.store_values(country_cf_params[year])  # Update country_cf for the multistage optimization
            model.first_year.store_values(year)  # Update first_year
            model.wf_cost.store_values(wf_cost_params[year])
                        
            # Path to the log file
            logfile_path = os.path.join(workspace_folder, "results", "combined", f"c_solverlog_{year}.txt")
            
            # Solve the model, passing the parameter file as an option
            results = solver.solve(model, tee=True, logfile=logfile_path, options=solver_options)
            
            # Detailed checking of solver results
            if results.solver.status == SolverStatus.ok:
                if results.solver.termination_condition == TerminationCondition.optimal:
                    print(f"Solver found an optimal solution for {year}.")
                    print(f"Objective value: {rnd_f(model.global_cost_obj.expr())}")
                else:
                    print(f"Solver stopped due to limit for {year}.")
                    print(f"Objective value: {rnd_f(model.global_cost_obj.expr())}")
                save_results(model, workspace_folder, year, prev_capacity)
                # Update prev_capacity with current capacities for the next stage
                prev_capacity['onss_ids'] = {onss: rnd_f(model.onss_cap_var[onss]) for onss in model.viable_onss_ids}
                prev_capacity['onc_ids'] = {(onss1, onss2): rnd_f(model.onc_cap_var[onss1, onss2]) for onss1, onss2 in model.viable_onc_ids}
                # Enforce capacity increase constraints
                enforce_increase_variables(model, prev_capacity)
                # Fix variables
                if year < first_year_mf_3:
                    update_and_fix_variables(model)
            elif results.solver.status == SolverStatus.error:
                print(f"Solver error occurred for {year}. Check solver log for more details.")
            elif results.solver.status == SolverStatus.warning:
                print(f"Solver finished with warnings for {year}. Results may not be reliable.")
            else:
                print(f"Unexpected solver status for {year}: {results.solver.status}. Check solver log for details.")

            print(f"Solver log for {year} saved to {os.path.join(workspace_folder, 'results', 'combined', f'c_solverlog_{year}.txt')}")

    # Decide whether to run single stage or multistage optimization
    if multi_stage == 0:
        print(f"Performing single stage optimization for {first_year_sf}...")
        solve_single_stage(model, workspace_folder)
    elif multi_stage == 1:
        print(f"Performing multistage optimization for {first_year_mf_1}, {first_year_mf_2}, and {first_year_mf_3}...")
        solve_multi_stage(model, workspace_folder)

    return None

# Define the main block
if __name__ == "__main__":
    # Specify the workspace folder
    workspace_folder = "C:\\Users\\cflde\\Documents\\Graduation Project\\ArcGIS Pro\\BalticSea\\Results\\datasets"

    # Call the optimization model function
    opt_model(workspace_folder)