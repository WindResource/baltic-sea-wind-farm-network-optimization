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

def determine_support_structure(water_depth):
    """
    Determines the support structure type based on water depth.

    Returns:
    - str: Support structure type ('monopile', 'jacket', 'floating', or 'default').
    """
    # Define depth ranges for different support structures
    if 0 <= water_depth < 30:
        return "sandisland"
    elif 30 <= water_depth < 150:
        return "jacket"
    elif 150 <= water_depth:
        return "floating"
    else:
        # If water depth is outside specified ranges, assign default support structure
        arcpy.AddWarning(f"Water depth {water_depth} does not fall within specified ranges for support structures. Assigning default support structure.")
        return "default"

def calc_equip_costs(water_depth, oss_capacity, HVC_type="AC"):
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

    # Get the support structure type based on water depth
    support_structure = determine_support_structure(water_depth)

    # Define parameters
    c1, c2, c3, c4 = support_structure_coeff[support_structure]
    
    # Define equivalent electrical power
    equiv_capacity = 0.5 * oss_capacity if HVC_type == "AC" else oss_capacity

    if support_structure == 'sandisland':
        # Calculate foundation costs for sand island
        area_island = (equiv_capacity * 5)
        slope = 0.75
        r_hub = np.sqrt(area_island/np.pi)
        r_seabed = r_hub + (water_depth + 3) / slope
        volume_island = (1/3) * slope * np.pi * (r_seabed ** 3 - r_hub ** 3)
        
        equip_costs = c1 * volume_island + c2 * area_island
    else:
        # Calculate foundation costs for jacket/floating
        equip_costs = (c1 * water_depth + c2 * 1000) * equiv_capacity + (c3 * water_depth + c4 * 1000)

    return equip_costs

def calc_costs(water_depth, port_distance, oss_capacity, HVC_type = "AC", operation = "inst"):
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
    coeff = inst_coeff if operation == 'installation' else deco_coeff

    # Get the support structure type based on water depth
    support_structure = determine_support_structure(water_depth)
    
    if support_structure == 'sandisland':
        c1, c2, c3, c4, c5 = coeff[('jacket' 'PSIV')]
        # Define equivalent electrical power
        equiv_capacity = 0.5 * oss_capacity if HVC_type == "AC" else oss_capacity
        
        # Calculate installation costs for sand island
        area_island = (equiv_capacity * 5)
        slope = 0.75
        r_hub = np.sqrt(area_island/np.pi)
        r_seabed = r_hub + (water_depth + 3) / slope
        volume_island = (1/3) * slope * np.pi * (r_seabed ** 3 - r_hub ** 3)
        
        
        total_costs = (volume_island / c1) * ((2 * port_distance / 1000) / c2) + (volume_island / c3) + (volume_island / c4) * (c5 * 1000) / 24
    elif support_structure == 'jacket':
        c1, c2, c3, c4, c5 = coeff[('jacket' 'PSIV')]
        # Calculate installation costs for jacket
        total_costs = ((1 / c1) * ((2 * port_distance / 1000) / c2 + c3) + c4) * (c5 * 1000) / 24
    elif support_structure == 'floating':
        total_costs = 0
        
        # Iterate over the coefficients for floating (HLCV and AHV)
        for vessel_type in [('floating', 'HLCV'), ('floating', 'AHV')]:
            c1, c2, c3, c4, c5 = coeff[vessel_type]
            
            # Calculate installation costs for the current vessel type
            vessel_costs = ((1 if vessel_type[1] == 'HLCV' else 3) / c1) * ((2 * port_distance / 1000) / c2 + c3) + c4 * (c5 * 1000) / 24
            
            # Add the costs for the current vessel type to the total costs
            total_costs += vessel_costs
    else:
        total_costs = None
        
    return total_costs

def logi_costs(water_depth, port_distance, failure_rate=0.08):
    """
    Calculate logistics costs for major substation repairs (part of OPEX) based on water depth, port distance, and failure rate.
    
    Returns:
    - tuple: Logistics costs.
    """
    # Logistics coefficients for different vessels
    logi_coeff = {
        'JUV': (18.5, 50, 150, 1),
        'Tug': (7.5, 50, 2.5, 2)
    }

    # Determine support structure based on water depth
    support_structure = determine_support_structure(water_depth).capitalize()

    # Determine logistics vessel based on support structure
    vessel = 'Tug' if support_structure == 'Floating' else 'JUV'

    # Get logistics coefficients for the chosen vessel
    c = logi_coeff[vessel]

    # Calculate logistics time in hours per year
    logistics_time = failure_rate * ((2 * c[3] * port_distance / 1000) / c[0] + c[1])

    # Calculate logistics costs using the provided equation
    logistics_costs = logistics_time * c[3] * 1000 / 24

    return logistics_time, logistics_costs

def add_fields(layer, fields_to_add):
    """
    Add new fields to the attribute table if they do not exist.
    
    Returns:
    None
    """
    for field_name, field_type, field_label in fields_to_add:
        if field_name not in [field.name for field in arcpy.ListFields(layer)]:
            if field_name == 'SuppStruct':
                arcpy.AddField_management(layer, field_name, field_type)
                arcpy.AlterField_management(layer, field_name, new_field_alias=field_label)
                arcpy.AddMessage(f"Added field '{field_name}' to the attribute table with label '{field_label}'.")
            else:
                arcpy.AddField_management(layer, field_name, field_type)
                arcpy.AddMessage(f"Added field '{field_name}' to the attribute table.")

def update_fields():
    """
    Update the attribute table of the offshore substation coordinates shapefile (OSSC) with calculated equipment, installation,
    decommissioning, logistics costs, and Opex.

    Returns:
    - None
    """
    
    # Define the capacities for which fields are to be added
    capacities = [500, 750, 1000, 1250, 1500]

    # Define the expense categories
    expense_categories = ['Equ', 'Ins', 'Dec', 'Lgi', 'Ope']  # Adjusted to include only relevant categories

    # Define fields to be added if they don't exist, adjusting to include field_label correctly
    fields_to_add = [('SuppStruct', 'TEXT', 'Substation support structure')]
    for capacity in capacities:
        for category in expense_categories:
            field_name = f'{category}{capacity}'
            field_label = f'{category} expenses for a {capacity} GW substation'
            fields_to_add.append((field_name, 'DOUBLE', field_label))

    # Access the current ArcGIS project
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map = aprx.activeMap

    # Find the wind turbine coordinates layer in the map
    oss_layer = next((layer for layer in map.listLayers() if layer.name.startswith('OSSC')), None)

    if not oss_layer:
        arcpy.AddError("No layer starting with 'WTC' found in the current map.")
        return

    arcpy.SelectLayerByAttribute_management(oss_layer, "CLEAR_SELECTION")
    arcpy.AddMessage(f"Processing layer: {oss_layer.name}")

    existing_fields = [field.name for field in arcpy.ListFields(oss_layer)]
    add_fields(oss_layer, fields_to_add)  # Adjusted function call to match add_fields definition

    with arcpy.da.UpdateCursor(oss_layer, existing_fields + [f.name for f in fields_to_add]) as cursor:
        for row in cursor:
            water_depth = row[existing_fields.index("WaterDepth")]
            port_distance = row[existing_fields.index("Distance")]
            for capacity in capacities:
                support_structure = determine_support_structure(water_depth)

                # Equipment Costs
                equip_costs = calc_equip_costs(water_depth, capacity)
                row[existing_fields.index(f'Equ{capacity}')] = equip_costs

                # Installation and Decommissioning Costs
                inst_costs = calc_costs(water_depth, port_distance, capacity, operation="installation")
                deco_costs = calc_costs(water_depth, port_distance, capacity, operation="decommissioning")
                row[existing_fields.index(f'Ins{capacity}')] = inst_costs
                row[existing_fields.index(f'Dec{capacity}')] = deco_costs

                # Logistics and Operating Expenses
                _, logistics_costs = logi_costs(water_depth, port_distance)
                row[existing_fields.index(f'Lgi{capacity}')] = logistics_costs
                # Assume a method to calculate OPEX exists; otherwise, adjust accordingly
                # row[existing_fields.index(f'Ope{capacity}')] = calculated_opex

            cursor.updateRow(row)
    arcpy.AddMessage(f"Attribute table of {oss_layer} updated successfully.")


if __name__ == "__main__":
    update_fields()





