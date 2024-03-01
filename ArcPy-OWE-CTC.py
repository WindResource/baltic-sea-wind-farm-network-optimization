import arcpy
import os
import numpy as np

def project_raster(input_raster, output_folder, output_spatial_ref):
    """
    Project the input raster to the specified coordinate system.

    Parameters:
    - input_raster (str): Path to the input raster file.
    - output_folder (str): Path to the output folder for the projected raster.
    - output_spatial_ref (arcpy.SpatialReference): Spatial reference of the desired coordinate system.

    Returns:
    - str: Path to the projected raster file.
    """
    try:
        # Get the name of the input raster without extension
        input_raster_name = os.path.splitext(os.path.basename(input_raster))[0]

        # Create the output raster path
        output_raster_path = os.path.join(output_folder, f"{input_raster_name}_projected.tif")

        arcpy.AddMessage(f"Projecting raster '{input_raster}' to {output_spatial_ref.name}...")

        # Project the raster
        arcpy.ProjectRaster_management(input_raster, output_raster_path, output_spatial_ref)

        arcpy.AddMessage(f"Raster projection completed. Output raster: {output_raster_path}")

        return output_raster_path

    except arcpy.ExecuteError as e:
        arcpy.AddError(f"Failed to project raster: {e}")
        return None
    except Exception as e:
        arcpy.AddError(f"An unexpected error occurred during raster projection: {e}")
        return None

def determine_support_structure(water_depth: float) -> str:
    """
    Determines the support structure type based on water depth.

    Parameters:
    - water_depth (float): Water depth in meters.

    Returns:
    - str: Support structure type ('monopile', 'jacket', 'floating', or 'default').
    """
    if 0 <= water_depth <= 25:
        return "monopile"
    elif 25 < water_depth <= 55:
        return "jacket"
    elif 55 < water_depth <= 200:
        return "floating"
    else:
        arcpy.AddWarning(f"Water depth {water_depth} does not fall within specified ranges for support structures. Assigning default support structure.")
        return "default"

def calc_equipment_costs(raster: arcpy.Raster, year: str, support_structure: str, turbine_capacity: float) -> float:
    """
    Calculates the equipment costs based on raster values, year, support structure, and turbine capacity.

    Parameters:
    - raster (arcpy.Raster): Raster representing water depth values.
    - year (str): Year for which equipment costs are calculated ('2020', '2030', or '2050').
    - support_structure (str): Support structure type ('monopile', 'jacket', 'floating', or 'default').
    - turbine_capacity (float): Rated power capacity of the wind turbine.

    Returns:
    - float: Calculated equipment costs.
    """
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
    wind_turbine_coeff = {
        '2020': 1500,
        '2030': 1200,
        '2050': 1000
    }

    key = (year, support_structure)
    c1, c2, c3 = support_structure_coeff[key]
    WT_rated_cost = wind_turbine_coeff[year]
    # Calculate equipment costs
    return turbine_capacity * ((c1 * (raster ** 2)) + (c2 * raster) + (c3 * 1000) + (WT_rated_cost))

def add_support_structure_and_costs_fields(bathy_raster_path: str, utm_zone: int):
    """
    Adds support structure and equipment costs fields to the attribute table of shapefiles in the workspace.

    Parameters:
    - bathy_raster_path (str): Path to the input bathymetry raster file.
    - utm_zone (int): UTM Zone number specified by the user.

    Returns:
    - None
    """
    try:
        arcpy.env.workspace = input_folder  # Set the workspace to the input_folder
        arcpy.AddMessage(f"Setting workspace to: {input_folder}")

        # Set the spatial reference to the specified UTM Zone
        utm_wkid = 32600 + utm_zone  # UTM Zone 33N is WKID 32633
        utm_spatial_ref = arcpy.SpatialReference(utm_wkid)

        # Project the bathymetry raster to the specified UTM Zone
        projected_raster_path = project_raster(bathy_raster_path, input_folder, utm_spatial_ref)
        if not projected_raster_path:
            arcpy.AddError("Failed to project the bathymetry raster.")
            return

        # List all shapefiles in the workspace
        shapefiles = arcpy.ListFeatureClasses("*.shp")

        # Check existing fields once before entering the loop
        fields_to_add = ["SuppStruct"] + [f"EC_{year}" for year in ['2020', '2030', '2050']]

        for input_shapefile_name in shapefiles:
            input_shapefile_path = os.path.join(input_folder, input_shapefile_name)
            arcpy.AddMessage(f"Processing input shapefile: {input_shapefile_path}")

            # Check if the input shapefile exists
            if not arcpy.Exists(input_shapefile_path):
                arcpy.AddError(f"Input shapefile '{input_shapefile_path}' does not exist.")
                continue

            # Invert the sign of raster values for water depth (bathymetry)
            inverted_raster = arcpy.sa.Times(projected_raster_path, -1)

            # Refresh the list of existing fields before checking if fields exist
            existing_fields = [field.name for field in arcpy.ListFields(input_shapefile_path)]

            # Add new fields only if they don't exist
            for field in fields_to_add:
                if field not in existing_fields:
                    arcpy.AddField_management(input_shapefile_path, field, "TEXT" if "SuppStruct" in field else "DOUBLE")

            # Refresh the list of existing fields after adding new ones
            existing_fields = [field.name for field in arcpy.ListFields(input_shapefile_path)]

            # Open the shapefile and update the new fields
            with arcpy.da.UpdateCursor(input_shapefile_path, ["SHAPE@", "TurbineID", "Capacity", "SuppStruct"] + [f"EC_{year}" for year in ['2020', '2030', '2050']]) as cursor:
                arcpy.AddMessage(f"Adding support structure and equipment costs for {input_shapefile_path}...")

                for row in cursor:
                    turbine_location, turbine_id, turbine_capacity, _, _, _, _ = row
                    x, y = turbine_location.centroid.X, turbine_location.centroid.Y
                    water_depth_at_location = arcpy.GetCellValue_management(inverted_raster, f"{x} {y}").getOutput(0)

                    # Skip processing if the value is 'NoData'
                    if water_depth_at_location == 'NoData':
                        arcpy.AddWarning(f"Water depth at location ({x}, {y}) is NoData. Skipping processing.")
                        continue

                    arcpy.AddMessage(f"Water Depth at Location ({x}, {y}): {water_depth_at_location}")

                    # Determine support structure type
                    support_structure = determine_support_structure(float(water_depth_at_location))
                    arcpy.AddMessage(f"Support Structure: {support_structure}")

                    # Calculate equipment costs for each year
                    for year in ['2020', '2030', '2050']:
                        equipment_costs = calc_equipment_costs(float(water_depth_at_location), year, support_structure, turbine_capacity)
                        row[4 + ['2020', '2030', '2050'].index(year)] = equipment_costs

                    # Update the SuppStruct and EquipCost fields
                    row[3] = support_structure
                    cursor.updateRow(row)

                arcpy.AddMessage(f"Support structure and equipment costs added to the attribute table of {input_shapefile_path} successfully.")

    except arcpy.ExecuteError as e:
        arcpy.AddMessage(f"Failed to add support structure and equipment costs: {e}")
    except Exception as e:
        arcpy.AddMessage(f"An unexpected error occurred: {e}")
    finally:
        arcpy.env.workspace = None  # Reset the workspace

if __name__ == "__main__":
    # Set your parameters (replace these with actual values)
    input_folder: str = arcpy.GetParameterAsText(0)
    bathy_raster_path: str = arcpy.GetParameterAsText(1)
    utm_zone: int = int(arcpy.GetParameterAsText(2))  # Assuming utm_zone is a user input parameter

    # Call the function to iterate over shapefiles in the input_folder and add support structure and equipment costs directly
    add_support_structure_and_costs_fields(bathy_raster_path, utm_zone)

