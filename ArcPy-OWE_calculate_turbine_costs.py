import arcpy
import os

def determine_support_structure(water_depth):
    """
    Determines the support structure type based on water depth.

    Parameters:
    - water_depth (float): Water depth in meters.

    Returns:
    - str: Support structure type ('monopile', 'jacket', 'floating', or 'default').
    """
    # Define depth ranges for different support structures
    if 0 <= water_depth <= 25:
        return "monopile"
    elif 25 < water_depth <= 55:
        return "jacket"
    elif 55 < water_depth <= 200:
        return "floating"
    else:
        # If water depth is outside specified ranges, assign default support structure
        arcpy.AddWarning(f"Water depth {water_depth} does not fall within specified ranges for support structures. Assigning default support structure.")
        return "default"

def calc_equip_costs(water_depth, year, turbine_capacity):
    """
    Calculates the equipment costs based on water depth values, year, and turbine capacity.

    Parameters:
    - water_depth (float): Water depth in meters.
    - year (str): Year for which equipment costs are calculated ('2020', '2030', or '2050').
    - turbine_capacity (float): Rated power capacity of the wind turbine.

    Returns:
    - float: Calculated equipment costs.
    """
    # Coefficients for equipment cost calculation based on the support structure and year
    support_structure_coeff = {
        ('2020', 'monopile'): (201, 613, 812),
        ('2030', 'monopile'): (181, 552, 370),
        ('2050', 'monopile'): (171, 521, 170),
        ('2020', 'jacket'): (114, -2270, 932),
        ('2030', 'jacket'): (103, -2043, 478),
        ('2050', 'jacket'): (97, -1930, 272),
        ('2020', 'floating'): (0, 774, 1481),
        ('2030', 'floating'): (0, 697, 1223),
        ('2050', 'floating'): (0, 658, 844)
    }

    # Coefficients for wind turbine rated cost
    wind_turbine_coeff = {
        '2020': 1500,
        '2030': 1200,
        '2050': 1000
    }

    # Get the support structure type based on water depth
    support_structure = determine_support_structure(water_depth)

    key = (year, support_structure)
    c1, c2, c3 = support_structure_coeff[key]
    WT_rated_cost = wind_turbine_coeff[year]

    # Calculate equipment costs using the provided formula
    return turbine_capacity * ((c1 * (water_depth ** 2)) + (c2 * water_depth) + (c3 * 1000) + (WT_rated_cost))

def calc_inst_deco_costs(water_depth: float, port_distance: float, turbine_capacity: float, operation: str) -> float:
    """
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
    Cost = sum [(1 / Capacity) * ((2 * port_distance / 1000) / Speed + Load time) + Inst. time * (Dayrate * 1000 / 24)]

    Explanation:
    The cost is calculated as the sum of costs for selected vessels. For each vessel,
    the equation represents the installation or decommissioning cost, taking into account
    the vessel's capacity, speed, load time, installation time, and dayrate.

    Returns:
    - float: Calculated costs in Euros.
    """
    
    # Installation coefficients for different vehicles
    inst_coeff = {
        'PSIV': (40 / turbine_capacity, 18.5, 24, 144, 200),
        'Tug': (0.3, 7.5, 5, 0, 0),
        'AHV': (7, 18.5, 30, 90, 40)
    }

    # Decommissioning coefficients for different vehicles
    deco_coeff = {
        'PSIV': (40 / turbine_capacity, 18.5, 24, 144, 200),
        'Tug': (0.3, 7.5, 5, 0, 0),
        'AHV': (7, 18.5, 30, 30, 40)
    }

    # Choose the appropriate coefficients based on the operation type
    coeff = inst_coeff if operation == 'installation' else deco_coeff

    # Determine support structure based on water depth
    support_structure = determine_support_structure(water_depth).capitalize()

    # Determine installation vehicle based on support structure
    if support_structure.lower() == 'floating':
        # For floating support structure, use both Tug and AHV
        vehicles = ['Tug', 'AHV']
    else:
        # For other support structures, use only PSIV
        vehicles = ['PSIV']

    # Calculate costs for selected vehicles and sum them
    costs = sum(
        ((1 / c[0]) * ((2 * port_distance / 1000) / c[1] + c[2]) + c[3]) * c[4] * 1000 / 24
        for c in [coeff[vehicle] for vehicle in vehicles]
    )
    
    return costs

def update_fields(turbine_file):
    """
    Update the attribute table of a shapefile with calculated equipment, installation, and decommissioning costs.

    Parameters:
    - turbine_file (str): Path to the turbine shapefile.

    Returns:
    - None
    """
    try:
        # Check if the turbine shapefile exists
        if not arcpy.Exists(turbine_file):
            arcpy.AddError(f"Turbine shapefile '{turbine_file}' does not exist.")
            return

        # Define the fields to be added if they don't exist
        fields_to_add = [
            {'name': 'SuppStruct', 'type': 'TEXT'},
            {'name': 'EC_2020', 'type': 'DOUBLE'},
            {'name': 'EC_2030', 'type': 'DOUBLE'},
            {'name': 'EC_2050', 'type': 'DOUBLE'},
            {'name': 'IC', 'type': 'DOUBLE'},
            {'name': 'CAP_2020', 'type': 'DOUBLE'},
            {'name': 'CAP_2030', 'type': 'DOUBLE'},
            {'name': 'CAP_2050', 'type': 'DOUBLE'},
            {'name': 'DEC', 'type': 'DOUBLE'}
        ]

        # Get the list of fields in the attribute table
        existing_fields = [field.name for field in arcpy.ListFields(turbine_file)]

        # Add fields if they do not exist
        for field in fields_to_add:
            if field['name'] not in existing_fields:
                arcpy.AddField_management(turbine_file, field['name'], field['type'])
                arcpy.AddMessage(f"Added field '{field['name']}' to the attribute table.")

        # Get the updated list of fields in the attribute table
        fields = [field.name for field in arcpy.ListFields(turbine_file)]

        # Update the attribute table with equipment, installation, and decommissioning costs
        with arcpy.da.UpdateCursor(turbine_file, fields) as cursor:
            for row in cursor:
                # Get field indices dynamically
                water_depth_index = fields.index("WaterDepth")
                capacity_index = fields.index("Capacity")

                # Get water depth and turbine capacity from the row
                water_depth = -row[water_depth_index]  # Invert the sign
                turbine_capacity = row[capacity_index]

                # Identify support structure and capitalize the first letter
                support_structure = determine_support_structure(water_depth).capitalize()
                row[fields.index("SuppStruct")] = support_structure

                # Update equipment costs for each year
                for year in ['2020', '2030', '2050']:
                    field_name_ec = f"EC_{year}"
                    field_name_cap = f"CAP_{year}"
                    if field_name_ec in fields and field_name_cap in fields:
                        # Calculate equipment costs
                        equi_costs = calc_equip_costs(water_depth, year, turbine_capacity)
                        row[fields.index(field_name_ec)] = round(equi_costs, 2)

                        # Calculate installation costs
                        inst_costs = calc_inst_deco_costs(water_depth, row[fields.index("Distance")], turbine_capacity, 'installation')
                        row[fields.index("IC")] = round(inst_costs, 2)

                        # Calculate and update capex for the current year
                        capex = equi_costs + inst_costs
                        row[fields.index(field_name_cap)] = round(capex, 2)

                # Update decommissioning costs (DEC)
                field_name_dec = "DEC"
                if field_name_dec in fields:
                    deco_costs = calc_inst_deco_costs(water_depth, row[fields.index("Distance")], turbine_capacity, 'decommissioning')
                    row[fields.index(field_name_dec)] = round(deco_costs, 2)

                # Update the row in the attribute table
                cursor.updateRow(row)

        arcpy.AddMessage(f"Equipment, installation, and decommissioning cost calculation for {turbine_file} completed.")

    except arcpy.ExecuteError as e:
        arcpy.AddError(f"Failed to update fields: {e}")
        arcpy.AddError(arcpy.GetMessages(2))  # Log more detailed error messages
    except Exception as e:
        arcpy.AddError(f"An unexpected error occurred: {e}")
        arcpy.AddError(arcpy.GetMessages(2))  # Log more detailed error messages

def check_updated_fields(turbine_file):
    """
    Check if the updated fields exist in the attribute table and if their values are nonzero.

    Parameters:
    - turbine_file (str): Path to the turbine shapefile.

    Returns:
    - bool: True if the fields exist and their values are nonzero and updated, False otherwise.
    """
    try:
        # Get the list of fields in the attribute table
        fields = [field.name for field in arcpy.ListFields(turbine_file)]

        # Check if the updated fields exist
        required_fields = ['SuppStruct', 'EC_2020', 'EC_2030', 'EC_2050', 'IC', 'CAP_2020', 'CAP_2030', 'CAP_2050', 'DEC']
        if not all(field in fields for field in required_fields):
            arcpy.AddWarning("Not all required fields are present in the attribute table.")
            return False

        # Check if the values of updated fields are nonzero
        with arcpy.da.SearchCursor(turbine_file, required_fields) as cursor:
            for row in cursor:
                for value in row:
                    if value == None or value == 0:
                        arcpy.AddWarning("Some updated fields have zero or None values.")
                        return False

        # All checks passed
        arcpy.AddMessage("All updated fields exist and have nonzero values in the attribute table.")
        return True

    except arcpy.ExecuteError as e:
        arcpy.AddError(f"Failed to check updated fields: {e}")
        return False
    except Exception as e:
        arcpy.AddError(f"An unexpected error occurred: {e}")
        return False

if __name__ == "__main__":
    # Get input parameters from ArcGIS tool parameters
    turbine_folder = arcpy.GetParameterAsText(0)

    try:
        # Set the workspace to the turbine folder
        arcpy.env.workspace = turbine_folder
        arcpy.AddMessage(f"Setting workspace to: {turbine_folder}")

        # List all shapefiles in the workspace
        shapefiles = arcpy.ListFeatureClasses("*.shp")

        # Check if there are any shapefiles in the folder
        if not shapefiles:
            arcpy.AddError(f"No shapefiles found in the specified folder: {turbine_folder}")
            exit()

        # Iterate through each shapefile and process it
        for input_shapefile_name in shapefiles:
            input_shapefile_path = os.path.join(turbine_folder, input_shapefile_name)
            arcpy.AddMessage(f"Processing input shapefile: {input_shapefile_path}")

            # Check if the shapefile exists
            if not arcpy.Exists(input_shapefile_path):
                arcpy.AddError(f"Input shapefile '{input_shapefile_path}' does not exist.")
                continue

            # Check if 'WaterDepth' and 'Distance' fields exist
            field_names = [field.name for field in arcpy.ListFields(input_shapefile_path)]
            required_fields = ['WaterDepth', 'Distance']

            if not all(field in field_names for field in required_fields):
                arcpy.AddError(f"Missing required fields ('WaterDepth' and/or 'Distance') in {input_shapefile_path}. Aborting.")
                continue

            # Update the attribute table with equipment, installation, and decommissioning costs
            update_fields(input_shapefile_path)

            # Check if updated fields exist and have nonzero values
            check_result = check_updated_fields(input_shapefile_path)
            if check_result:
                arcpy.AddMessage("All checks passed.")
            else:
                arcpy.AddWarning("One or more checks failed.")

    except arcpy.ExecuteError as e:
        arcpy.AddMessage(f"Failed to process shapefiles: {e}")
    except Exception as e:
        arcpy.AddMessage(f"An unexpected error occurred: {e}")
    finally:
        # Reset the workspace to None to avoid potential issues
        arcpy.env.workspace = None



