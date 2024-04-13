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

def calc_equip_costs(water_depth, support_structure, year, turbine_capacity):
    """
    Calculates the equipment costs based on water depth values, year, and turbine capacity.

    Returns:
    - float: Calculated equipment costs.
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

    # Calculate equipment costs using the provided formula
    c1, c2, c3 = support_structure_coeff[(support_structure, year)]
    support_structure_costs = turbine_capacity * (c1 * (water_depth ** 2)) + (c2 * water_depth) + (c3 * 1000)
    turbine_costs = turbine_capacity * turbine_coeff[year]

    equip_costs = support_structure_costs + turbine_costs
    
    return equip_costs

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
    coeff = inst_coeff if operation == 'installation' else deco_coeff

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

def update_fields():
    """
    Update the attribute table of the wind turbine coordinates shapefile (WTC) with calculated equipment, installation,
    decommissioning, logistics costs, logistics time, and Opex.

    Returns:
    - None
    """
    # Function to add a field if it does not exist in the layer
    def add_field_if_not_exists(layer, field_name, field_type):
        if field_name not in [field.name for field in arcpy.ListFields(layer)]:
            arcpy.AddField_management(layer, field_name, field_type)
            arcpy.AddMessage(f"Added field '{field_name}' to the attribute table.")

    # Define fields to be added if they don't exist
    fields_to_add = [
        ('SuppStruct', 'TEXT'),
        ('EquiC20', 'DOUBLE'),
        ('EquiC30', 'DOUBLE'),
        ('EquiC50', 'DOUBLE'),
        ('InstC', 'DOUBLE'),
        ('Capex20', 'DOUBLE'),
        ('Capex30', 'DOUBLE'),
        ('Capex50', 'DOUBLE'),
        ('LogiC', 'DOUBLE'),
        ('Opex20', 'DOUBLE'),
        ('Opex30', 'DOUBLE'),
        ('Opex50', 'DOUBLE'),
        ('Decex', 'DOUBLE'),
    ]
    
    # Access the current ArcGIS project
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map = aprx.activeMap

    # Find the wind turbine layer in the map
    turbine_layer = next((layer for layer in map.listLayers() if layer.name.startswith('WTC')), None)

    # Check if the turbine layer exists
    if not turbine_layer:
        arcpy.AddError("No layer starting with 'WTC' found in the current map.")
        return

    # Deselect all currently selected features
    arcpy.SelectLayerByAttribute_management(turbine_layer, "CLEAR_SELECTION")
    
    arcpy.AddMessage(f"Processing layer: {turbine_layer.name}")

    # Check if required fields exist in the attribute table
    required_fields = ['WaterDepth', 'Capacity', 'Distance']
    existing_fields = [field.name for field in arcpy.ListFields(turbine_layer)]
    for field in required_fields:
        if field not in existing_fields:
            arcpy.AddError(f"Required field '{field}' is missing in the attribute table.")
            return

    # Add new fields to the attribute table if they do not exist
    for field_name, field_type in fields_to_add:
        add_field_if_not_exists(turbine_layer, field_name, field_type)

    # Get the list of fields in the attribute table
    fields = [field.name for field in arcpy.ListFields(turbine_layer)]

    # Update each row in the attribute table
    with arcpy.da.UpdateCursor(turbine_layer, fields) as cursor:
        for row in cursor:
            # Extract water depth and turbine capacity from the current row
            water_depth = row[fields.index("WaterDepth")]  # Invert the sign
            turbine_capacity = row[fields.index("Capacity")]
            distance = row[fields.index("Distance")]
            
            # Determine support structure and assign it to the corresponding field
            support_structure = determine_support_structure(water_depth)
            row[fields.index("SuppStruct")] = support_structure.capitalize()

            # Iterate over each year and calculate costs and time
            for year in ['2020', '2030', '2050']:
                field_name_ec = f"EquiC{year[2:]}"
                field_name_cap = f"Capex{year[2:]}"

                if field_name_ec in fields and field_name_cap in fields:
                    # Round function
                    def rnd(r):
                        return round(r / int(1e6), 6)
                    
                    # Calculate equipment costs for the current year
                    equi_costs = calc_equip_costs(water_depth, support_structure, year, turbine_capacity)
                    row[fields.index(field_name_ec)] = rnd(equi_costs)

                    # Calculate installation and decommissioning costs
                    inst_costs = calc_costs(water_depth, support_structure, distance,
                                                        turbine_capacity, 'installation')
                    deco_costs = calc_costs(water_depth, support_structure, distance,
                                                        turbine_capacity, 'decommissioning')

                    # Assign calculated values to the corresponding fields
                    row[fields.index("InstC")] = rnd(inst_costs)

                    # Calculate and assign total capital expenditure for the current year
                    capex = equi_costs + inst_costs
                    row[fields.index(field_name_cap)] = rnd(capex)

                    # Assign decommissioning costs if the field exists
                    field_name_dec = "Decex"
                    if field_name_dec in fields:
                        row[fields.index(field_name_dec)] = rnd(deco_costs)

                    # Calculate and assign logistics costs
                    logi_costs = calc_logi_costs(water_depth, support_structure, distance)
                    row[fields.index("LogiC")] = rnd(logi_costs)

                    # Calculate material costs and assign operating expenses if the field exists
                    material_costs = 0.025 * equi_costs
                    field_name_opex = f"Opex{year[2:]}"
                    if field_name_opex in fields:
                        row[fields.index(field_name_opex)] = rnd(material_costs + logi_costs)

            cursor.updateRow(row)

    arcpy.AddMessage(f"Attribute table of {turbine_layer} updated successfully.")

if __name__ == "__main__":
    update_fields()





