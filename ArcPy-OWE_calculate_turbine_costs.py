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

def calc_equipment_costs(water_depth, year, turbine_capacity):
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

def update_equipment_costs(input_shapefile):
    """
    Update the attribute table of a shapefile with calculated equipment costs.

    Parameters:
    - input_shapefile (str): Path to the input shapefile.

    Returns:
    - None
    """
    try:
        # Check if the input shapefile exists
        if not arcpy.Exists(input_shapefile):
            arcpy.AddError(f"Input shapefile '{input_shapefile}' does not exist.")
            return

        # Define the fields to be added
        fields_to_add = [
            {'name': 'SuppStruct', 'type': 'TEXT'},
            {'name': 'EC_2020', 'type': 'DOUBLE'},
            {'name': 'EC_2030', 'type': 'DOUBLE'},
            {'name': 'EC_2050', 'type': 'DOUBLE'}
        ]

        # Get the list of fields in the attribute table
        existing_fields = [field.name for field in arcpy.ListFields(input_shapefile)]

        # Add fields if they do not exist
        for field in fields_to_add:
            if field['name'] not in existing_fields:
                arcpy.AddField_management(input_shapefile, field['name'], field['type'])
                arcpy.AddMessage(f"Added field '{field['name']}' to the attribute table.")

        # Get the updated list of fields in the attribute table
        fields = [field.name for field in arcpy.ListFields(input_shapefile)]

        # Update the attribute table with equipment costs and support structure
        with arcpy.da.UpdateCursor(input_shapefile, fields) as cursor:
            for row in cursor:
                # Check if 'SuppStruct' exists in the fields list
                if 'SuppStruct' in fields:
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
                    field_name = f"EC_{year}"
                    if field_name in fields:
                        equipment_costs = calc_equipment_costs(water_depth, year, turbine_capacity)
                        row[fields.index(field_name)] = equipment_costs

                # Update the row in the attribute table
                cursor.updateRow(row)

        arcpy.AddMessage(f"Equipment cost calculation and attribute update for {input_shapefile} completed.")

    except arcpy.ExecuteError as e:
        arcpy.AddError(f"Failed to update equipment costs: {e}")
    except Exception as e:
        arcpy.AddError(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    # Get input parameters from ArcGIS tool parameters
    input_folder = arcpy.GetParameterAsText(0)

    try:
        # Set the workspace to the input folder
        arcpy.env.workspace = input_folder
        arcpy.AddMessage(f"Setting workspace to: {input_folder}")

        # List all shapefiles in the workspace
        shapefiles = arcpy.ListFeatureClasses("*.shp")

        # Iterate through each shapefile and process it
        for input_shapefile_name in shapefiles:
            input_shapefile_path = os.path.join(input_folder, input_shapefile_name)
            arcpy.AddMessage(f"Processing input shapefile: {input_shapefile_path}")

            # Check if the shapefile exists
            if not arcpy.Exists(input_shapefile_path):
                arcpy.AddError(f"Input shapefile '{input_shapefile_path}' does not exist.")
                continue

            # Update the attribute table with equipment costs
            update_equipment_costs(input_shapefile_path)

    except arcpy.ExecuteError as e:
        arcpy.AddMessage(f"Failed to process shapefiles: {e}")
    except Exception as e:
        arcpy.AddMessage(f"An unexpected error occurred: {e}")
    finally:
        # Reset the workspace to None to avoid potential issues
        arcpy.env.workspace = None

