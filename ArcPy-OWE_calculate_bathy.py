import arcpy
import os
from typing import List

def project_raster(input_raster: str, output_spatial_ref: arcpy.SpatialReference) -> arcpy.Raster:
    """
    Project the input raster to the specified coordinate system.

    Parameters:
    - input_raster (str): Path to the input raster file.
    - output_spatial_ref (arcpy.SpatialReference): Spatial reference of the desired coordinate system.

    Returns:
    - arcpy.Raster: Projected raster.
    """
    try:
        arcpy.AddMessage(f"Projecting raster '{input_raster}' to {output_spatial_ref.name}...")

        # Project the raster using arcpy.ProjectRaster_management
        projected_raster = arcpy.ProjectRaster_management(input_raster, "in_memory\\projected_raster", output_spatial_ref).getOutput(0)

        arcpy.AddMessage("Raster projection completed.")

        return projected_raster

    except arcpy.ExecuteError as e:
        arcpy.AddError(f"Failed to project raster: {e}")
        return None
    except Exception as e:
        arcpy.AddError(f"An unexpected error occurred during raster projection: {e}")
        return None

def calculate_water_depth(input_shapefile: str, projected_raster: arcpy.Raster) -> None:
    """
    Calculate water depth from a bathymetry raster and add it to the attribute table of a shapefile.

    Parameters:
    - input_shapefile (str): Path to the input shapefile.
    - projected_raster (arcpy.Raster): Projected bathymetry raster.

    Returns:
    - None
    """
    try:
        # Check if the input shapefile exists
        if not arcpy.Exists(input_shapefile):
            arcpy.AddError(f"Input shapefile '{input_shapefile}' does not exist.")
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
                water_depth = arcpy.GetCellValue_management(projected_raster, f"{centroid.X} {centroid.Y}").getOutput(0)

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

        # Project the bathymetry raster to the specified UTM coordinate system
        spatial_reference = arcpy.Describe(shapefiles[0]).spatialReference
        projected_raster: arcpy.Raster = project_raster(bathy_raster, spatial_reference)

        if projected_raster is None:
            arcpy.AddError("Failed to project the bathymetry raster.")
        else:
            # Iterate through each shapefile and process it
            for input_shapefile_name in shapefiles:
                input_shapefile_path: str = os.path.join(input_folder, input_shapefile_name)
                arcpy.AddMessage(f"Processing input shapefile: {input_shapefile_path}")

                # Check if the shapefile exists
                if not arcpy.Exists(input_shapefile_path):
                    arcpy.AddError(f"Input shapefile '{input_shapefile_path}' does not exist.")
                    continue

                # Calculate water depth and update attribute table
                calculate_water_depth(input_shapefile_path, projected_raster)

    except arcpy.ExecuteError as e:
        arcpy.AddMessage(f"Failed to process shapefiles: {e}")
    except Exception as e:
        arcpy.AddMessage(f"An unexpected error occurred: {e}")
    finally:
        # Reset the workspace to None to avoid potential issues
        arcpy.env.workspace = None
