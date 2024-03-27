import arcpy
import numpy as np

def project_raster() -> list:
    """
    Project the specified rasters to the specified coordinate system.

    Returns:
    - list: List of projected raster objects.
    """
    try:
        # Set the spatial reference to UTM Zone 33N
        utm_wkid = 32633  # UTM Zone 33N
        utm_spatial_ref = arcpy.SpatialReference(utm_wkid)

        # Get the current map
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        map = aprx.activeMap

        # Raster substrings to be searched
        raster_substrings = ['bathymetry', 'Weibull-A_100m', 'Weibull-k_100m']
        projected_rasters = []

        for raster_substring in raster_substrings:
            # Get the raster layer in the map
            input_layer = None
            for layer in map.listLayers():
                if raster_substring in layer.name:
                    input_layer = layer
                    break

            if input_layer is None:
                arcpy.AddError(f"No raster containing '{raster_substring}' found in the active map.")
            else:
                arcpy.AddMessage(f"Projecting raster '{input_layer}' to UTM Zone 33N...")

                # Project the raster using arcpy.ProjectRaster_management
                result = arcpy.management.ProjectRaster(input_layer, f"in_memory\\projected_{raster_substring}", utm_spatial_ref)
                
                # Get the output raster from the result object
                projected_raster = result.getOutput(0)
                projected_rasters.append(projected_raster)

                arcpy.AddMessage(f"Raster projection for '{input_layer.name}' completed.")

        # Print out the list of projected raster objects
        arcpy.AddMessage("List of projected rasters:")
        for raster in projected_rasters:
            arcpy.AddMessage(raster)

        return projected_rasters

    except arcpy.ExecuteError as e:
        arcpy.AddError(f"Failed to project raster: {e}")
        return []
    except Exception as e:
        arcpy.AddError(f"An unexpected error occurred during raster projection: {e}")
        return []

def calculate_water_depth(projected_rasters: list) -> None:
    """
    Calculate water depth, Weibull-A, and Weibull-k from projected rasters and add them to the attribute table of a wind turbine feature layer.

    Parameters:
    - projected_rasters (list): List of projected raster objects or paths.

    Returns:
    - None
    """
    try:
        # Get the current map
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        map = aprx.activeMap

        # Get the first feature layer in the map that starts with 'WTC'
        input_layer = None
        for layer in map.listLayers():
            if layer.isFeatureLayer and layer.name.startswith('WTC'):
                input_layer = layer
                break
        
        if input_layer is None:
            arcpy.AddError("No feature layer starting with 'WTC' found in the current map.")
            return

        arcpy.AddMessage(f"Processing layer: {input_layer.name}")
        
        # Ensure that projected_rasters are arcpy Raster objects
        for i in range(len(projected_rasters)):
            if isinstance(projected_rasters[i], str):
                projected_rasters[i] = arcpy.Raster(projected_rasters[i])

        # Loop through the projected rasters
        for projected_raster in projected_rasters:
            # Convert raster to numpy array
            raster_array = arcpy.RasterToNumPyArray(projected_raster, nodata_to_value=np.nan)

            # Get raster properties
            extent = projected_raster.extent
            cell_width = projected_raster.meanCellWidth
            cell_height = projected_raster.meanCellHeight

            # Determine which attribute to update based on raster name
            if 'bathymetry' in projected_raster.name:
                field_name = "WaterDepth"
            elif 'Weibull-A' in projected_raster.name:
                field_name = "WeibullA"
            elif 'Weibull-k' in projected_raster.name:
                field_name = "WeibullK"
            else:
                arcpy.AddWarning(f"Raster '{projected_raster.name}' does not match expected naming convention. Skipping...")
                continue

            # Add field if it does not exist in the feature layer
            if field_name not in [field.name for field in arcpy.ListFields(input_layer)]:
                arcpy.management.AddField(input_layer, field_name, "DOUBLE")

            # Update the attribute table with values from the raster
            with arcpy.da.UpdateCursor(input_layer, ["SHAPE@", field_name]) as cursor:
                for row in cursor:
                    # Get the centroid of the shape
                    centroid = row[0].centroid
                    
                    # Get the cell indices
                    col = int((centroid.X - extent.XMin) / cell_width)
                    row_index = int((extent.YMax - centroid.Y) / cell_height)
                    
                    # Get the value from the numpy array
                    value = raster_array[row_index, col]
                    
                    # Update the field
                    row[1] = float(value) if not np.isnan(value) else None
                    cursor.updateRow(row)

            arcpy.AddMessage(f"{field_name} calculation and attribute update for {input_layer.name} completed.")

    except arcpy.ExecuteError as e:
        arcpy.AddError(f"Failed to calculate attributes: {e}")
    except Exception as e:
        arcpy.AddError(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    try:
        # Project the rasters
        projected_rasters = project_raster()

        if projected_rasters:
            # Calculate water depth for the turbine layer using the projected rasters
            calculate_water_depth(projected_rasters)

    except arcpy.ExecuteError as e:
        arcpy.AddMessage(f"Failed to process wind turbine feature layer: {e}")
    except Exception as e:
        arcpy.AddMessage(f"An unexpected error occurred: {e}")
