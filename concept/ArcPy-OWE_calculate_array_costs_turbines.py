"""
This script is designed to automate the calculation and updating of cost and logistical parameters for wind turbine installations within GIS shapefiles, utilizing the ArcPy site package. It facilitates the assessment of various costs associated with wind turbine projects, including equipment, installation, decommissioning, and logistics, based on spatial and non-spatial attributes found in shapefiles for turbines and wind farms.

Functions:

    calculate_total_costs(turbine_layer, windfarm_file):
        Calculate the total costs for each category by summing the corresponding values in each row of the turbine attribute table.

        Parameters:
        - turbine_layer (str): Path to the turbine shapefile.
        - windfarm_file (str): Path to the wind farm shapefile.

        Returns:
        - dict: A dictionary containing total costs for each category.

    determine_support_structure(water_depth):
        Determines the support structure type based on water depth.

        Parameters:
        - water_depth (float): Water depth in meters.

        Returns:
        - str: Support structure type ('monopile', 'jacket', 'floating', or 'default').

    calc_equip_costs(water_depth, year, turbine_capacity):
        Calculates the equipment costs based on water depth values, year, and turbine capacity.

        Parameters:
        - water_depth (float): Water depth in meters.
        - year (str): Year for which equipment costs are calculated ('2020', '2030', or '2050').
        - turbine_capacity (float): Rated power capacity of the wind turbine.

        Returns:
        - float: Calculated equipment costs.

    calc_costs(water_depth, port_distance, turbine_capacity, operation):
        Calculate installation or decommissioning costs based on the water depth, port distance,
        and rated power of the wind turbines.

        Parameters:
        - water_depth (float): Water depth in meters.
        - port_distance (float): Distance to the port in meters.
        - turbine_capacity (float): Rated power capacity of the wind turbines in megawatts (MW).
        - operation (str): Operation type ('installation' or 'decommissioning').

        Coefficients:
        - Capacity (u/lift): Capacity of the vessel in units per lift.
        - Speed (km/h): Speed of the vessel in kilometers per hour.
        - Load time (h/lift): Load time per lift in hours per lift.
        - Inst. time (h/u): Installation time per unit in hours per unit.
        - Dayrate (keu/d): Dayrate of the vessel in thousands of euros per day.

        Vessels:
        - SPIV (Self-Propelled Installation Vessel)
        - AHV (Anchor Handling Vessel)
        - Tug (Tug Boat)

        Equation:
        Hours = (1 / c[0]) * ((2 * port_distance / 1000) / c[1] + c[2]) + c[3]
        Cost = Hours * c[4] * 1000 / 24

        Returns:
        - tuple: Calculated hours and costs in Euros.

    logi_costs(water_depth, port_distance, failure_rate=0.08):
        Calculate logistics time and costs based on water depth, port distance, and failure rate for major wind turbine repairs.

        Parameters:
        - water_depth (float): Water depth in meters.
        - port_distance (float): Distance to the port in meters.
        - failure_rate (float, optional): Failure rate for the wind turbines (/yr). Default is 0.08.

        Coefficients:
        - Speed (km/h): Speed of the vessel in kilometers per hour.
        - Repair time (h): Repair time in hours.
        - Dayrate (keu/d): Dayrate of the vessel in thousands of euros per day.
        - Roundtrips: Number of roundtrips for the logistics operation.

        Equations:
        - Logistics Time: labda * ((2 * c4 * port_distance) / c1 + c2)
        - Logistics Costs: Logistics Time * c4 / 24

        Returns:
        - tuple: Logistics time in hours per year and logistics costs in Euros.

    update_fields():
        Update the attribute table of the wind turbine coordinates shapefile (WTC) with calculated equipment, installation,
        decommissioning, logistics costs, logistics time, and Opex.

        Returns:
        - None

"""
import arcpy
import numpy as np

def determine_support_structure(water_depth):
    """
    Determines the support structure type based on water depth.

    Returns:
    - np.ndarray: Support structure type ('monopile', 'jacket', 'floating', or 'default').
    """
    # Define depth ranges for different support structures
    support_structure = np.empty_like(water_depth, dtype='<U8')
    support_structure[(0 <= water_depth) & (water_depth < 25)] = "monopile"
    support_structure[(25 <= water_depth) & (water_depth < 55)] = "jacket"
    support_structure[(55 <= water_depth) & (water_depth <= 200)] = "floating"
    support_structure[~((0 <= water_depth) & (water_depth <= 200))] = "default"

    return support_structure

def calc_equip_costs(water_depth, support_structure, year, turbine_capacity):
    """
    Calculates the equipment costs based on water depth values, year, and turbine capacity.

    Returns:
    - np.ndarray: Calculated equipment costs.
    """
    # Coefficients for equipment cost calculation based on the support structure and year
    support_structure_coeff = {
        ('monopile', '2020'): (201, 613, 812),
        ('monopile', '2030'): (181, 552, 370),
        ('monopile', '2050'): (171, 521, 170),
        ('jacket', '2020'): (114, -2270, 932),
        ('jacket', '2030'): (103, -2043, 478),
        ('jacket', '2050'): (97, -1930, 272),
        ('floating', '2020'): (0, 774, 1481),
        ('floating', '2030'): (0, 697, 1223),
        ('floating', '2050'): (0, 658, 844)
    }

    # Coefficients for wind turbine rated cost
    turbine_coeff = {
        '2020': 1500,
        '2030': 1200,
        '2050': 1000
    }

    # Look up coefficients for each element in the arrays
    c1 = np.vectorize(lambda ss, yr: support_structure_coeff[(ss, yr)][0])(support_structure, year)
    c2 = np.vectorize(lambda ss, yr: support_structure_coeff[(ss, yr)][1])(support_structure, year)
    c3 = np.vectorize(lambda ss, yr: support_structure_coeff[(ss, yr)][2])(support_structure, year)
    support_structure_costs = turbine_capacity * (c1 * (water_depth ** 2)) + (c2 * water_depth) + (c3 * 1000)
    turbine_costs = turbine_capacity * turbine_coeff[year]

    equip_costs = support_structure_costs + turbine_costs

    return equip_costs

def calc_costs(water_depth, support_structure, port_distance, turbine_capacity, operation):
    """
    Calculate installation or decommissioning costs based on the water depth, port distance,
    and rated power of the wind turbines.

    Returns:
    - np.ndarray: Calculated hours and costs in Euros.
    """
    # Installation coefficients for different vehicles
    inst_coeff = {
        'PSIV': (40 / turbine_capacity, 18.5, 24, 144, 200),
        'Tug': (0.3, 7.5, 5, 0, 2.5),
        'AHV': (7, 18.5, 30, 90, 40)
    }

    # Decommissioning coefficients for different vehicles
    deco_coeff = {
        'PSIV': (40 / turbine_capacity, 18.5, 24, 144, 200),
        'Tug': (0.3, 7.5, 5, 0, 2.5),
        'AHV': (7, 18.5, 30, 30, 40)
    }

    # Choose the appropriate coefficients based on the operation type
    coeff = inst_coeff if operation == 'installation' else deco_coeff

    # Vectorized support_structure calculation
    support_structure = determine_support_structure(water_depth).lower()

    if np.any((support_structure == 'monopile') | (support_structure == 'jacket')):
        c1, c2, c3, c4, c5 = np.vectorize(lambda vt: coeff['PSIV'] if vt in ['monopile', 'jacket'] else None)(support_structure)
        total_costs = ((1 / c1) * ((2 * port_distance) / c2 + c3) + c4) * (c5 * 1000) / 24
    elif np.any(support_structure == 'floating'):
        total_costs = np.zeros_like(support_structure)
        
        for vessel_type in ['Tug', 'AHV']:
            c1, c2, c3, c4, c5 = np.vectorize(lambda vt: coeff[vessel_type] if vt == 'floating' else None)(support_structure)
            vessel_costs = ((1 / c1) * ((2 * port_distance) / c2 + c3) + c4) * (c5 * 1000) / 24
            total_costs += vessel_costs
    else:
        total_costs = None
        
    return total_costs

def calc_logi_costs(water_depth, support_structure, port_distance, failure_rate=0.08):
    """
    Calculate logistics time and costs for major wind turbine repairs (part of OPEX) based on water depth, port distance, and failure rate for major wind turbine repairs.
    
    Returns:
    - np.ndarray: Logistics time in hours per year and logistics costs in Euros.
    """
    # Logistics coefficients for different vessels
    logi_coeff = {
        'JUV': (18.5, 50, 150, 1),
        'Tug': (7.5, 50, 2.5, 2)
    }

    # Determine logistics vessel based on support structure
    vessel = np.where(support_structure == 'monopile' | 'jacket', 'JUV', 'Tug')

    c1, c2, c3, c4 = np.vectorize(lambda vt: logi_coeff[vt])(vessel)

    # Calculate logistics costs
    logi_costs = failure_rate * ((2 * c4 * port_distance / 1000) / c1 + c2) * (c3 * 1000) / 24

    return logi_costs

import pandas as pd
import numpy as np

def update_fields():
    """
    Update the attribute table of the Offshore SubStation Coordinates (OSSC) layer.
    """
    # Placeholder setup for ArcGIS objects
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map = aprx.activeMap
    oss_layers = [layer for layer in map.listLayers() if layer.name.startswith('OSSC')]
    if not oss_layers:
        arcpy.AddError("No OSSC layer found.")
        return
    oss_layer = oss_layers[0]
    arcpy.SelectLayerByAttribute_management(oss_layer, "CLEAR_SELECTION")
    
    # Check required fields exist
    required_fields = ['WaterDepth', 'Distance']
    array = arcpy.da.FeatureClassToNumPyArray(oss_layer, required_fields)
    water_depth_array = array['WaterDepth']
    distance_array = array['Distance']

    # Determine support structure
    support_structure = determine_support_structure(water_depth_array)

    # Define capacities and HVC types
    capacities = np.array([500, 1000, 1500, 2000, 2500])
    HVC_types = np.array(['AC', 'DC'])

    # Use np.newaxis to prepare for broadcasting
    water_depth_expanded = water_depth_array[:, np.newaxis, np.newaxis]
    distance_expanded = distance_array[:, np.newaxis, np.newaxis]
    support_structure_expanded = support_structure[:, np.newaxis, np.newaxis]
    capacities_expanded = capacities[np.newaxis, :, np.newaxis]
    HVC_types_expanded = HVC_types[np.newaxis, np.newaxis, :]

    # Broadcasting to match dimensions: locations x capacities x HVC_types
    final_shape = (water_depth_array.size, capacities.size, HVC_types.size)
    expanded_water_depth = np.broadcast_to(water_depth_expanded, final_shape).flatten()
    expanded_distance = np.broadcast_to(distance_expanded, final_shape).flatten()
    expanded_support_structure = np.broadcast_to(support_structure_expanded, final_shape).flatten()
    expanded_capacities = np.broadcast_to(capacities_expanded, final_shape).flatten()
    expanded_HVC_types = np.broadcast_to(HVC_types_expanded, final_shape).flatten()

    # Calculate costs
    # Example calculation function call (ensure your functions support these expanded arrays)
    supp_costs, conv_costs, equip_costs = calc_equip_costs(expanded_water_depth, expanded_support_structure, expanded_capacities, expanded_HVC_types)
    inst_costs = calc_costs(expanded_water_depth, expanded_support_structure, expanded_distance, expanded_capacities, expanded_HVC_types, 'inst')
    deco_costs = calc_costs(expanded_water_depth, expanded_support_structure, expanded_distance, expanded_capacities, expanded_HVC_types, 'deco')

    # Convert results to DataFrame
    df = pd.DataFrame({
        'WaterDepth': expanded_water_depth,
        'Distance': expanded_distance,
        'SupportStructure': expanded_support_structure,
        'Capacity': expanded_capacities,
        'HVCType': expanded_HVC_types,
        'SupportCosts': supp_costs,
        'ConverterCosts': conv_costs,
        'EquipmentCosts': equip_costs,
        'InstallationCosts': inst_costs,
        'DecommissioningCosts': deco_costs,
    })

    # Save DataFrame to an Excel file
    df.to_excel('results.xlsx', index=False)
    arcpy.AddMessage("Data saved to results.xlsx.")

if __name__ == "__main__":
    update_fields()
