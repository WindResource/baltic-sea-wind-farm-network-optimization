import arcpy
import os
from typing import List, Tuple

def project_raster(input_raster: str, output_folder: str, output_spatial_ref: arcpy.SpatialReference) -> str:
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
        return ""
    except Exception as e:
        arcpy.AddError(f"An unexpected error occurred during raster projection: {e}")
        return ""

def calculate_water_depth(input_shapefile: str, bathy_raster: str) -> None:
    """
    Calculate water depth from a bathymetry raster and add it to the attribute table of a shapefile.

    Parameters:
    - input_shapefile (str): Path to the input shapefile.
    - bathy_raster (str): Path to the bathymetry raster file.

    Returns:
    - None
    """
    try:
        # Check if the input shapefile and raster exist
        if not arcpy.Exists(input_shapefile):
            arcpy.AddError(f"Input shapefile '{input_shapefile}' does not exist.")
            return
        if not arcpy.Exists(bathy_raster):
            arcpy.AddError(f"Bathymetry raster '{bathy_raster}' does not exist.")
            return

        # Add 'WaterDepth' field if it does not exist
        if not arcpy.ListFields(input_shapefile, "WaterDepth"):
            arcpy.AddField_management(input_shapefile, "WaterDepth", "DOUBLE")

        # Update the attribute table with water depth values
        with arcpy.da.UpdateCursor(input_shapefile, ["SHAPE@", "WaterDepth"]) as cursor:
            for row in cursor:
                # Get the centroid of the shape
                centroid = row[0].centroid

                # Get the water depth value from the raster
                water_depth = arcpy.GetCellValue_management(bathy_raster, f"{centroid.X} {centroid.Y}").getOutput(0)

                # Update the 'WaterDepth' field
                row[1] = float(water_depth) if water_depth != "NoData" else None
                cursor.updateRow(row)

        arcpy.AddMessage(f"Water depth calculation and attribute update for {input_shapefile} completed.")

    except arcpy.ExecuteError as e:
        arcpy.AddError(f"Failed to calculate water depth: {e}")
    except Exception as e:
        arcpy.AddError(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    # Get input parameters from ArcGIS tool parameters
    input_folder: str = arcpy.GetParameterAsText(0)
    bathy_raster: str = arcpy.GetParameterAsText(1)

    try:
        # Set the workspace to the input folder
        arcpy.env.workspace = input_folder
        arcpy.AddMessage(f"Setting workspace to: {input_folder}")

        # List all shapefiles in the workspace
        shapefiles: List[str] = arcpy.ListFeatureClasses("*.shp")

        # Iterate through each shapefile and process it
        for input_shapefile_name in shapefiles:
            input_shapefile_path: str = os.path.join(input_folder, input_shapefile_name)
            arcpy.AddMessage(f"Processing input shapefile: {input_shapefile_path}")

            # Check if the shapefile exists
            if not arcpy.Exists(input_shapefile_path):
                arcpy.AddError(f"Input shapefile '{input_shapefile_path}' does not exist.")
                continue

            # Project the bathymetry raster to the specified UTM coordinate system
            projected_raster_path: str = project_raster(bathy_raster, input_folder, arcpy.Describe(input_shapefile_path).spatialReference)
            if not projected_raster_path:
                arcpy.AddError("Failed to project the bathymetry raster.")
                continue

            # Calculate water depth and update attribute table
            calculate_water_depth(input_shapefile_path, projected_raster_path)

    except arcpy.ExecuteError as e:
        arcpy.AddMessage(f"Failed to process shapefiles: {e}")
    except Exception as e:
        arcpy.AddMessage(f"An unexpected error occurred: {e}")
    finally:
        # Reset the workspace to None to avoid potential issues
        arcpy.env.workspace = None
