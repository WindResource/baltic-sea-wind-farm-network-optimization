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

from pyomo.environ import *
import numpy as np
import os
from itertools import product

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

from pyomo.environ import Ceiling, minimize

def export_cable_costs(distance, required_active_power, polarity="AC"):
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

    required_active_power *= 1e6  # (MW > W)
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

    # Filter data based on desired voltage
    cable_data = [cable for cable in cable_data if cable[0] >= required_voltage]

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
    scaling_factors = [1e3, 1e-6, 1e-6, 1e-12, 1, 1, 1]

    # Apply scaling to each column in cable_data
    scaled_cable_data = []
    for cable in cable_data:
        scaled_cable = [cable[i] * scaling_factors[i] for i in range(len(cable))]
        scaled_cable_data.append(scaled_cable)

    power_factor = 0.90
    cable_count = []  # To store the number of cables and corresponding cable data

    for cable in scaled_cable_data:
        voltage, resistance, capacitance, ampacity = cable[0], cable[2], cable[3], cable[4]
        nominal_power_per_cable = voltage * ampacity
        if polarity == "AC":  # Three phase AC
            ac_apparent_power = required_active_power / power_factor
            # Determine number of cables needed based on required total apparent power
            n_cables = Ceiling(ac_apparent_power / nominal_power_per_cable)

            current = ac_apparent_power / voltage

        else:  # Assuming polarity == "DC"
            # Determine number of cables needed based on required power
            n_cables = Ceiling(required_active_power / nominal_power_per_cable)

            current = required_active_power / voltage

        resistive_losses = current ** 2 * resistance * length / n_cables
        power_eff = (resistive_losses / required_active_power)

        # Add the calculated data to the list
        cable_count.append((cable, n_cables))

    # Calculate the total costs for each cable combination
    equip_costs_array = [cable[5] * length * n_cables for cable, n_cables in cable_count]
    inst_costs_array = [cable[6] * length * n_cables for cable, n_cables in cable_count]

    # Calculate total costs
    total_costs_array = [equip + inst for equip, inst in zip(equip_costs_array, inst_costs_array)]

    # Find the cable combination with the minimum total cost
    min_cost_index = total_costs_array.index(min(total_costs_array))

    # Initialize costs
    equip_costs = equip_costs_array[min_cost_index]
    inst_costs = inst_costs_array[min_cost_index]
    ope_costs_yearly = 0.2 * 1e-2 * equip_costs
    deco_costs = 0.5 * inst_costs

    # Calculate present value
    total_costs = present_value(equip_costs, inst_costs, ope_costs_yearly, deco_costs)

    return total_costs

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
            r_hub = sqrt(area_island/np.pi)
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
            r_hub = sqrt(area_island/np.pi)
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
            
        return total_costs

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

def find_viable_iac(wf_lon, wf_lat, oss_lon, oss_lat):
    """
    Find all pairs of offshore wind farms and offshore substations within 150km.
    
    Parameters are dictionaries keyed by substation IDs with longitude and latitude values.
    """
    connections = []
    for wf_key, oss_key in product(wf_lon.keys(), oss_lon.keys()):
        distance = haversine(wf_lon[wf_key], wf_lat[wf_key], oss_lon[oss_key], oss_lat[oss_key])
        if distance <= 150:
            connections.append((wf_key, oss_key))
    return connections

def find_viable_ec(oss_lon, oss_lat, onss_lon, onss_lat):
    """
    Find all pairs of offshore and onshore substations within 300km.
    
    Parameters are dictionaries keyed by substation IDs with longitude and latitude values.
    """
    connections = []
    for oss_key, onss_key in product(oss_lon.keys(), onss_lon.keys()):
        distance = haversine(oss_lon[oss_key], oss_lat[oss_key], onss_lon[onss_key], onss_lat[onss_key])
        if distance <= 300:
            connections.append((oss_key, onss_key))
    return connections

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
    
    # Set the SCIP binary directory
    scip_dir = "C:\\Program Files\\SCIPOptSuite 9.0.0"
    os.environ["SCIPOPTDIR"] = scip_dir

    # Create a Pyomo model
    model = ConcreteModel()

    """
    Process data
    """
    print("Processing data...")
    
    # Load datasets
    wf_dataset_file = os.path.join(workspace_folder, 'wf_data.npy')
    oss_dataset_file = os.path.join(workspace_folder, 'oss_data.npy')
    onss_dataset_file = os.path.join(workspace_folder, 'onss_data.npy')
    
    wf_dataset = np.load(wf_dataset_file, allow_pickle=True)
    oss_dataset = np.load(oss_dataset_file, allow_pickle=True)
    onss_dataset = np.load(onss_dataset_file, allow_pickle=True)

    # Keys data
    wf_keys = [data[0] for data in wf_dataset]
    oss_keys = [data[0] for data in oss_dataset]
    onss_keys = [data[0] for data in onss_dataset]

    # Wind farm data
    wf_iso, wf_lon, wf_lat, wf_cap, wf_costs = {}, {}, {}, {}, {}

    for data in wf_dataset:
        key = data[0]
        wf_iso[key] = data[1]
        wf_lon[key] = data[2]
        wf_lat[key] = data[3]
        wf_cap[key] = data[5]
        wf_costs[key] = data[6]

    # Offshore substation data
    oss_iso, oss_lon, oss_lat, oss_wdepth, oss_icover, oss_pdist = {}, {}, {}, {}, {}, {}

    for data in oss_dataset:
        key = data[0]
        oss_iso[key] = data[1]
        oss_lon[key] = data[2]
        oss_lat[key] = data[3]
        oss_wdepth[key] = data[4]
        oss_icover[key] = data[5]
        oss_pdist[key] = data[6]
    
    # Onshore substation data
    onss_iso, onss_lon, onss_lat = {}, {}, {}

    for data in onss_dataset:
        key = data[0]
        onss_iso[key] = data[1]
        onss_lon[key] = data[2]
        onss_lat[key] = data[3]

    
    """
    Define model parameters
    """
    print("Defining model parameters...")
    
    # Wind farm parameters
    model.wf_iso = Param(wf_keys, initialize=wf_iso, within=Any)
    model.wf_lon = Param(wf_keys, initialize=wf_lon, within=NonNegativeReals)
    model.wf_lat = Param(wf_keys, initialize=wf_lat, within=NonNegativeReals)
    model.wf_cap = Param(wf_keys, initialize=wf_cap, within=NonNegativeIntegers)

    # Offshore substation parameters
    model.oss_iso = Param(oss_keys, initialize=oss_iso, within=Any)
    model.oss_lon = Param(oss_keys, initialize=oss_lon, within=NonNegativeReals)
    model.oss_lat = Param(oss_keys, initialize=oss_lat, within=NonNegativeReals)
    model.oss_wdepth = Param(oss_keys, initialize=oss_wdepth, within=NonNegativeIntegers)
    model.oss_icover = Param(oss_keys, initialize=oss_icover, within=Binary)
    model.oss_pdist = Param(oss_keys, initialize=oss_pdist, within=NonNegativeIntegers)

    # Onshore substation parameters
    model.onss_iso = Param(onss_keys, initialize=onss_iso, within=Any)
    model.onss_lon = Param(onss_keys, initialize=onss_lon, within=NonNegativeReals)
    model.onss_lat = Param(onss_keys, initialize=onss_lat, within=NonNegativeReals)

    """
    Define decision variables
    """
    print("Defining decision parameters...")
    
    # Calculate viable connections
    viable_iac = find_viable_iac(wf_lon, wf_lat, oss_lon, oss_lat)
    viable_ec = find_viable_ec(oss_lon, oss_lat, onss_lon, onss_lat)

    # You can then integrate these connections into your model as needed
    # For example, as a Pyomo Set
    model.viable_iac = Set(initialize= viable_iac, dimen=2)
    model.viable_ec = Set(initialize= viable_ec, dimen=2)
    
    model.select_wf = Var(wf_keys, within=Binary)
    model.select_oss = Var(oss_keys, within=Binary)
    model.select_iac = Var(model.viable_iac, within=Binary)
    model.select_ec = Var(model.viable_ec, within=Binary)


    """
    Define Expressions
    """
    print("Defining expressions...")
    
    
    # Distance expressions
    def iac_dist_rule(model, wf, oss):
        return haversine(model.wf_lon[wf], model.wf_lat[wf], model.oss_lon[oss], model.oss_lat[oss])
    model.iac_dist = Expression(wf_keys, oss_keys, rule=iac_dist_rule)
    
    def ec_dist_rule(model, oss, onss):
        return haversine(model.oss_lon[oss], model.oss_lat[oss], model.onss_lon[onss], model.onss_lat[onss])
    model.ec_dist = Expression(oss_keys, onss_keys, rule=ec_dist_rule)
    
    # Capacity expressions
    def oss_capacity_rule(model, oss):
        return sum(model.wf_cap[wf] * model.select_iac[wf, oss] for wf, oss_key in model.viable_iac if oss_key == oss)
    model.oss_cap = Expression(oss_keys, rule=oss_capacity_rule)

    def ec_capacity_rule(model, oss, onss):
        return sum(model.oss_cap[oss] * model.select_ec[oss_key, onss] for oss_key, onss_key in model.viable_ec if oss_key == oss and onss_key == onss)
    model.ec_cap = Expression(model.viable_ec, rule=ec_capacity_rule)

    # Cost expressions
    def oss_cost_rule(model, oss):
        return offshore_substation_costs(model.oss_wdepth[oss], model.oss_icover[oss], model.oss_pdist[oss], model.oss_cap[oss], "AC")
    model.oss_costs = Expression(oss_keys, rule=oss_cost_rule)

    def ec_cost_rule(model, oss, onss):
        return export_cable_costs(model.ec_dist[oss, onss], model.ec_cap[oss, onss], polarity="AC")
    model.ec_costs = Expression(model.viable_ec, rule=ec_cost_rule)
    
    
    """
    Define Objective function
    """
    print("Defining objective function")

    def total_cost_rule(model):
        # Summing wind farm costs
        wf_total_cost = sum(wf_costs[wf] * model.select_wf[wf] for wf in wf_keys)
        # Summing offshore substation costs
        oss_total_cost = sum(model.oss_costs[oss] * model.select_oss[oss] for oss in oss_keys)
        # Summing inter array cable costs for viable connections
        iac_total_cost = sum(model.ec_costs[wf, oss] * model.select_iac[wf, oss] for (wf, oss) in model.viable_ec)
        # Summing export cable costs for viable connections
        ec_total_cost = sum(model.ec_costs[oss, onss] * model.select_ec[oss, onss] for (oss, onss) in model.viable_ec)
        # The objective is to minimize the total cost
        return wf_total_cost + oss_total_cost + iac_total_cost + ec_total_cost

    # Set the objective in the model
    model.total_cost = Objective(rule=total_cost_rule, sense=minimize)
    
    
    """
    Define Constraints
    """
    print("Defining constraints")

    # Minimum total capacity constraint
    # Constraint 1:
    def min_total_wf_capacity_rule(model):
        min_required_capacity = 0.5 * sum(wf_cap.values())
        return sum(model.wf_cap[wf] * model.select_wf[wf] for wf in wf_keys) >= min_required_capacity
    model.min_total_wf_capacity = Constraint(rule=min_total_wf_capacity_rule)

    """
    Fully Updated Define Constraints for Radial Connection System
    """
    print("Fully updating constraints for radial system...")

    # Constraint: Every selected wind farm is connected to exactly one offshore substation via exactly one inter-array cable
    def wind_farm_to_oss_rule(model, wf):
        return sum(model.select_iac[wf, oss] for oss in oss_keys if (wf, oss) in model.viable_iac) == model.select_wf[wf]
    model.wind_farm_to_oss_con = Constraint(wf_keys, rule=wind_farm_to_oss_rule)

    # Constraint: Inter-array cables can only connect selected wind farms to selected offshore substations
    def iac_wf_oss_connection_rule(model, wf, oss):
        return model.select_iac[wf, oss] <= model.select_wf[wf] and model.select_iac[wf, oss] <= model.select_oss[oss]
    model.iac_wf_oss_connection_con = Constraint(model.viable_iac, rule=iac_wf_oss_connection_rule)

    # Constraint: Every selected offshore substation is connected to exactly one onshore substation via exactly one export cable
    def oss_to_onss_rule(model, oss):
        return sum(model.select_ec[oss, onss] for onss in onss_keys if (oss, onss) in model.viable_ec) == model.select_oss[oss]
    model.oss_to_onss_con = Constraint(oss_keys, rule=oss_to_onss_rule)

    # Constraint: Export cables can only connect selected offshore substations to selected onshore substations
    def ec_oss_onss_connection_rule(model, oss, onss):
        return model.select_ec[oss, onss] <= model.select_oss[oss] and model.select_ec[oss, onss] <= model.onss_iso[onss]
    model.ec_oss_onss_connection_con = Constraint(model.viable_ec, rule=ec_oss_onss_connection_rule)

    # New Constraint: Every selected onshore substation must connect to exactly one offshore substation via exactly one export cable
    def onss_to_oss_rule(model, onss):
        return sum(model.select_ec[oss, onss] for oss in oss_keys if (oss, onss) in model.viable_ec) == model.onss_iso[onss]
    model.onss_to_oss_con = Constraint(onss_keys, rule=onss_to_oss_rule)

    
    
    # Capacity constraints
    # Constraint 2.1: Capacity of inter-array cable equals the capacity of wind farm
    def iac_capacity_rule(model, wf, oss):
        return model.select_iac[wf, oss] * model.wf_cap[wf] == model.select_wf[wf] * model.wf_cap[wf]
    model.iac_capacity = Constraint(wf_keys, oss_keys, rule=iac_capacity_rule)

    # Constraint 2.2: Capacity of offshore substation equals the capacity of inter-array cable
    def oss_capacity_rule(model, oss):
        return sum(model.select_iac[wf, oss] * model.wf_cap[wf] for wf in wf_keys if (wf, oss) in model.viable_iac) \
            == model.select_oss[oss] * model.oss_cap[oss]
    model.oss_capacity = Constraint(oss_keys, rule=oss_capacity_rule)

    # Constraint 2.3: Capacity of export cable equals the capacity of offshore substation
    def ec_capacity_rule(model, oss, onss):
        return sum(model.select_ec[oss, onss] * model.oss_cap[oss] for (oss, onss) in model.viable_ec if oss == oss) \
            == model.select_oss[oss] * model.oss_cap[oss]
    model.ec_capacity = Constraint(oss_keys, rule=ec_capacity_rule)


    # Country code constraints
    # Constraint 3.1: ISO of the wind farm equals the ISO of the connected offshore substation
    def wf_oss_iso_matching_rule(model, wf, oss):
        if (wf, oss) in model.viable_iac:
            return model.select_iac[wf, oss] * (model.wf_iso[wf] == model.oss_iso[oss]) == model.select_iac[wf, oss]
        else:
            return Constraint.Skip
    model.wf_oss_iso_matching = Constraint(wf_keys, oss_keys, rule=wf_oss_iso_matching_rule)

    # Constraint 3.2: ISO of the offshore substation equals the ISO of the connected onshore substation
    def oss_onss_iso_matching_rule(model, oss, onss):
        if (oss, onss) in model.viable_ec:
            return model.select_ec[oss, onss] * (model.oss_iso[oss] == model.onss_iso[onss]) == model.select_ec[oss, onss]
        else:
            return Constraint.Skip
    model.oss_onss_iso_matching = Constraint(oss_keys, onss_keys, rule=oss_onss_iso_matching_rule)


    """
    Solve the model
    """
    print("Solving model...")
    
    # Create a solver object and specify PySCIPOpt as the solver
    solver = SolverFactory('pyscipopt')

    # Solve the model
    results = solver.solve(model)
    
    """
    Print the solution
    """
    print("Succes! Displaying the solution...")
    
    # Check solver status and retrieve solution
    if results.solver.termination_condition == TerminationCondition.optimal:
        # Model was solved to optimality
        model.display()
    elif results.solver.termination_condition == TerminationCondition.infeasible:
        # Model is infeasible
        print("Model is infeasible.")
    else:
        # Other termination conditions (e.g., solver error)
        print("Solver terminated with status:", results.solver.termination_condition)

    return model

# Define the main block
if __name__ == "__main__":
    # Specify the workspace folder
    workspace_folder = "C:\\Users\\cflde\\Documents\\Graduation Project\\ArcGIS Pro\\BalticSea\\Results\\datasets"

    # Call the optimization model function
    opt_model(workspace_folder)





