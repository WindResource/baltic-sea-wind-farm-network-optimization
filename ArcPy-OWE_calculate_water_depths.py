import arcpy
import os
from typing import List

def project_raster(bathy_file: str, output_spatial_ref: arcpy.SpatialReference) -> arcpy.Raster:
    """
    Project the bathymetry raster to the specified coordinate system.

    Parameters:
    - bathy_file (str): Path to the bathymetry raster file.
    - output_spatial_ref (arcpy.SpatialReference): Spatial reference of the desired coordinate system.

    Returns:
    - arcpy.Raster: Projected raster.
    """
    try:
        arcpy.AddMessage(f"Projecting bathymetry raster '{bathy_file}' to {output_spatial_ref.name}...")

        # Project the raster using arcpy.ProjectRaster_management
        projected_raster = arcpy.ProjectRaster_management(bathy_file, "in_memory\\projected_raster", output_spatial_ref).getOutput(0)

        arcpy.AddMessage("Raster projection completed.")

        return projected_raster

    except arcpy.ExecuteError as e:
        arcpy.AddError(f"Failed to project bathymetry raster: {e}")
        return None
    except Exception as e:
        arcpy.AddError(f"An unexpected error occurred during bathymetry raster projection: {e}")
        return None

def calculate_water_depth(turbine_file: str, projected_raster: arcpy.Raster) -> None:
    """
    Calculate water depth from a bathymetry raster and add it to the attribute table of a wind turbine coordinate file.

    Parameters:
    - turbine_file (str): Path to the wind turbine coordinate file.
    - projected_raster (arcpy.Raster): Projected bathymetry raster.

    Returns:
    - None
    """
    try:
        # Check if the input turbine file exists
        if not arcpy.Exists(turbine_file):
            arcpy.AddError(f"Wind turbine coordinate file '{turbine_file}' does not exist.")
            return

        # Add 'WaterDepth' field if it does not exist
        field_name = "WaterDepth"
        if field_name not in [field.name for field in arcpy.ListFields(turbine_file)]:
            arcpy.AddField_management(turbine_file, field_name, "DOUBLE")

        # Update the attribute table with water depth values
        with arcpy.da.UpdateCursor(turbine_file, ["SHAPE@", field_name]) as cursor:
            for row in cursor:
                # Get the centroid of the shape
                centroid = row[0].centroid

                # Get the water depth value from the raster
                water_depth = arcpy.GetCellValue_management(projected_raster, f"{centroid.X} {centroid.Y}").getOutput(0)

                # Update the 'WaterDepth' field
                row[1] = float(water_depth) if water_depth != "NoData" else None
                cursor.updateRow(row)

        arcpy.AddMessage(f"Water depth calculation and attribute update for {turbine_file} completed.")

    except arcpy.ExecuteError as e:
        arcpy.AddError(f"Failed to calculate water depth: {e}")
    except Exception as e:
        arcpy.AddError(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    # Get input parameters from ArcGIS tool parameters
    turbine_folder: str = arcpy.GetParameterAsText(0)
    bathy_file: str = arcpy.GetParameterAsText(1)

    try:
        # Set the workspace to the turbine folder
        arcpy.env.workspace = turbine_folder
        arcpy.AddMessage(f"Setting workspace to: {turbine_folder}")

        # List all turbine files in the workspace
        turbine_files: List[str] = arcpy.ListFeatureClasses("*.shp")

        # Project the bathymetry raster to the specified UTM coordinate system
        spatial_reference = arcpy.Describe(turbine_files[0]).spatialReference
        projected_raster: arcpy.Raster = project_raster(bathy_file, spatial_reference)

        if projected_raster is None:
            arcpy.AddError("Failed to project the bathymetry raster.")
        else:
            # Iterate through each turbine file and process it
            for turbine_file_name in turbine_files:
                turbine_file_path: str = os.path.join(turbine_folder, turbine_file_name)
                arcpy.AddMessage(f"Processing wind turbine coordinate file: {turbine_file_path}")

                # Check if the turbine file exists
                if not arcpy.Exists(turbine_file_path):
                    arcpy.AddError(f"Wind turbine coordinate file '{turbine_file_path}' does not exist.")
                    continue

                # Calculate water depth and update attribute table
                calculate_water_depth(turbine_file_path, projected_raster)

    except arcpy.ExecuteError as e:
        arcpy.AddMessage(f"Failed to process wind turbine coordinate files: {e}")
    except Exception as e:
        arcpy.AddMessage(f"An unexpected error occurred: {e}")
    finally:
        # Reset the workspace to None to avoid potential issues
        arcpy.env.workspace = None
