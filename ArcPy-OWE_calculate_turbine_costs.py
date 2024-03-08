import arcpy

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

        # Add 'EC_2020', 'EC_2030', and 'EC_2050' fields if they do not exist
        for year in ['2020', '2030', '2050']:
            field_name = f"EC_{year}"
            if not arcpy.ListFields(input_shapefile, field_name):
                arcpy.AddField_management(input_shapefile, field_name, "DOUBLE")

        # Update the attribute table with equipment costs
        with arcpy.da.UpdateCursor(input_shapefile, ["WaterDepth", "EC_2020", "EC_2030", "EC_2050", "TurbineID", "Capacity"]) as cursor:
            for row in cursor:
                # Get water depth, turbine ID, and turbine capacity from the row
                water_depth = row[0]
                turbine_id = row[4]
                turbine_capacity = row[5]

                # Update equipment costs for each year
                for year in ['2020', '2030', '2050']:
                    field_name = f"EC_{year}"
                    equipment_costs = calc_equipment_costs(water_depth, year, turbine_capacity)
                    row[cursor.fields.index(field_name)] = equipment_costs

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
            input_shapefile_path = arcpy.ValidateTableName(input_shapefile_name, input_folder)
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
