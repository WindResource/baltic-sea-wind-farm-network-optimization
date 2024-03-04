import arcpy
import os
from typing import List, Tuple

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

        # Project the raster using arcpy.ProjectRaster_management
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

    key = (year, support_structure)
    c1, c2, c3 = support_structure_coeff[key]
    WT_rated_cost = wind_turbine_coeff[year]

    # Calculate equipment costs using the provided formula
    return turbine_capacity * ((c1 * (raster ** 2)) + (c2 * raster) + (c3 * 1000) + (WT_rated_cost))

def process_shapefiles(input_folder: str, utm_zone: int, bathy_raster_path: str) -> List[Tuple[str, arcpy.Raster]]:
    """
    Process shapefiles in the workspace.

    Parameters:
    - input_folder (str): Path to the input folder containing shapefiles.
    - utm_zone (int): UTM Zone number specified by the user.
    - bathy_raster_path (str): Path to the input bathymetry raster file.

    Returns:
    - List[Tuple[str, arcpy.Raster]]: List of processed shapefiles with their paths and corresponding inverted bathymetry rasters.
    """
    try:
        # Set the workspace to the input folder
        arcpy.env.workspace = input_folder
        arcpy.AddMessage(f"Setting workspace to: {input_folder}")

        # Determine the UTM spatial reference based on the specified UTM zone
        utm_wkid = 32600 + utm_zone
        utm_spatial_ref = arcpy.SpatialReference(utm_wkid)

        # Project the bathymetry raster to the specified UTM coordinate system
        projected_raster_path = project_raster(bathy_raster_path, input_folder, utm_spatial_ref)
        if not projected_raster_path:
            arcpy.AddError("Failed to project the bathymetry raster.")
            return []

        # List all shapefiles in the workspace
        shapefiles = arcpy.ListFeatureClasses("*.shp")
        processed_shapefiles: List[Tuple[str, arcpy.Raster]] = []

        # Iterate through each shapefile and process it
        for input_shapefile_name in shapefiles:
            input_shapefile_path = os.path.join(input_folder, input_shapefile_name)
            arcpy.AddMessage(f"Processing input shapefile: {input_shapefile_path}")

            # Check if the shapefile exists
            if not arcpy.Exists(input_shapefile_path):
                arcpy.AddError(f"Input shapefile '{input_shapefile_path}' does not exist.")
                continue

            # Create an inverted bathymetry raster for the shapefile
            inverted_raster = arcpy.sa.Times(projected_raster_path, -1)
            processed_shapefiles.append((input_shapefile_path, inverted_raster))

        return processed_shapefiles

    except arcpy.ExecuteError as e:
        arcpy.AddMessage(f"Failed to process shapefiles: {e}")
        return []
    except Exception as e:
        arcpy.AddMessage(f"An unexpected error occurred: {e}")
        return []
    finally:
        # Reset the workspace to None to avoid potential issues
        arcpy.env.workspace = None

def update_attribute_table(input_shapefile_path: str, inverted_raster: arcpy.Raster):
    """
    Update the attribute table of a shapefile.

    Parameters:
    - input_shapefile_path (str): Path to the input shapefile.
    - inverted_raster (arcpy.Raster): Inverted bathymetry raster.

    Returns:
    - None
    """
    try:
        # Define the fields to add to the attribute table
        fields_to_add = [
            ("SuppStruct", "TEXT"),
            ("WaterDepth", "DOUBLE"),
            ("EC_2020", "DOUBLE"),
            ("EC_2030", "DOUBLE"),
            ("EC_2050", "DOUBLE")
        ]

        # Add the required fields if they do not already exist
        for field, field_type in fields_to_add:
            if not arcpy.ListFields(input_shapefile_path, field):
                arcpy.AddField_management(input_shapefile_path, field, field_type)

        # Update the attribute table using an update cursor
        with arcpy.da.UpdateCursor(
            input_shapefile_path, ["SHAPE@", "TurbineID", "Capacity", "SuppStruct", "WaterDepth", "EC_2020", "EC_2030", "EC_2050"]
        ) as cursor:
            arcpy.AddMessage(f"Processing shapefile: {input_shapefile_path}...")

            # Iterate through each row in the attribute table
            for row in cursor:
                # Check if there are enough fields in the row
                if len(row) < 5:
                    arcpy.AddWarning(f"Insufficient number of fields retrieved. Skipping row update.")
                    continue

                # Extract relevant information from the row
                turbine_location, turbine_id, turbine_capacity, *_ = row[:3]

                # Get the coordinates of the turbine location
                x, y = turbine_location.centroid.X, turbine_location.centroid.Y

                # Display a message indicating the start of processing for each wind turbine
                arcpy.AddMessage(f"Processing Wind Turbine {turbine_id} at Location ({x}, {y})...")

                # Get the water depth at the turbine location from the inverted raster
                water_depth_at_location = arcpy.GetCellValue_management(inverted_raster, f"{x} {y}").getOutput(0)

                # Check if water depth is NoData, and skip processing if it is
                if water_depth_at_location == 'NoData':
                    arcpy.AddWarning(f"Water depth at location ({x}, {y}) is NoData. Skipping processing.")
                    continue

                # Determine the support structure type based on water depth
                support_structure = determine_support_structure(float(water_depth_at_location))

                # Update the equipment costs for each year
                for year_index, year in enumerate(['2020', '2030', '2050']):
                    equipment_costs = calc_equipment_costs(float(water_depth_at_location), year, support_structure, turbine_capacity)
                    row[5 + year_index] = equipment_costs

                # Update the support structure and water depth fields in the attribute table
                row[3] = support_structure
                row[4] = float(water_depth_at_location)  # Add water depth to the attribute table
                cursor.updateRow(row)

                # Display a message indicating the end of processing for each wind turbine
                arcpy.AddMessage(f"Processing for Wind Turbine {turbine_id} completed.")

            # Display a message indicating the end of processing for the entire shapefile
            arcpy.AddMessage(f"Processing of shapefile {input_shapefile_path} completed successfully.")

    except arcpy.ExecuteError as e:
        arcpy.AddMessage(f"Failed to update attribute table: {e}")
    except Exception as e:
        arcpy.AddMessage(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    # Get input parameters from ArcGIS tool parameters
    input_folder: str = arcpy.GetParameterAsText(0)
    bathy_raster_path: str = arcpy.GetParameterAsText(1)
    utm_zone: int = int(arcpy.GetParameterAsText(2))

    # Process shapefiles in the specified input folder
    processed_shapefiles = process_shapefiles(input_folder, utm_zone, bathy_raster_path)

    # Iterate through each processed shapefile and update its attribute table
    for shapefile_info in processed_shapefiles:
        input_shapefile_path, inverted_raster = shapefile_info
        update_attribute_table(input_shapefile_path, inverted_raster)


