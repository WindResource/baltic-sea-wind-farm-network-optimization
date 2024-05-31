import arcpy
import numpy as np

def calculate_raster() -> None:
    """
    Calculate water depth from a projected bathymetry raster and add it to the attribute table of offshore substation feature layers.

    Returns:
    - None
    """
    
    # Get the current map
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map_layer = aprx.activeMap

    # Initialize variables
    coord_layers = []
    raster_layers = []
    
    # Find layers
    for layer in map_layer.listLayers():
        if layer.isFeatureLayer and (layer.name.startswith('OSSC') or layer.name.startswith('EHC')):
            coord_layers.append(layer)
        elif layer.isRasterLayer and 'bathymetry' in layer.name:
            raster_layers.append(layer)
    
    # Error handling
    if not coord_layers:
        arcpy.AddError("No feature layers starting with 'OSSC' or 'EHC' found in the current map.")
        return
    if not raster_layers:
        arcpy.AddError("No raster layers with 'bathymetry' found in the current map.")
        return

    # Deselect all currently selected features
    for coord_layer in coord_layers:
        arcpy.SelectLayerByAttribute_management(coord_layer, "CLEAR_SELECTION")
    
    arcpy.AddMessage(f"Processing layers: {[layer.name for layer in coord_layers]}")
    
    # Convert raster layers to paths
    raster_paths = [raster_layer.dataSource for raster_layer in raster_layers]
    
    # Convert rasters to numpy arrays
    raster_arrays = [arcpy.RasterToNumPyArray(raster_path, nodata_to_value=np.nan) for raster_path in raster_paths]
    
    # Get raster properties
    raster_descs = [arcpy.Describe(raster_layer) for raster_layer in raster_layers]
    extents = [raster_desc.extent for raster_desc in raster_descs]
    cell_widths = [raster_desc.meanCellWidth for raster_desc in raster_descs]
    cell_heights = [raster_desc.meanCellHeight for raster_desc in raster_descs]

    # Iterate over each coordinate layer
    for coord_layer in coord_layers:
        # Add 'WaterDepth' field if it does not exist in the feature layer
        field_name = "WaterDepth"
        if field_name not in [field.name for field in arcpy.ListFields(coord_layer)]:
            arcpy.management.AddField(coord_layer, field_name, "DOUBLE")

        # Update the attribute table with water depth values
        with arcpy.da.UpdateCursor(coord_layer, ["SHAPE@", field_name]) as cursor:
            for row in cursor:
                # Get the point geometry
                point_geom = row[0]
                
                # Get the centroid of the point
                point = point_geom.centroid
                
                # Iterate over each raster
                for raster_array, extent, cell_width, cell_height in zip(raster_arrays, extents, cell_widths, cell_heights):
                    # Calculate the column index of the cell containing the point
                    cell_column = round((point.X - extent.XMin) / cell_width)
                    
                    # Calculate the row index of the cell containing the point
                    cell_row = round((extent.YMax - point.Y) / cell_height)
                    
                    # Check if the calculated indices are within bounds
                    if cell_row >= 0 and cell_row < raster_array.shape[0] and cell_column >= 0 and cell_column < raster_array.shape[1]:
                        # Get the water depth value from the numpy array
                        water_depth = raster_array[cell_row, cell_column]
                        
                        # Update the 'WaterDepth' field in the attribute table
                        row[1] = float(max(0, - water_depth)) if not np.isnan(water_depth) else row[1] or 0
                        
                        if not np.isnan(water_depth): cursor.updateRow(row)

    arcpy.AddMessage("Water depth calculation and attribute update completed.")

# Check if the script is executed standalone or as a module
if __name__ == "__main__":
    calculate_raster()
