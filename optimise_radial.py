"""
Wind Farm Optimization Model Setup

This script sets up and solves an optimization problem for selecting wind farms, offshore substations,
and their connections to minimize total costs while adhering to operational constraints. It considers
the costs of selecting wind farms and substations, plus the costs associated with connecting these
entities based on distances. It ensures configurations meet specified requirements, including
connection feasibility, capacity limitations, and distance constraints.

- generate_connections_and_costs(wind_farms, offshore_ss, onshore_ss, cost_per_distance_unit): Generates
    pwfible connections between entities and calculates associated costs based on distances.
    Parameters:
    - wind_farms (dict): Dictionary of wind farms with 'coordinates'.
    - offshore_ss (dict): Dictionary of offshore substations with 'coordinates'.
    - onshore_ss (dict): Dictionary of onshore substations with 'coordinates'.
    - cost_per_distance_unit (float): Cost factor per unit of distance (e.g., per kilometer).
    Returns:
    - tuple of (dict, dict): Two dictionaries, one for connection costs and one for distances, 
    with tuple ids representing connections (e.g., ('WF1', 'OSS1')).

- add_constraints(model, wind_farms, offshore_ss, onshore_ss, connections_costs, distances,
        min_total_capacity, max_wf_wf_dist, max_wf_ss_dist, universal_offshore_ss_max_capacity):
    Adds operational constraints to the optimization model, including capacity and distance limitations.
    Parameters:
    - model (ConcreteModel): The Pyomo model.
    - wind_farms (dict): Dictionary of wind farms.
    - offshore_ss (dict): Dictionary of offshore substations.
    - onshore_ss (dict): Dictionary of onshore substations.
    - connections_costs (dict): Dictionary of connection costs.
    - distances (dict): Dictionary of distances between entities.
    - min_total_capacity (float): Minimum total capacity requirement for selected wind farms.
    - max_wf_wf_dist (float): Maximum allowed distance from wind farms to offshore substations.
    - max_wf_ss_dist (float): Maximum allowed distance from offshore substations to onshore substations.
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

    from pyomo.environ import Ceiling, minimize
    
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

        resistive_lwfes = current ** 2 * resistance * length / n_cables
        power_eff = (resistive_lwfes / required_active_power)

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

def offshore_substation_costs(water_depth, ice_cover, port_distance, wf_capacity, polarity = "AC"):
    """
    Estimate the costs associated with an offshore substation based on various parameters.

    Parameters:
    - water_depth (float): Water depth at the location of the offshore substation.
    - ice_cover (int): Indicator of ice cover presence (1 for presence, 0 for absence).
    - port_distance (float): Distance from the offshore location to the nearest port.
    - wf_capacity (float): Capacity of the offshore substation.
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

    def equip_costs(water_depth, support_structure, ice_cover, wf_capacity, polarity):
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
        equiv_capacity = 0.5 * wf_capacity if polarity == "AC" else wf_capacity

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
        conv_costs = c5 * wf_capacity * int(1e3) + c6 * int(1e6) #* int(1e3)
        
        # Calculate equipment costs
        equip_costs = supp_costs + conv_costs
        
        return supp_costs, conv_costs, equip_costs

    def inst_deco_costs(water_depth, support_structure, port_distance, wf_capacity, polarity, operation):
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
            equiv_capacity = 0.5 * wf_capacity if polarity == "AC" else wf_capacity
            
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
    supp_costs, conv_costs, equip_costs =  equip_costs(water_depth, supp_structure, ice_cover, wf_capacity, polarity)

    # Calculate installation and decommissioning costs
    inst_costs = inst_deco_costs(water_depth, supp_structure, port_distance, wf_capacity, polarity, "inst")
    deco_costs = inst_deco_costs(water_depth, supp_structure, port_distance, wf_capacity, polarity, "deco")

    # Calculate yearly operational costs
    ope_costs_yearly = oper_costs(support_structure, supp_costs, conv_costs)
    
    # Calculate present value of costs    
    wf_costs = present_value(equip_costs, inst_costs, ope_costs_yearly, deco_costs)
    
    return wf_costs

def ec_cost_plh(distance, capacity, polarity):
    """
    Placeholder function to calculate export cable costs.

    Parameters:
    - distance (float): Distance of the export cable.
    - capacity (float): Capacity of the export cable.
    - polarity (str): Polarity of the cost calculation.

    Returns:
    - cost (float): Total cost of the export cable.
    """
    # Example cost calculation
    cost = distance * 2000 + capacity * 500
    
    # Polarity adjustment
    if polarity == "AC":
        cost *= 1.1  # Example adjustment for AC costs
    elif polarity == "DC":
        cost *= 1.2  # Example adjustment for DC costs
    
    return cost

def onss_cost_plh(capacity, threshold):
    """
    Calculate the cost for ONSS expansion above a certain capacity.

    Parameters:
    - capacity (float): The total capacity for which the cost is to be calculated.
    - threshold (float): The capacity threshold specific to the ONSS above which costs are incurred.
    
    Returns:
    - (float) Cost of expanding the ONSS if the capacity exceeds the threshold.
    """
    
    # Calculate the cost function: difference between capacity and threshold multiplied by the cost factor
    cost_function = (capacity - threshold) * 1000
    
    # Ensure that the cost is only applied above the capacity threshold and is zero at or below the threshold
    cost_function_max = (cost_function + abs(cost_function)) / 2
    
    return cost_function_max

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

def find_viable_ec(wf_lon, wf_lat, onss_lon, onss_lat, wf_iso, onss_iso):
    """
    Find all pairs of offshore and onshore substations within 300km,
    ensuring that they belong to the same country based on their ISO codes.
    
    Parameters are dictionaries indexed by substation IDs with longitude, latitude, and ISO codes.
    """
    connections = []
    for wf_id, onss_id in product(wf_lon.keys(), onss_lon.keys()):
        # Calculate the distance first to see if they are within the viable range
        distance = haversine(wf_lon[wf_id], wf_lat[wf_id], onss_lon[onss_id], onss_lat[onss_id])
        if distance <= 300 and wf_iso[wf_id] == onss_iso[onss_id]:  # Check if the distance is within 300 km and check if the ISO codes match
            connections.append((int(wf_id), int(onss_id)))

    return connections

def get_viable_entities(viable_ec):
    """
    Identifies unique wind farm, offshore substation, and onshore substation IDs
    based on their involvement in viable inter-array and export cable connections.

    Parameters:
    - viable_ec (list of tuples): List of tuples, each representing a viable connection
        between a wind farm and an offshore substation (wf_id, wf_id).
    - viable_ec (list of tuples): List of tuples, each representing a viable connection
        between an offshore substation and an onshore substation (wf_id, onss_id).

    Returns:
    - viable_wf (set): Set of wind farm IDs with at least one viable connection to an offshore substation.
    - viable_wf (set): Set of offshore substation IDs involved in at least one viable connection
        either to a wind farm or an onshore substation.
    - viable_onss (set): Set of onshore substation IDs with at least one viable connection to an offshore substation.
    """
    viable_wf = set()
    viable_onss = set()

    # Extract unique offshore and onshore substation IDs from export cable connections
    for wf_id, onss_id in viable_ec:
        viable_wf.add(int(wf_id))
        viable_onss.add(int(onss_id))

    return viable_wf, viable_onss

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
    onss_dataset_file = os.path.join(workspace_folder, 'onss_data.npy')
    
    wf_dataset = np.load(wf_dataset_file, allow_pickle=True)
    onss_dataset = np.load(onss_dataset_file, allow_pickle=True)

    # Component identifiers
    wf_ids = [int(data[0]) for data in wf_dataset]
    onss_ids = [int(data[0]) for data in onss_dataset]

    # Wind farm data
    wf_iso, wf_lon, wf_lat, wf_cap, wf_cost = {}, {}, {}, {}, {}

    for data in wf_dataset:
        id = int(data[0])
        wf_iso[id] = iso_to_int_mp[data[1]]
        wf_lon[id] = data[2]
        wf_lat[id] = data[3]
        wf_cap[id] = data[5]
        wf_cost[id] = data[6]
    
    # Onshore substation data
    onss_iso, onss_lon, onss_lat, onss_thold = {}, {}, {}, {}

    for data in onss_dataset:
        id = int(data[0])
        onss_iso[id] = iso_to_int_mp[data[1]]
        onss_lon[id] = data[2]
        onss_lat[id] = data[3]
        onss_thold[id] = data[4]

    """
    Define model parameters
    """
    print("Defining model parameters...")
    
    # Identifiers model components
    model.wf_ids = Set(initialize=wf_ids)
    model.onss_ids = Set(initialize=onss_ids)
    
    # Wind farm model parameters
    model.wf_iso = Param(model.wf_ids, initialize=wf_iso, within=NonNegativeIntegers)
    model.wf_lon = Param(model.wf_ids, initialize=wf_lon, within=NonNegativeReals)
    model.wf_lat = Param(model.wf_ids, initialize=wf_lat, within=NonNegativeReals)
    model.wf_cap = Param(model.wf_ids, initialize=wf_cap, within=NonNegativeIntegers)
    model.wf_cost = Param(model.wf_ids, initialize=wf_cost, within=NonNegativeIntegers)

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
    viable_ec = find_viable_ec(wf_lon, wf_lat, onss_lon, onss_lat, wf_iso, onss_iso)

    model.viable_ec_ids = Set(initialize= viable_ec, dimen=2)
    
    # Calculate viable entities based on the viable connections
    model.viable_wf_ids, model.viable_onss_ids = get_viable_entities(viable_ec)
    
    # Initialize variables to one
    model.select_wf_var = Var(model.viable_wf_ids, within=Binary)
    model.select_onss_var = Var(model.viable_onss_ids, within=Binary)
    model.select_ec_var = Var(model.viable_ec_ids, within=Binary)

    # Define a dictionary containing variable names and their respective lengths
    print_variables = {
        "select_wf": model.select_wf_var,
        "select_onss": model.select_onss_var,
        "select_ec": model.select_ec_var
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
    Define distance and capacity expressions for Export Cables (EC)
    """
    def ec_distance_rule(model, wf, onss):
        return haversine(model.wf_lon[wf], model.wf_lat[wf], model.onss_lon[onss], model.onss_lat[onss])
    model.ec_dist_exp = Expression(model.viable_ec_ids, rule=ec_distance_rule)

    def ec_capacity_rule(model, wf, onss):
        return model.wf_cap[wf]
    model.ec_cap_exp = Expression(model.viable_ec_ids, rule=ec_capacity_rule)

    def ec_cost_rule(model, wf, onss):
        return ec_cost_plh(model.ec_dist_exp[wf, onss], model.ec_cap_exp[wf, onss], polarity="AC")
    model.ec_cost_exp = Expression(model.viable_ec_ids, rule=ec_cost_rule)

    """
    Define expressions for Onshore Substations (ONSS)
    """
    def onss_capacity_rule(model, onss):
        return sum(model.wf_cap[wf] for wf in model.viable_wf_ids if (wf, onss) in model.viable_ec_ids)
    model.onss_cap = Expression(model.viable_onss_ids, rule=onss_capacity_rule)

    def onss_cost_rule(model, onss):
        return onss_cost_plh(model.onss_cap[onss], model.onss_thold[onss])
    model.onss_cost_exp = Expression(model.viable_onss_ids, rule=onss_cost_rule)

    """
    Define Objective function
    """
    print("Defining objective function...")

    def global_cost_rule(model):
        """
        Calculate the total cost of the energy system. This includes the costs of selecting
        and connecting wind farms, offshore substations, and onshore substations. The objective is to minimize this total cost.

        The total cost is computed by summing:
        - The costs of selected wind farms.
        - The operational costs of selected offshore substations.
        - The costs associated with inter-array cables connecting wind farms to offshore substations.
        - The costs associated with export cables connecting offshore substations to onshore substations.

        Parameters:
        - model: The Pyomo model object containing all necessary decision variables and parameters.

        Returns:
        - The computed total cost of the network configuration, which the optimization process seeks to minimize.
        """
        wf_total_cost = sum(model.wf_cost[wf] * model.select_wf_var[wf] for wf in model.viable_wf_ids)
        onss_total_costs = sum(model.onss_cost_exp[onss] * model.select_onss_var[onss] for onss in model.viable_onss_ids)
        ec_total_cost = sum(model.ec_cost_exp[wf, onss] * model.select_ec_var[wf, onss] for (wf, onss) in model.viable_ec_ids)
        
        return wf_total_cost + ec_total_cost + onss_total_costs

    # Set the objective in the model
    model.global_cost_obj = Objective(rule=global_cost_rule, sense=minimize)

    """
    Define Constraints
    """
    print("Defining capacity constraints...")

    def min_total_wf_capacity_rule(model):
        """
        Enforce that the sum of the capacities of all selected wind farms meets at least a specified minimum fraction 
        of the total potential capacity of all wind farms considered.
        """
        min_required_capacity = 1 * sum(model.wf_cap[wf] for wf in model.viable_wf_ids)
        return sum(model.wf_cap[wf] * model.select_wf_var[wf] for wf in model.viable_wf_ids) >= min_required_capacity
    model.min_total_wf_capacity_con = Constraint(rule=min_total_wf_capacity_rule)

    print("Defining connectivity constraints...")

    def ec_connect_rule(model, wf):
        """Ensure that if a wind farm is connected, it must connect to exactly one onshore substation."""
        connect_to_onss = sum(model.select_ec_var[wf, onss] for onss in model.onss_ids if (wf, onss) in model.viable_ec_ids)
        return connect_to_onss == model.select_wf_var[wf]
    model.wf_onss_connection_activation_con = Constraint(model.viable_wf_ids, rule=ec_connect_rule)

    def onss_select_rule(model, onss):
        """
        Ensure that if any offshore substation is connected to an onshore substation,
        then the onshore substation is also selected.
        """
        M = len(model.viable_wf_ids)  # Assuming maximum number of viable offshore substations
        connect_from_wf = sum(model.select_ec_var[wf, onss] for wf in model.viable_wf_ids if (wf, onss) in model.viable_ec_ids)
        return model.select_onss_var[onss] * M >= connect_from_wf
    model.onss_select_con = Constraint(model.viable_onss_ids, rule=onss_select_rule)

    """
    Solve the model
    """
    print("Solving model...")
    
    def configure_scip_solver():
        """
        Configure SCIP solver options to optimize performance for NLP problems with many binary variables.

        Returns:
        - A dictionary with configured solver options suitable for SCIP when solving NLP problems with binary variables.
        """
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
            'separating/aggressive': 1,   # Enable aggressive separation
            'conflict/enable': 1,         # Activate conflict analysis
            'heuristics/rens/freq': 10,      # Frequency of RENS heuristic
            'heuristics/diving/freq': 10,    # Frequency of diving heuristic
            'propagating/maxroundsroot': 15, # Propagation rounds at root node
            'limits/nodes': 1e5,             # Maximum nodes in search tree
            'limits/totalnodes': 1e5,         # Total node limit acrwf threads
            'emphasis/feasibility': 1,         # Emphasize feasibility
            'emphasis/memory': 1,           # Emphasize memory
            'separating/maxrounds': 10,  # Limit cut rounds at non-root nodes
            'heuristics/feaspump/freq': 10  # Frequency of feasibility pump heuristic
        }

        return solver_options

    def save_results(model, workspace_folder):
        """
        Save the IDs of selected components of the optimization model along with all their corresponding parameters,
        including directly retrieved capacity and cost from the model expressions, into both .npy and .txt files as structured arrays.
        Headers are included in the .txt files for clarity.

        Parameters:
        - model: The optimized Pyomo model.
        - workspace_folder: The path to the directory where results will be saved.
        """
        def expr_f(e):
            return round(e.expr())
        
        selected_components = {
            'wf_ids': {
                'data': np.array([(wf, model.wf_lon[wf], model.wf_lat[wf], model.wf_cap[wf], model.wf_cost[wf]) 
                                for wf in model.viable_wf_ids if model.select_wf_var[wf].value == 1], 
                                dtype=[('id', int), ('lon', float), ('lat', float), ('capacity', int), ('cost', int)]),
                'headers': "ID, Longitude, Latitude, Capacity, Cost"
            },
            'onss_ids': {
                'data': np.array([(onss, model.onss_lon[onss], model.onss_lat[onss], expr_f(model.onss_cap[onss]), expr_f(model.onss_cost_exp[onss])) 
                                for onss in model.viable_onss_ids if model.select_onss_var[onss].value == 1], 
                                dtype=[('id', int), ('lon', float), ('lat', float), ('capacity', int), ('cost', int)]),
                'headers': "ID, Longitude, Latitude, Capacity, Cost"
            },
            'ec_ids': {
                'data': np.array([(wf, onss, model.wf_lon[wf], model.wf_lat[wf], model.onss_lon[onss], model.onss_lat[onss], expr_f(model.ec_cap_exp[wf, onss]), expr_f(model.ec_cost_exp[wf, onss])) 
                                for wf, onss in model.viable_ec_ids if model.select_ec_var[wf, onss].value == 1], 
                                dtype=[('wf_id', int), ('onss_id', int), ('wf_lon', float), ('wf_lat', float), ('onss_lon', float), ('onss_lat', float), ('capacity', int), ('cost', int)]),
                'headers': "OSS_ID, ONSS_ID, OSSLongitude, OSSLatitude, ONSSLongitude, ONSSLatitude, Capacity, Cost"
            }
        }

        # Ensure the results directory exists
        results_dir = os.path.join(workspace_folder, "results", "radial")
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)

        for key, info in selected_components.items():
            npy_file_path = os.path.join(results_dir, f'{key}_r.npy')
            txt_file_path = os.path.join(results_dir, f'{key}_r.txt')

            # Save as .npy file
            np.save(npy_file_path, info['data'])

            # Save as .txt file for easier viewing
            with open(txt_file_path, 'w') as file:
                file.write(info['headers'] + '\n')  # Write the headers
                for entry in info['data']:
                    file.write(', '.join(map(str, entry)) + '\n')

            print(f'Saved {key} in {npy_file_path} and {txt_file_path}')


        # Ensure the results directory exists
        results_dir = os.path.join(workspace_folder, "results")
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)

        for key, info in selected_components.items():
            npy_file_path = os.path.join(results_dir, f'{key}_r.npy')
            txt_file_path = os.path.join(results_dir, f'{key}_r.txt')

            # Save as .npy file
            np.save(npy_file_path, info['data'])

            # Save as .txt file for easier viewing
            with open(txt_file_path, 'w') as file:
                file.write(info['headers'] + '\n')  # Write the headers
                for entry in info['data']:
                    file.write(', '.join(map(str, entry)) + '\n')

            print(f'Saved {key} in {npy_file_path} and {txt_file_path}')


    # Set the path to the Scip solver executable
    scip_path = "C:\\Program Files\\SCIPOptSuite 9.0.0\\bin\\scip.exe"
    
    # Create a solver object and specify the solver executable path
    solver = SolverFactory('scip')
    solver.options['executable'] = scip_path

    # Define the path for the solver log
    solver_log_path = os.path.join(workspace_folder, "results", "radial", "solver_log_r.txt")
    
    # Retrieve solver options with the configured settings
    solver_options = configure_scip_solver()
    
    # Pass the log path directly to the solver
    results = solver.solve(model, tee=True, logfile=solver_log_path, options=solver_options)
    
    # Detailed checking of solver results
    if results.solver.status == SolverStatus.ok:
        if results.solver.termination_condition == TerminationCondition.optimal:
            print("Solver found an optimal solution.")
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