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

        # Get the active map
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        map = aprx.listMaps()[0]

        # Find the bathymetry raster
        bathy_raster_path = None
        for lyr in map.listLayers():
            if lyr.name.lower().endswith("bathymetry") and lyr.isRasterLayer:
                bathy_raster_path = lyr.dataSource
                break

        if bathy_raster_path is None:
            arcpy.AddError("No bathymetry raster ending with 'bathymetry' found in the active map.")
            return None

        arcpy.AddMessage(f"Projecting bathymetry raster '{bathy_raster_path}' to UTM Zone 33N...")

        # Project the raster using arcpy.ProjectRaster_management
        projected_raster = arcpy.management.ProjectRaster(bathy_raster_path, "in_memory\\projected_raster", utm_spatial_ref).getOutput(0)

        arcpy.AddMessage("Raster projection completed.")

        return projected_raster

    except arcpy.ExecuteError as e:
        arcpy.AddError(f"Failed to project bathymetry raster: {e}")
        return None
    except Exception as e:
        arcpy.AddError(f"An unexpected error occurred during bathymetry raster projection: {e}")
        return None

def calculate_water_depth(projected_raster: arcpy.Raster) -> None:
    """
    Calculate water depth from a projected bathymetry raster and add it to the attribute table of a wind turbine feature layer.

    Parameters:
    - projected_raster (arcpy.Raster): Projected bathymetry raster.

    Returns:
    - None
    """
    try:
        # Get the active map
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        map = aprx.listMaps()[0]

        # Find the turbine layer
        turbine_layer_obj = None
        for lyr in map.listLayers():
            if lyr.name.startswith("WTC") and lyr.isFeatureLayer:
                turbine_layer_obj = lyr
                break

        if turbine_layer_obj is None:
            arcpy.AddError("No wind turbine feature layer starting with 'WTC' found in the active map.")
            return

        # Retrieve the extent of the turbine layer
        extent = turbine_layer_obj.getExtent()

        # Convert raster to numpy array
        raster_array = arcpy.RasterToNumPyArray(projected_raster, nodata_to_value=np.nan)

        # Get raster properties
        cell_width = projected_raster.meanCellWidth
        cell_height = projected_raster.meanCellHeight

        # Add 'WaterDepth' field if it does not exist in the turbine layer
        field_name = "WaterDepth"
        if field_name not in [field.name for field in turbine_layer_obj.fields]:
            arcpy.management.AddField(turbine_layer_obj, field_name, "DOUBLE")

        # Update the attribute table with water depth values
        with arcpy.da.UpdateCursor(turbine_layer_obj, ["SHAPE@", field_name]) as cursor:
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

        arcpy.AddMessage(f"Water depth calculation and attribute update for {turbine_layer_obj.name} completed.")

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
            calculate_water_depth(projected_raster)

    except arcpy.ExecuteError as e:
        arcpy.AddMessage(f"Failed to process wind turbine feature layer: {e}")
    except Exception as e:
        arcpy.AddMessage(f"An unexpected error occurred: {e}")
