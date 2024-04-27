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
    with tuple ids representing connections (e.g., ('WF1', 'OSS1')).

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

def oss_cost_plh(wdepth, icover, pdist, capacity, polarity):
    """
    Placeholder function to calculate offshore substation costs.

    Parameters:
    - wdepth (float): Water depth.
    - icover (int): Ice cover (binary: 0 for no ice, 1 for ice).
    - pdist (float): Distance to port.
    - capacity (float): Capacity of the offshore substation.
    - polarity (str): Polarity of the cost calculation.

    Returns:
    - cost (float): Total cost of the offshore substation.
    """
    # Example cost calculation
    cost = wdepth * 1000 + icover * 5000 + pdist * 2000 + capacity * 1000
    
    # Polarity adjustment
    if polarity == "AC":
        cost *= 1.1  # Example adjustment for AC costs
    elif polarity == "DC":
        cost *= 1.2  # Example adjustment for DC costs
    
    return cost

def iac_cost_plh(distance, capacity, polarity):
    """
    Calculate inter-array cable costs.

    Parameters:
    - distance (float): Distance of the inter-array cable.
    - capacity (float): Capacity of the inter-array cable.
    - polarity (str): Polarity of the cost calculation.

    Returns:
    - cost (float): Total cost of the inter-array cable.
    """
    # Example cost calculation
    cost = distance * 1500 + capacity * 400
    
    # Polarity adjustment
    if polarity == "AC":
        cost *= 1.1  # Example adjustment for AC costs
    elif polarity == "DC":
        cost *= 1.2  # Example adjustment for DC costs
    
    return cost

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
    
    Parameters are dictionaries ided by substation IDs with longitude and latitude values.
    """
    connections = []
    for wf_id, oss_id in product(wf_lon.keys(), oss_lon.keys()):
        distance = haversine(wf_lon[wf_id], wf_lat[wf_id], oss_lon[oss_id], oss_lat[oss_id])
        if distance <= 150:
            connections.append((int(wf_id), int(oss_id)))
    return connections

def find_viable_ec(oss_lon, oss_lat, onss_lon, onss_lat):
    """
    Find all pairs of offshore and onshore substations within 300km.
    
    Parameters are dictionaries ided by substation IDs with longitude and latitude values.
    """
    connections = []
    for oss_id, onss_id in product(oss_lon.keys(), onss_lon.keys()):
        distance = haversine(oss_lon[oss_id], oss_lat[oss_id], onss_lon[onss_id], onss_lat[onss_id])
        if distance <= 500:
            connections.append((int(oss_id), int(onss_id)))
            
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
    oss_dataset_file = os.path.join(workspace_folder, 'oss_data.npy')
    onss_dataset_file = os.path.join(workspace_folder, 'onss_data.npy')
    
    wf_dataset = np.load(wf_dataset_file, allow_pickle=True)
    oss_dataset = np.load(oss_dataset_file, allow_pickle=True)
    onss_dataset = np.load(onss_dataset_file, allow_pickle=True)

    # Component identifiers
    wf_ids = [int(data[0]) for data in wf_dataset]
    oss_ids = [int(data[0]) for data in oss_dataset]
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

    # Offshore substation data
    oss_iso, oss_lon, oss_lat, oss_wdepth, oss_icover, oss_pdist = {}, {}, {}, {}, {}, {}

    for data in oss_dataset:
        id = int(data[0])
        oss_iso[id] = iso_to_int_mp[data[1]]
        oss_lon[id] = data[2]
        oss_lat[id] = data[3]
        oss_wdepth[id] = data[4]
        oss_icover[id] = data[5]
        oss_pdist[id] = data[6]
    
    # Onshore substation data
    onss_iso, onss_lon, onss_lat = {}, {}, {}

    for data in onss_dataset:
        id = int(data[0])
        onss_iso[id] = iso_to_int_mp[data[1]]
        onss_lon[id] = data[2]
        onss_lat[id] = data[3]

    """
    Define model parameters
    """
    print("Defining model parameters...")
    
    # Identifiers model components
    model.wf_ids = Set(initialize=wf_ids)
    model.oss_ids = Set(initialize=oss_ids)
    model.onss_ids = Set(initialize=onss_ids)
    
    # Wind farm model parameters
    model.wf_iso = Param(model.wf_ids, initialize=wf_iso, within=NonNegativeIntegers)
    model.wf_lon = Param(model.wf_ids, initialize=wf_lon, within=NonNegativeReals)
    model.wf_lat = Param(model.wf_ids, initialize=wf_lat, within=NonNegativeReals)
    model.wf_cap = Param(model.wf_ids, initialize=wf_cap, within=NonNegativeIntegers)
    model.wf_cost = Param(model.wf_ids, initialize=wf_cost, within=NonNegativeIntegers)

    # Offshore substation model parameters
    model.oss_iso = Param(model.oss_ids, initialize=oss_iso, within=NonNegativeIntegers)
    model.oss_lon = Param(model.oss_ids, initialize=oss_lon, within=NonNegativeReals)
    model.oss_lat = Param(model.oss_ids, initialize=oss_lat, within=NonNegativeReals)
    model.oss_wdepth = Param(model.oss_ids, initialize=oss_wdepth, within=NonNegativeIntegers)
    model.oss_icover = Param(model.oss_ids, initialize=oss_icover, within=Binary)
    model.oss_pdist = Param(model.oss_ids, initialize=oss_pdist, within=NonNegativeIntegers)

    # Onshore substation model parameters
    model.onss_iso = Param(model.onss_ids, initialize=onss_iso, within=NonNegativeIntegers)
    model.onss_lon = Param(model.onss_ids, initialize=onss_lon, within=NonNegativeReals)
    model.onss_lat = Param(model.onss_ids, initialize=onss_lat, within=NonNegativeReals)

    """
    Define decision variables
    """
    print("Defining decision parameters...")
    
    # Calculate viable connections
    viable_iac = find_viable_iac(wf_lon, wf_lat, oss_lon, oss_lat)
    viable_ec = find_viable_ec(oss_lon, oss_lat, onss_lon, onss_lat)

    model.viable_iac_ids = Set(initialize= viable_iac, dimen=2)
    model.viable_ec_ids = Set(initialize= viable_ec, dimen=2)
    
    model.select_wf_var = Var(model.wf_ids, within=Binary)
    model.select_oss_var = Var(model.oss_ids, within=Binary)
    model.select_iac_var = Var(model.viable_iac_ids, within=Binary)
    model.select_ec_var = Var(model.viable_ec_ids, within=Binary)
    
    # Print the decision variables
    print("select_wf ids:", list(model.select_wf_var)[:5])
    print("select_oss ids:", list(model.select_oss_var)[:5])
    print("select_iac ids:", list(model.select_iac_var)[:20])
    print("select_ec ids:", list(model.select_ec_var)[:20])


    """
    Define Expressions
    """
    print("Defining distance expressions...")
    
    def iac_dist_rule(model, wf, oss):
        """
        Calculate the geographic distance between a wind farm (WF) and an offshore substation (OSS) using the Haversine formula,
        only if there is an inter-array cable (IAC) connection.

        Parameters:
        - model: The Pyomo model object.
        - wf: Index of the wind farm.
        - oss: Index of the offshore substation.

        Returns:
        - The calculated distance multiplied by the binary decision variable indicating if the connection exists.
        """
        return haversine(model.wf_lon[wf], model.wf_lat[wf], model.oss_lon[oss], model.oss_lat[oss]) * model.select_iac_var[wf, oss]
    
    model.iac_dist_exp = Expression(model.viable_iac_ids, rule=iac_dist_rule)

    def ec_dist_rule(model, oss, onss):
        """
        Calculate the geographic distance between an offshore substation (OSS) and an onshore substation (ONSS) using the Haversine formula,
        only if there is an export cable (EC) connection.

        Parameters:
        - model: The Pyomo model object.
        - oss: Index of the offshore substation.
        - onss: Index of the onshore substation.

        Returns:
        - The calculated distance multiplied by the binary decision variable indicating if the connection exists.
        """
        return haversine(model.oss_lon[oss], model.oss_lat[oss], model.onss_lon[onss], model.onss_lat[onss]) * model.select_ec_var[oss, onss]
    
    model.ec_dist_exp = Expression(model.viable_ec_ids, rule=ec_dist_rule)
    
    def iac_capacity_rule(model, wf, oss):
        """
        Calculate the capacity contribution of a wind farm (WF) to an offshore substation (OSS) through an inter-array cable (IAC).

        Parameters:
        - model: The Pyomo model object.
        - wf: Index of the wind farm.
        - oss: Index of the offshore substation.

        Returns:
        - The wind farm's capacity multiplied by the binary decision variable indicating if the connection exists.
        """
        return model.wf_cap[wf] * model.select_iac_var[wf, oss]
    
    model.iac_cap_exp = Expression(model.viable_iac_ids, rule=iac_capacity_rule)

    def oss_capacity_rule(model, oss):
        """
        Sum the capacities from all connected wind farms to an offshore substation (OSS).

        Parameters:
        - model: The Pyomo model object.
        - oss: Index of the offshore substation.

        Returns:
        - The total capacity received by the OSS from connected wind farms.
        """
        return sum(model.iac_cap_exp[wf, oss] * model.select_iac_var[wf, oss] for wf in model.wf_ids if (wf, oss) in model.viable_iac_ids)
    
    model.oss_cap_exp = Expression(model.oss_ids, rule=oss_capacity_rule)

    def ec_capacity_rule(model, oss, onss):
        """
        Calculate the transmission capacity from an offshore substation (OSS) to an onshore substation (ONSS) through an export cable (EC).

        Parameters:
        - model: The Pyomo model object.
        - oss: Index of the offshore substation.
        - onss: Index of the onshore substation.

        Returns:
        - The capacity of the OSS multiplied by the binary decision variable indicating if the connection exists.
        """
        return model.oss_cap_exp[oss] * model.select_ec_var[oss, onss]

    model.ec_cap_exp = Expression(model.viable_ec_ids, rule=ec_capacity_rule)

    
    def iac_cost_rule(model, wf, oss):
        """
        Calculate the cost of an inter-array cable (IAC) connection based on distance and capacity.

        Parameters:
        - model: The Pyomo model object.
        - wf: Index of the wind farm.
        - oss: Index of the offshore substation.

        Returns:
        - The calculated cost of the IAC.
        """
        return iac_cost_plh(model.iac_dist_exp[wf, oss], model.iac_cap_exp[wf, oss], polarity = "AC")
        
    model.iac_cost_exp = Expression(model.viable_iac_ids, rule=iac_cost_rule)

    def oss_cost_rule(model, oss):
        """
        Calculate the cost of maintaining an offshore substation (OSS) based on water depth, ice cover, and port distance,
        adjusted by its capacity.

        Parameters:
        - model: The Pyomo model object.
        - oss: Index of the offshore substation.

        Returns:
        - The calculated cost of the OSS.
        """
        return oss_cost_plh(model.oss_wdepth[oss], model.oss_icover[oss], model.oss_pdist[oss], model.oss_cap_exp[oss], polarity = "AC")

    model.oss_cost_exp = Expression(model.oss_ids, rule=oss_cost_rule)

    def ec_cost_rule(model, oss, onss):
        """
        Calculate the cost of an export cable (EC) connection between an OSS and an ONSS based on the distance and the transmission capacity.

        Parameters:
        - model: The Pyomo model object.
        - oss: Index of the offshore substation.
        - onss: Index of the onshore substation.

        Returns:
        - The calculated cost of the EC.
        """
        return ec_cost_plh(model.ec_dist_exp[oss, onss], model.ec_cap_exp[oss, onss], polarity = "AC")
    
    model.ec_cost_exp = Expression(model.viable_ec_ids, rule=ec_cost_rule)


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
        wf_total_cost = sum(model.wf_cost[wf] * model.select_wf_var[wf] for wf in model.wf_ids)
        oss_total_cost = sum(model.oss_cost_exp[oss] * model.select_oss_var[oss] for oss in model.oss_ids)
        iac_total_cost = sum(model.iac_cost_exp[wf, oss] * model.select_iac_var[wf, oss] for (wf, oss) in model.viable_iac_ids)
        ec_total_cost = sum(model.ec_cost_exp[oss, onss] * model.select_ec_var[oss, onss] for (oss, onss) in model.viable_ec_ids)
        return wf_total_cost + oss_total_cost + iac_total_cost + ec_total_cost

    # Set the objective in the model
    model.global_cost_obj = Objective(rule=global_cost_rule, sense=minimize)

    """
    Define Constraints
    """
    print("Defining constraints...")

    def min_total_wf_capacity_rule(model):
        """
        Enforce that the sum of the capacities of all selected wind farms meets at least a specified minimum fraction 
        of the total potential capacity of all wind farms considered. This constraint ensures that the optimized layout 
        provides sufficient capacity to meet energy production targets or requirements.
        
        Parameters:
        - model: The Pyomo model object containing all model components.
        
        Returns:
        - A constraint expression that the total capacity of selected wind farms is at least a certain fraction of the total potential capacity.
        """
        global_cap_frac = 0.5
        
        min_required_capacity = global_cap_frac * sum(model.wf_cap[wf] for wf in model.wf_ids)
        return sum(model.wf_cap[wf] * model.select_wf_var[wf] for wf in model.wf_ids) >= min_required_capacity
    
    model.min_total_wf_capacity_con = Constraint(rule=min_total_wf_capacity_rule)
    
    def wind_farm_to_oss_rule(model, wf):
        """
        Ensure each selected wind farm is connected to exactly one offshore substation.
        This function ensures that if a wind farm is selected, it must be connected to a single offshore substation.

        Parameters:
        - model: The Pyomo model object containing the decision variables and parameters.
        - wf: The index of the wind farm being evaluated.

        Returns:
        - A constraint expression enforcing one-to-one connection between selected wind farms and offshore substations.
        """
        return sum(model.select_iac_var[wf, oss] for oss in model.oss_ids if (wf, oss) in model.viable_iac_ids) == model.select_wf_var[wf]

    model.wind_farm_to_oss_con = Constraint(model.wf_ids, rule=wind_farm_to_oss_rule)

    def oss_to_onss_rule(model, oss):
        """
        Ensure each offshore substation that is connected to any wind farm transmits to exactly one onshore substation.
        This function enforces that offshore substations relay their connections to precisely one onshore substation.

        Parameters:
        - model: The Pyomo model object containing the decision variables and parameters.
        - oss: The index of the offshore substation being evaluated.

        Returns:
        - A constraint expression that limits each offshore substation to a single output to onshore substations,
        matching its input connections.
        """
        input_from_wf = sum(model.select_iac_var[wf, oss] for wf in model.wf_ids if (wf, oss) in model.viable_iac_ids)
        output_to_onss = sum(model.select_ec_var[oss, onss] for onss in model.onss_ids if (oss, onss) in model.viable_ec_ids)
        return output_to_onss == input_from_wf
    
    model.oss_to_onss_con = Constraint(model.oss_ids, rule=oss_to_onss_rule)

    def match_iso_wf_oss_rule(model, wf, oss):
        """
        Ensures that the country code (ISO) of the wind farm matches that of the connected offshore substation
        for all active inter-array cable (IAC) connections.

        Parameters:
        - model: The Pyomo model object containing the decision variables and parameters.
        - wf: The index of the wind farm being evaluated.
        - oss: The index of the offshore substation being evaluated.

        Returns:
        - A constraint expression that enforces matching ISO codes between wind farms and offshore substations.
        """
        if (wf, oss) in model.viable_iac_ids:
            return model.select_iac_var[wf, oss] * (model.wf_iso[wf] - model.oss_iso[oss]) == 0
        else:
            return Constraint.Skip

    model.match_iso_wf_oss_con = Constraint(model.wf_ids, model.oss_ids, rule=match_iso_wf_oss_rule)

    def match_iso_oss_onss_rule(model, oss, onss):
        """
        Ensures that the country code (ISO) of the offshore substation matches that of the connected onshore substation
        for all active export cable (EC) connections.

        Parameters:
        - model: The Pyomo model object containing the decision variables and parameters.
        - oss: The index of the offshore substation being evaluated.
        - onss: The index of the onshore substation being evaluated.

        Returns:
        - A constraint expression that enforces matching ISO codes between offshore substations and onshore substations.
        """
        if (oss, onss) in model.viable_ec_ids:
            return model.select_ec_var[oss, onss] * (model.oss_iso[oss] - model.onss_iso[onss]) == 0
        else:
            return Constraint.Skip

    model.match_iso_oss_onss_con = Constraint(model.oss_ids, model.onss_ids, rule=match_iso_oss_onss_rule)

    """
    Solve the model
    """
    print("Solving model...")

    # Create a solver object and specify PySCIPOpt as the solver
    solver = SolverFactory('scip')

    # Solve the model
    results = solver.solve(model, tee=True)  # tee=True to display solver output during solving

    """
        Print the solution
        """
    if results.solver.status == SolverStatus.ok and results.solver.termination_condition == TerminationCondition.optimal:
        print("Success! Displaying the solution...")
        
        # Print selected wind farms
        selected_wf = [wf for wf in model.wf_ids if model.select_wf_var[wf].value == 1]
        print("Selected Wind Farms: ", selected_wf)
        
        # Print selected offshore substations
        selected_oss = [oss for oss in model.oss_ids if model.select_oss_var[oss].value == 1]
        print("Selected Offshore Substations: ", selected_oss)
        
        # Print active inter-array cable connections
        active_iac = [(wf, oss) for (wf, oss) in model.viable_iac_ids if model.select_iac_var[wf, oss].value == 1]
        print("Active Inter-Array Cables: ", active_iac)
        
        # Print active export cable connections
        active_ec = [(oss, onss) for (oss, onss) in model.viable_ec_ids if model.select_ec_var[oss, onss].value == 1]
        print("Active Export Cables: ", active_ec)

    elif results.solver.termination_condition == TerminationCondition.infeasible:
        print("No solution found: Problem is infeasible.")
    else:
        print("Solver Status: ", results.solver.status)
    
    return None


# Define the main block
if __name__ == "__main__":
    # Specify the workspace folder
    workspace_folder = "C:\\Users\\cflde\\Documents\\Graduation Project\\ArcGIS Pro\\BalticSea\\Results\\datasets"

    # Call the optimization model function
    opt_model(workspace_folder)





