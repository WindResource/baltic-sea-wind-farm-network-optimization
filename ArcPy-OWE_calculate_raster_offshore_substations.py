import arcpy
import numpy as np

def project_raster() -> arcpy.Raster:
    """
    Project the bathymetry raster to the specified coordinate system.

    Returns:
    - arcpy.Raster: Projected raster.
    """
    try:
        # Set the spatial reference to UTM Zone 33N
        utm_wkid = 32633  # UTM Zone 33N
        utm_spatial_ref = arcpy.SpatialReference(utm_wkid)

        # Get the current map
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        map = aprx.activeMap

        # Get the first layer in the map that ends with 'bathymetry.tif'
        input_layer = None
        for layer in map.listLayers():
            if layer.name.endswith('bathymetry.tif'):
                input_layer = layer
                break

        if input_layer is None:
            arcpy.AddError("No bathymetry raster ending with 'bathymetry' found in the active map.")
            return None

        arcpy.AddMessage(f"Projecting bathymetry raster '{input_layer}' to UTM Zone 33N...")

        # Project the raster using arcpy.ProjectRaster_management
        result = arcpy.management.ProjectRaster(input_layer, "in_memory\\projected_raster", utm_spatial_ref)
        
        # Get the output raster from the result object
        projected_raster = result.getOutput(0)

        arcpy.AddMessage("Raster projection completed.")

        return projected_raster

    except arcpy.ExecuteError as e:
        arcpy.AddError(f"Failed to project bathymetry raster: {e}")
        return None
    except Exception as e:
        arcpy.AddError(f"An unexpected error occurred during bathymetry raster projection: {e}")
        return None

def calculate_raster(projected_raster: arcpy.Raster) -> None:
    """
    Calculate water depth from a projected bathymetry raster and add it to the attribute table of a offshore substation feature layer.

    Parameters:
    - projected_raster (Union[str, arcpy.Raster]): Either a path to the projected bathymetry raster or an arcpy Raster object.

    Returns:
    - None
    """
    try:
        # Ensure that projected_raster is an arcpy Raster object
        if isinstance(projected_raster, str):
            projected_raster = arcpy.Raster(projected_raster)

        # Get the current map
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        map = aprx.activeMap

        # Get the first feature layer in the map that starts with 'WTC'
        input_layer = None
        for layer in map.listLayers():
            if layer.isFeatureLayer:
                if layer.name.startswith('WTC'):
                    input_layer = layer
                    break
        
        if input_layer is None:
            arcpy.AddError("No feature layer starting with 'WTC' found in the current map.")
            return

        arcpy.AddMessage(f"Processing layer: {input_layer.name}")
        
        # Convert raster to numpy array
        raster_array = arcpy.RasterToNumPyArray(projected_raster, nodata_to_value=np.nan)

        # Get raster properties
        extent = projected_raster.extent
        cell_width = projected_raster.meanCellWidth
        cell_height = projected_raster.meanCellHeight

        # Add 'WaterDepth' field if it does not exist in the feature layer
        field_name = "WaterDepth"
        if field_name not in [field.name for field in arcpy.ListFields(input_layer)]:
            arcpy.management.AddField(input_layer, field_name, "DOUBLE")

        # Update the attribute table with water depth values
        with arcpy.da.UpdateCursor(input_layer, ["SHAPE@", field_name]) as cursor:
            for row in cursor:
                # Get the centroid of the shape
                centroid = row[0].centroid
                
                # Get the cell indices
                col = int((centroid.X - extent.XMin) / cell_width)
                row_index = int((extent.YMax - centroid.Y) / cell_height)
                
                # Get the water depth value from the numpy array
                water_depth = raster_array[row_index, col]
                
                # Update the 'WaterDepth' field
                row[1] = float(water_depth) if not np.isnan(water_depth) else None
                cursor.updateRow(row)

        arcpy.AddMessage(f"Water depth calculation and attribute update for {input_layer.name} completed.")

    except arcpy.ExecuteError as e:
        arcpy.AddError(f"Failed to calculate water depth: {e}")
    except Exception as e:
        arcpy.AddError(f"An unexpected error occurred: {e}")

# Check if the script is executed standalone or as a module
if __name__ == "__main__":
    try:
        # Project the bathymetry raster
        projected_raster = project_raster()

        if projected_raster:
            # Calculate water depth for the turbine layer using the projected raster
            calculate_raster(projected_raster)

    except arcpy.ExecuteError as e:
        arcpy.AddMessage(f"Failed to process wind turbine feature layer: {e}")
    except Exception as e:
        arcpy.AddMessage(f"An unexpected error occurred: {e}")
