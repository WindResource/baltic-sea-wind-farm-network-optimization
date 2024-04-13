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

def determine_support_structure(water_depth):
    """
    Determines the support structure type based on water depth.

    Returns:
    - str: Support structure type ('monopile', 'jacket', 'floating', or 'default').
    """
    # Define depth ranges for different support structures
    if 0 <= water_depth < 25:
        return "monopile"
    elif 25 <= water_depth < 55:
        return "jacket"
    elif 55 <= water_depth <= 200:
        return "floating"
    else:
        # If water depth is outside specified ranges, assign default support structure
        arcpy.AddWarning(f"Water depth {water_depth} does not fall within specified ranges for support structures. Assigning default support structure.")
        return "default"

def equip_costs(water_depth, support_structure, turbine_capacity, year):
    """
    Calculates the equipment costs based on water depth values, year, and turbine capacity.

    Returns:
    - float: Calculated equipment costs.
    """
    # Coefficients for equipment cost calculation based on the support structure and year
    supp_coeff = {
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

    # Calculate equipment costs using the provided formula
    c1, c2, c3 = supp_coeff[(support_structure, year)]
    supp_costs = turbine_capacity * (c1 * (water_depth ** 2)) + (c2 * water_depth) + (c3 * 1000)
    turbine_costs = turbine_capacity * turbine_coeff[year]

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
    - tuple: Calculated hours and costs in Euros.
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
    coeff = inst_coeff if operation == 'inst' else deco_coeff

    # Determine support structure based on water depth
    support_structure = determine_support_structure(water_depth).lower()

    if support_structure == 'monopile' or 'jacket':
        c1, c2, c3, c4, c5 = coeff['PSIV']
        # Calculate installation costs for jacket
        total_costs = ((1 / c1) * ((2 * port_distance) / c2 + c3) + c4) * (c5 * 1000) / 24
    elif support_structure == 'floating':
        total_costs = 0
        
        # Iterate over the coefficients for floating (Tug and AHV)
        for vessel_type in ['Tug', 'AHV']:
            c1, c2, c3, c4, c5 = coeff[vessel_type]
            
            # Calculate installation costs for the current vessel type
            vessel_costs = ((1 / c1) * ((2 * port_distance) / c2 + c3) + c4) * (c5 * 1000) / 24
            
            # Add the costs for the current vessel type to the total costs
            total_costs += vessel_costs
    else:
        total_costs = None
        
    return total_costs

def calc_logi_costs(water_depth, support_structure, port_distance, failure_rate=0.08):
    """
    Calculate logistics time and costs for major wind turbine repairs (part of OPEX) based on water depth, port distance, and failure rate for major wind turbine repairs.
    
    Coefficients:
        - Speed (km/h): Speed of the vessel in kilometers per hour.
        - Repair time (h): Repair time in hours.
        - Dayrate (keu/d): Dayrate of the vessel in thousands of euros per day.
        - Roundtrips: Number of roundtrips for the logistics operation.
    
    Returns:
    - tuple: Logistics time in hours per year and logistics costs in Euros.
    """
    # Logistics coefficients for different vessels
    logi_coeff = {
        'JUV': (18.5, 50, 150, 1),
        'Tug': (7.5, 50, 2.5, 2)
    }

    # Determine logistics vessel based on support structure
    vessel = 'JUV' if support_structure == 'monopile' or 'jacket' else 'Tug'

    c1, c2, c3, c4 = logi_coeff[vessel]

    # Calculate logistics costs
    logi_costs = failure_rate * ((2 * c4 * port_distance / 1000) / c1 + c2) * (c3 * 1000) / 24

    return logi_costs

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

    array_wf = arcpy.da.FeatureClassToNumPyArray(wfc_layer,'*')
    longitude_array = array_wf['Longitude']
    latitide_array = array_wf['Latitude']

    # Determine support structure for all water depths
    supp_array = determine_support_structure(water_depth_array)

    # Calculate equipment costs for expanded arrays
    supp_costs, turbine_costs, equip_costs_wt = equip_costs(water_depth_array, supp_array, capacity_array, year = "2020")

    # Installation and decomissioning expenses
    inst_costs_wt = calc_costs(water_depth_array, supp_array, distance_array, capacity_array, operation = "inst")
    deco_costs_wt = calc_costs(water_depth_array, supp_array, distance_array, capacity_array, operation = "inst")

    # Calculate capital expenses
    cap_expenses_wt = np.add(equip_costs_wt, inst_costs_wt)

    # Operating expenses calculation with conditional logic for support structures
    # Using numpy.where to apply condition across the array
    ope_expenses_wt = 0.025 * turbine_costs

    # Calculate total expenses
    total_costs_wt = np.add(cap_expenses_wt, deco_costs_wt, ope_expenses_wt)

    # Find unique values of 'WF_ID' and their corresponding counts
    unique_wf_ids, counts = np.unique(wfid_array, return_counts=True)

    # Initialize an array to store the sum of 'total_costs_wt' for each unique 'WF_ID'
    total_costs_sum_per_wf_id = np.zeros_like(unique_wf_ids, dtype=float)

    # Calculate the cumulative sum of 'total_costs_wt' using np.add.at
    np.add.at(total_costs_sum_per_wf_id, wfid_array, total_costs_wt)

    # Return the total costs per WF_ID
    total_costs_wf = total_costs_sum_per_wf_id / counts
    
    
    # Save the results or update the layer attributes as required by your project needs
    arcpy.AddMessage("Data updated successfully.")
    
    ## some code here

    # Define the data type for a structured array with all necessary fields
    dtype = [
        ('WT_ID', 'U10'),  # Adjust string length as needed
        ('Longitude', float),
        ('Latitude', float),
        ('Capacity', float),
        ('TotalCost', float)
    ]

    # Initialize an empty list to store data dictionaries
    data_list = []

    # Iterate over the indices of the unique WF_IDs
    for i, wf_id in enumerate(unique_wf_ids):
        # Find the indices where WF_ID equals the current unique WF_ID
        indices = np.where(wfid_array == wf_id)[0]
        # Iterate over the indices and create a data dictionary for each record
        for index in indices:
            data_dict = {
                'WT_ID': wtid_array[index],
                'Longitude': longitude_array[index],
                'Latitude': latitide_array[index],
                'Capacity': capacity_array[index],
                'TotalCost': total_costs_wf[i]  # Use the corresponding total cost for the WF_ID
            }
            # Append the data dictionary to the data list
            data_list.append(data_dict)

    # Convert the list of dictionaries to a structured array
    data_array = np.array([(d['WT_ID'], d['Longitude'], d['Latitude'], d['Capacity'], d['TotalCost']) for d in data_list], dtype=dtype)

    # Save the structured array to a .npy file in the specified folder
    np.save(os.path.join(output_folder, 'oss_data.npy'), data_array)
    arcpy.AddMessage("Data saved successfully.")

    # Assuming the structured array is named 'data_array'
    save_structured_array_to_txt(os.path.join(output_folder, 'oss_data.txt'), data_array)
    arcpy.AddMessage("Data saved successfully.")


if __name__ == "__main__":
    # Prompt the user to input the folder path where they want to save the output files
    output_folder = arcpy.GetParameterAsText(0)
    gen_dataset(output_folder)




