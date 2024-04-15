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
import os
import numpy as np
from scipy.stats import weibull_min

def determine_support_structure(water_depth):
    """
    Determines the support structure type based on water depth. Updated to work with expanded arrays.

    Parameters:
    - water_depth (float or numpy array): Water depth in meters.

    Returns:
    - str: Support structure type ('monopile', 'jacket', 'floating', or 'default').
    """
    # Ensure water_depth is a numpy array
    water_depth = np.atleast_1d(water_depth)

    # Define depth ranges for different support structures
    support_structure = np.select(
        [water_depth < 25, (water_depth >= 25) & (water_depth < 55), water_depth >= 55],
        ["monopile", "jacket", "floating"],
        default="default"
    )

    return support_structure

def equip_costs(water_depth, support_structure, turbine_capacity, year):
    """
    Calculates the equipment costs based on water depth values, year, and turbine capacity.

    Returns:
    - tuple: Tuple containing arrays of calculated equipment costs for support structures and turbines, and total equipment costs.
    """
    # Coefficients for equipment cost calculation based on the support structure and year
    support_structure_coeff = {
        'monopile': {
            '2020': (201, 613, 812, 0),
            '2030': (181, 552, 370, 0),
            '2050': (171, 521, 170, 0),
        },
        'jacket': {
            '2020': (114, -2270, 932, 0),
            '2030': (103, -2043, 478, 0),
            '2050': (97, -1930, 272, 0),
        },
        'floating': {
            '2020': (0, 774, 1481, 0),
            '2030': (0, 697, 1223, 0),
            '2050': (0, 658, 844, 0),
        }
    }

    # Coefficients for wind turbine rated cost
    turbine_coeff = {
        '2020': 1500,
        '2030': 1200,
        '2050': 1000
    }

    # Ensure water_depth, support_structure, and turbine_capacity are arrays
    water_depth = np.asarray(water_depth)
    support_structure = np.asarray(support_structure)
    turbine_capacity = np.asarray(turbine_capacity)

    # Ensure support_structure is lowercase
    support_structure = np.char.lower(support_structure)

    # Initialize arrays to store equipment costs
    supp_costs = np.zeros_like(water_depth)
    turbine_costs = turbine_capacity * turbine_coeff[year]

    # Vectorized calculations for each support structure type
    for structure, structure_coeffs in support_structure_coeff.items():
        mask = support_structure == structure
        c1, c2, c3, c4 = structure_coeffs[year]
        supp_costs[mask] = turbine_capacity[mask] * (c1 * (water_depth[mask] ** 2) + c2 * water_depth[mask] + c3) + c4

    equip_costs = supp_costs + turbine_costs
    
    return supp_costs, turbine_costs, equip_costs

def calc_costs(water_depth, support_structure, port_distance, turbine_capacity, operation):
    """
    Calculate installation or decommissioning costs based on the water depth, port distance,
    and rated power of the wind turbines.

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

    Returns:
    - numpy array: Calculated costs in Euros for each turbine.
    """
    # Ensure water_depth, support_structure, and turbine_capacity are arrays
    water_depth = np.asarray(water_depth)
    support_structure = np.asarray(support_structure)
    port_distance = np.asarray(port_distance)
    turbine_capacity = np.asarray(turbine_capacity)
    
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
    coeff = inst_coeff if operation == 'inst' else deco_coeff

    # Ensure support_structure is lowercase
    support_structure = np.char.lower(support_structure)

    # Initialize an array to store the total costs for each turbine
    total_costs = np.zeros_like(water_depth)

    # Iterate over unique support structures to calculate costs
    for structure in np.unique(support_structure):
        indices = np.where(support_structure == structure)[0]
        
        # Calculate costs for the current support structure
        if structure == 'monopile' or structure == 'jacket':
            _, c2, c3, c4, c5 = coeff['PSIV']
            c1 = 40 / turbine_capacity[indices]
            total_costs[indices] = ((1 / c1) * ((2 * port_distance[indices]) / c2 + c3) + c4) * (c5 * 1000) / 24
        elif structure == 'floating':
            for vessel_type in ['Tug', 'AHV']:
                c1, c2, c3, c4, c5 = coeff[vessel_type]
                vessel_costs = ((1 / c1) * ((2 * port_distance[indices]) / c2 + c3) + c4) * (c5 * 1000) / 24
                total_costs[indices] += vessel_costs

    return total_costs

import numpy as np
from scipy.stats import weibull_min
from scipy.interpolate import interp1d

import numpy as np
from scipy.stats import weibull_min

import numpy as np
from scipy.stats import weibull_min

def calculate_aep_and_capacity_factor(weibullA_array, weibullK_array):
    """
    Calculate the Annual Energy Production (AEP) and Capacity Factor of wind turbines.

    Args:
        weibullA_array (numpy array): Array of Weibull scale parameters (m/s).
        weibullK_array (numpy array): Array of Weibull shape parameters.

    Returns:
        tuple: A tuple containing arrays of AEP (in kWh) and Capacity Factor (as a percentage).
    """
    # Constants and parameters
    alpha = 0.11  # Exponent of the power law for scaling wind speed
    hub_height = 112  # Wind turbine hub height (meters)
    hours_per_year = 365.25 * 24  # Average number of hours in a year
    ava_factor = 0.94  # Wind turbine availability factor
    turbine_rating = 8 * 1e3  # Turbine rating (kW)

    # Power curve of the NREL Reference 8MW wind turbine
    power_curve_data = {
        1: 0, 2: 0, 3: 0, 4: 359, 4.5: 561, 5: 812, 5.5: 1118, 6: 1483, 6.5: 1911, 7: 2407,
        7.5: 2974, 8: 3616, 8.5: 4336, 9: 5135, 9.5: 6015, 10: 6976, 10.5: 7518, 11: 7813,
        12: 8000, 13: 8000, 14: 8000, 15: 8000, 16: 8000, 17: 8000, 18: 8000, 19: 8000,
        20: 8000, 21: 8000, 22: 8000, 23: 8000, 24: 8000, 25: 8000
    }

    # Initialize arrays to store AEP and capacity factor
    aep_array = np.zeros_like(weibullA_array)
    capacity_factor_array = np.zeros_like(weibullK_array)

    # Create wind speeds array
    wind_speeds = np.array(list(power_curve_data.keys()))

    # Iterate over each element of the input arrays
    for i, (weibullA, weibullK) in enumerate(zip(weibullA_array, weibullK_array)):
        # Scale the Weibull parameters to hub height using the power law
        weibullA_hh = weibullA * (hub_height / 100) ** alpha

        # Define the Weibull distribution with the scaled parameters
        weibull_dist = weibull_min(weibullK, scale=weibullA_hh)

        # Calculate the probability density function (PDF) at each wind speed
        pdf_array = weibull_dist.cdf(wind_speeds + 0.5) - weibull_dist.cdf(wind_speeds - 0.5)

        # Calculate AEP by integrating the power curve over the Weibull distribution
        aep_array[i] = np.sum(np.array(list(power_curve_data.values())) * pdf_array) * hours_per_year * ava_factor

        # Calculate capacity factor
        capacity_factor_array[i] = (aep_array[i] / (turbine_rating * hours_per_year))  # Convert to percentage

    return aep_array, capacity_factor_array

def save_structured_array_to_txt(filename, structured_array):
    """
    Saves a structured numpy array to a text file.

    Parameters:
    - filename (str): The path to the file where the array should be saved.
    - structured_array (numpy structured array): The array to save.
    """
    # Open the file in write mode
    with open(filename, 'w') as file:
        # Write header
        header = ', '.join(structured_array.dtype.names)
        file.write(header + '\n')

        # Write data rows
        for row in structured_array:
            row_str = ', '.join(str(value) for value in row)
            file.write(row_str + '\n')

def gen_dataset(output_folder: str):
    """
    Generates a numpy dataset containing longitude, latitude, AC and DC capacities, and total costs for each OSS_ID.
    """
    
    # Access the current ArcGIS project
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map = aprx.activeMap

    # Find the offshore substation layer
    wtc_layer = [layer for layer in map.listLayers() if layer.name.startswith('WTC')][0]

    wfc_layer = [layer for layer in map.listLayers() if layer.name.startswith('WFC')][0]
    
    # Check if any OSSC layer exists
    if not wtc_layer:
        arcpy.AddError("No layer starting with 'WTC' found in the current map.")
        return
    if not wfc_layer:
        arcpy.AddError("No layer starting with 'WFC' found in the current map.")
        return

    # Deselect all currently selected features
    for layer in [wtc_layer,wfc_layer]:
        arcpy.SelectLayerByAttribute_management(layer, "CLEAR_SELECTION")

    arcpy.AddMessage(f"Processing layer: {wtc_layer.name}")

    # Check if required fields exist in the attribute table
    required_fields = ['WaterDepth','Distance']
    for field in required_fields:
        if field not in [f.name for f in arcpy.ListFields(wtc_layer)]:
            arcpy.AddError(f"Required field '{field}' is missing in the attribute table.")
            return

    # Convert attribute table to NumPy array
    array_wtc = arcpy.da.FeatureClassToNumPyArray(wtc_layer,'*')
    water_depth_array = array_wtc['WaterDepth']
    distance_array = array_wtc['Distance']
    capacity_array = array_wtc['Capacity']
    wfid_array = array_wtc['WF_ID']
    wtid_array = array_wtc['WT_ID']
    wa_array = array_wtc['WeibullA']
    wk_array = array_wtc['WeibullK']

    array_wf = arcpy.da.FeatureClassToNumPyArray(wfc_layer,'*')
    longitude_array_wf = array_wf['Longitude']
    latitude_array_wf = array_wf['Latitude']
    wfid_array_wf = array_wf['WF_ID']
    iso_array_wf = array_wf['ISO']

    # Determine support structure for all water depths
    supp_array = determine_support_structure(water_depth_array)

    # Calculate equipment costs for expanded arrays
    supp_costs, turbine_costs, equip_costs_wt = equip_costs(water_depth_array, supp_array, capacity_array, year = "2020")

    # Installation and decomissioning expenses
    inst_costs_wt = calc_costs(water_depth_array, supp_array, distance_array, capacity_array, operation = "inst")
    deco_costs_wt = calc_costs(water_depth_array, supp_array, distance_array, capacity_array, operation = "deco")

    # Calculate capital expenses
    cap_expenses_wt = np.add(equip_costs_wt, inst_costs_wt)

    # Operating expenses calculation with conditional logic for support structures
    # Using numpy.where to apply condition across the array
    ope_expenses_wt = 0.025 * turbine_costs

    # Calculate total expenses
    total_costs_wt = np.add(cap_expenses_wt, deco_costs_wt, ope_expenses_wt)

    aep_array, cf_array = calculate_aep_and_capacity_factor(wa_array, wk_array)
    
    # Aggregate total costs and capacity for each unique WF_ID
    total_costs_wf = {}
    total_capacity_wf = {}
    total_aep_wf = {}
    avg_cf_wf = {}

    # Iterate over each unique WF_ID
    unique_wfids = np.unique(wfid_array)
    for wfid in unique_wfids:
        # Find indices where WF_ID matches the current WF_ID
        wt_index = np.where(wfid_array == wfid)[0]
        
        # Sum total costs and capacity for the current WF_ID
        total_costs_wf[wfid] = np.sum(total_costs_wt[wt_index])
        total_capacity_wf[wfid] = np.sum(capacity_array[wt_index])
        
        total_aep_wf[wfid] = np.sum(aep_array[wt_index])
        avg_cf_wf[wfid] = np.mean(cf_array[wt_index])


    # Define data dictionary structure
    dtype = [
        ('WF_ID', int),  # Adjust string length as needed
        ('ISO', 'U10'),
        ('Longitude', float),
        ('Latitude', float),
        ('TotalCapacity', int),
        ('TotalCost', int),
        ('TotalAEP', object),
        ('AvgCf', float)
    ]
    
    # Initialize an empty list to store data dictionaries
    data_list = []
    
    # Iterate through each unique WF_ID and create data dictionary
    for wfid in unique_wfids:
        # Find the first occurrence of WF_ID in the array
        wf_index = np.where(wfid_array_wf == wfid)[0][0]
        
        iso = iso_array_wf[wf_index]
        
        # Retrieve longitude and latitude from the first occurrence
        longitude = longitude_array_wf[wf_index]
        latitude = latitude_array_wf[wf_index]
        
        # Retrieve total costs and capacity for the current WF_ID
        total_costs = total_costs_wf[wfid]
        total_capacity = total_capacity_wf[wfid]
        
        total_aep = total_aep_wf[wfid]
        avg_cf = avg_cf_wf[wfid]
        
        # Create data dictionary
        data_dict = {
            'WF_ID': wfid,
            'ISO': iso,
            'Longitude': np.round(longitude, 6),
            'Latitude': np.round(latitude, 6),
            'TotalCapacity': np.int(np.round(total_capacity)),
            'TotalCost': np.int(np.round(total_costs / 1000)),
            'TotalAEP' : np.int(np.round(total_aep)),
            'AvgCf': np.round(avg_cf, 4)
        }
        data_list.append(data_dict)

    # Convert the list of dictionaries to a structured array
    data_array = np.array([(d['WF_ID'], d['ISO'], d['Longitude'], d['Latitude'], d['TotalCapacity'], d['TotalCost'], d['TotalAEP'], d['AvgCf']) for d in data_list], dtype=dtype)

    # Sort data_array by WF_ID
    data_array_sorted = np.sort(data_array, order='WF_ID')

    # Save the sorted structured array to a .npy file in the specified folder
    np.save(os.path.join(output_folder, 'wf_data.npy'), data_array_sorted)
    arcpy.AddMessage("Data saved successfully.")

    # Save sorted structured array to a .txt file
    save_structured_array_to_txt(os.path.join(output_folder, 'wf_data.txt'), data_array_sorted)
    arcpy.AddMessage("Data saved successfully.")

    
if __name__ == "__main__":
    # Prompt the user to input the folder path where they want to save the output files
    output_folder = arcpy.GetParameterAsText(0)
    gen_dataset(output_folder)
