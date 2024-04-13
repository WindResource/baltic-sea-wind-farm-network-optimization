"""
Calculate installation or decommissioning costs of offshore substations based on the water depth, and port distance.

Parameters:
- water_depth (float): Water depth at the installation site, in meters.
- port_distance (float): Distance from the installation site to the nearest port, in kilometers.
- oss_capacity (float): Capacity of the offshore substation, in units.
- HVC_type (str, optional): Type of high-voltage converter ('AC' or 'DC'). Defaults to 'AC'.
- operation (str, optional): Type of operation ('inst' for installation or 'deco' for decommissioning). Defaults to 'inst'.

Returns:
- float: Calculated installation or decommissioning costs in Euros.

Coefficients:
- Capacity (u/lift): Capacity of the vessel in units per lift.
- Speed (km/h): Speed of the vessel in kilometers per hour.
- Load time (h/lift): Load time per lift in hours per lift.
- Inst. time (h/u): Installation time per unit in hours per unit.
- Dayrate (keu/d): Dayrate of the vessel in thousands of euros per day.

Vessels:
- SUBV (Self-Unloading Bulk Vessels)
- SPIV (Self-Propelled Installation Vessel)
- HLCV (Heavy-Lift Cargo Vessels)
- AHV (Anchor Handling Vessel)

Notes:
- The function supports both installation and decommissioning operations.
- Costs are calculated based on predefined coefficients for different support structures and vessels.
- If the support structure is unrecognized, the function returns None.
"""
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
"""
Add new fields to the attribute table if they do not exist.

Parameters:
- layer: The layer to which fields will be added.
- fields_to_add: A list of tuples containing field definitions. Each tuple should contain:
    - Field name (str): The name of the field.
    - Field type (str): The data type of the field.
    - Field label (str): The label or description of the field.

Returns:
None
"""

import arcpy
import numpy as np
import pandas as pd

def determine_support_structure(water_depth):
    """
    Determines the support structure type based on water depth. Updated to work with expanded arrays.

    Parameters:
    - water_depth (float or numpy array): Water depth in meters.

    Returns:
    - numpy array: Support structure type ('sandisland', 'jacket', 'floating', or 'default').
    """
    # Ensure water_depth is a numpy array
    water_depth = np.atleast_1d(water_depth)

    # Define depth ranges for different support structures
    support_structure = np.select(
        [water_depth < 30, (water_depth >= 30) & (water_depth < 150), water_depth >= 150],
        ["sandisland", "jacket", "floating"],
        default="default"
    )

    return support_structure

import numpy as np

def calc_equip_costs(water_depth, support_structure, oss_capacity, HVC_type):
    """
    Calculates the offshore substation equipment costs for expanded arrays of inputs.
    
    Parameters:
    - water_depth (numpy array): Expanded array of water depths in meters.
    - support_structure (numpy array): Expanded array of support structure types.
    - oss_capacity (numpy array): Expanded array of offshore substation capacities in MW.
    - HVC_type (numpy array): Expanded array of High Voltage Cable types ('AC' or 'DC').

    Returns:
    - tuple of numpy arrays: Equipment costs for support structure, power converter, and total.
    """
    # Initialize costs arrays
    supp_costs = np.zeros_like(water_depth, dtype=float)
    conv_costs = np.zeros_like(water_depth, dtype=float)

    # Coefficients for each support structure type
    support_structure_coeff = {'sandisland': (3.26, 804, 0, 0), 'jacket': (233, 47, 309, 62), 'floating': (87, 68, 116, 91)}
    equip_coeff = {'AC': (22.87, 7.06), 'DC': (102.93, 31.75)}

    # Determine equivalent capacity based on HVC type
    equiv_capacity = np.where(HVC_type == "AC", 0.5 * oss_capacity, oss_capacity)

    # Vectorized calculations for each support structure type
    for structure, (c1, c2, c3, c4) in support_structure_coeff.items():
        structure_mask = support_structure == structure

        if structure == 'sandisland':
            # Specific calculation for 'sandisland'
            area_island = equiv_capacity[structure_mask] * 5
            slope = 0.75
            r_hub = np.sqrt(area_island / np.pi)
            r_seabed = r_hub + (water_depth[structure_mask] + 3) / slope
            volume_island = (1/3) * slope * np.pi * (r_seabed**3 - r_hub**3)
            supp_costs[structure_mask] = c1 * volume_island + c2 * area_island
        else:
            # Calculations for 'jacket' or 'floating'
            supp_costs[structure_mask] = (c1 * water_depth[structure_mask] + c2 * 1000) * equiv_capacity[structure_mask] + (c3 * water_depth[structure_mask] + c4 * 1000)

    # Vectorized power converter costs based on HVC type
    for hvc_type, (c5, c6) in equip_coeff.items():
        hvc_mask = HVC_type == hvc_type
        conv_costs[hvc_mask] = c5 * oss_capacity[hvc_mask] * 1e3 + c6 * 1e6

    # Calculate total equipment costs
    equip_costs = supp_costs + conv_costs

    return supp_costs, conv_costs, equip_costs


def calc_costs(water_depth, support_structure, port_distance, oss_capacity, HVC_type="AC", operation="inst"):
    """
    Calculate installation or decommissioning costs of offshore substations based on arrays of inputs.

    Parameters:
    - water_depth (numpy array): Water depth in meters.
    - support_structure (numpy array): Type of support structure ('sandisland', 'jacket', 'floating').
    - port_distance (numpy array): Distance to port in kilometers.
    - oss_capacity (numpy array): Offshore substation capacity in MW.
    - HVC_type (str, optional): High Voltage Cable type ('AC' or 'DC'). Defaults to 'AC'.
    - operation (str, optional): Type of operation ('inst' for installation or 'deco' for decommissioning). Defaults to 'inst'.

    Returns:
    - numpy array: Calculated installation or decommissioning costs.
    """
    # Installation coefficients for different vehicles and structures
    inst_coeff = {
        'sandisland': (20000, 25, 2000, 6000, 15),
        'jacket': (1, 18.5, 24, 96, 200),
        'floating': (1, 22.5, 10, 0, 40)
    }

    # Decommissioning coefficients for different vehicles and structures
    deco_coeff = {
        'sandisland': (20000, 25, 2000, 6000, 15),
        'jacket': (1, 18.5, 24, 96, 200),
        'floating': (1, 22.5, 10, 0, 40)
    }

    # Choose the appropriate coefficients based on the operation type
    coeff_dict = inst_coeff if operation == 'inst' else deco_coeff

    # Initialize an empty array for total_costs with the same shape as the input arrays
    total_costs = np.zeros_like(water_depth, dtype=float)

    # Iterate through each support structure type and calculate costs
    for structure in np.unique(support_structure):
        # Get the coefficients for the current support structure
        c1, c2, c3, c4, c5 = coeff_dict[structure]

        # Find indices where the current support structure matches
        idx = np.where(support_structure == structure)

        # Calculate costs based on the structure type
        if structure == 'sandisland':
            # Specific calculations for sandisland
            volume_island = (oss_capacity[idx] * 5)  # Assuming a simple volume calculation based on capacity
            total_costs[idx] = ((volume_island / c1) * ((2 * port_distance[idx]) / c2) + (volume_island / c3) + (volume_island / c4)) * (c5 * 1000) / 24
        elif structure == 'jacket':
            # Specific calculations for jacket
            total_costs[idx] = ((1 / c1) * ((2 * port_distance[idx]) / c2 + c3) + c4) * (c5 * 1000) / 24
        elif structure == 'floating':
            # Specific calculations for floating
            total_costs[idx] = ((1 / c1) * ((2 * port_distance[idx]) / c2 + c3) + c4) * (c5 * 1000) / 24

    return total_costs


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


def update_fields():
    """
    Update the attribute table of the Offshore SubStation Coordinates (OSSC) layer.

    Returns:
    - None
    """
    
    # Access the current ArcGIS project
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map = aprx.activeMap

    # Find the offshore substation layer
    oss_layers = [layer for layer in map.listLayers() if layer.name.startswith('OSSC')]

    # Check if any OSSC layer exists
    if not oss_layers:
        arcpy.AddError("No layer starting with 'OSSC' found in the current map.")
        return

    # Select the first OSSC layer
    oss_layer = oss_layers[0]

    # Deselect all currently selected features
    arcpy.SelectLayerByAttribute_management(oss_layer, "CLEAR_SELECTION")

    arcpy.AddMessage(f"Processing layer: {oss_layer.name}")

    # Check if required fields exist in the attribute table
    required_fields = ['WaterDepth','Distance']
    for field in required_fields:
        if field not in [f.name for f in arcpy.ListFields(oss_layer)]:
            arcpy.AddError(f"Required field '{field}' is missing in the attribute table.")
            return

    # Convert attribute table to NumPy array
    array = arcpy.da.FeatureClassToNumPyArray(oss_layer,'*')
    water_depth_array = array['WaterDepth']
    distance_array = array['Distance']

    # Determine support structure for all water depths
    support_structure = determine_support_structure(water_depth_array)

    # Define capacities for which costs are to be calculated
    capacities = np.array([500, 1000, 1500, 2000, 2500])

    # Expand water_depth_array and support_structure to match each capacity, alternating between AC and DC for HVC type
    expanded_water_depth = np.repeat(water_depth_array[:, np.newaxis], len(capacities) * 2, axis=1).flatten()
    expanded_distance = np.repeat(distance_array[:, np.newaxis], len(capacities) * 2, axis=1).flatten()
    
    expanded_support_structure = np.repeat(support_structure[:, np.newaxis], len(capacities) * 2, axis=1).flatten()
    expanded_capacities = np.tile(np.repeat(capacities, 2), len(water_depth_array))
    HVC_types = np.tile(np.array(['AC', 'DC']), len(capacities) * len(water_depth_array))

    # Calculate equipment costs for expanded arrays
    supp_costs, conv_costs, equip_costs = calc_equip_costs(expanded_water_depth, expanded_support_structure, expanded_capacities, HVC_types)

    # Installation and decomissioning expenses
    inst_costs = calc_costs(expanded_water_depth, expanded_support_structure, expanded_distance, expanded_capacities, HVC_types, operation='inst')
    deco_costs = calc_costs(expanded_water_depth, expanded_support_structure, expanded_distance, expanded_capacities, HVC_types, operation='deco')

    # Calculate capital expenses
    cap_expenses = equip_costs + inst_costs

    # Operating expenses calculation with conditional logic for support structures
    # Using numpy.where to apply condition across the array
    ope_expenses = np.where(expanded_support_structure == 'sandisland',
                            0.03 * conv_costs + 0.015 * supp_costs,
                            0.03 * conv_costs)

    # Calculate total expenses
    total_costs = cap_expenses + deco_costs + ope_expenses  # Note: Operating expenses included in total costs

    # Save the results or update the layer attributes as required by your project needs
    arcpy.AddMessage("Data updated successfully.")

    # Define the data type for a structured array with all necessary fields
    dtype = [
        ('OSS_ID', 'U10'),  # Adjust string length as needed
        ('Longitude', float),
        ('Latitude', float),
        ('Capacity', float),
        ('HVCType', 'U2'),  # 'AC' or 'DC'
        ('TotalCosts', float),
    ]

    # Number of records
    n_records = len(expanded_water_depth)  # Assuming this represents the total number of records

    # Create an empty structured array
    data_array = np.empty(n_records, dtype=dtype)

    # Fill the array
    data_array['OSS_ID'] = np.tile(array['OSS_ID'], n_records // len(array['OSS_ID']))  # Example for repeating OSS_ID, adjust logic as needed
    data_array['Longitude'] = np.tile(array['Longitude'], n_records // len(array['Longitude']))  # Repeat for each record
    data_array['Latitude'] = np.tile(array['Latitude'], n_records // len(array['Latitude']))  # Repeat for each record
    # Populate other fields similarly
    data_array['HVCType'] = HVC_types
    data_array['Capacity'] = expanded_capacities
    data_array['TotalCosts'] = np.round(total_costs)

    # Save the structured array to a .npy file
    np.save('calculated_data.npy', data_array)

    # Confirm successful save
    print("Data saved successfully to calculated_data.npy.")
    
    # Assuming the structured array is named 'data_array'
    save_structured_array_to_txt('calculated_data.txt', data_array)
    print("Data saved successfully to calculated_data.txt.")

if __name__ == "__main__":
    update_fields()

