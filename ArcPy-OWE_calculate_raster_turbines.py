import arcpy
import numpy as np

def calculate_raster() -> None:
    """
    Calculate water depth, Weibull-A, and Weibull-k values for a point from projected raster layers and add them to the
    attribute table of an offshore substation feature layer.

    Returns:
    - None
    """
    
    # Get the current map
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map_layer = aprx.activeMap

    # Initialize variables
    coord_layer = None
    raster_layer_lists = {'bathymetry': [], 'Weibull-A': [], 'Weibull-k': []}
    
    # Find layers
    for layer in map_layer.listLayers():
        if layer.isFeatureLayer and layer.name.startswith('WTC'):
            coord_layer = layer
        elif layer.isRasterLayer:
            for key in raster_layer_lists.keys():
                if key in layer.name:
                    raster_layer_lists[key].append(layer)
    
    # Error handling
    if coord_layer is None:
        arcpy.AddError("No feature layer starting with 'WTC' found in the current map.")
        return
    if not raster_layer_lists['bathymetry']:
        arcpy.AddError("No raster layers with 'bathymetry' found in the current map.")
        return
    if not raster_layer_lists['Weibull-A']:
        arcpy.AddError("No raster layers with 'Weibull-A' found in the current map.")
        return
    if not raster_layer_lists['Weibull-k']:
        arcpy.AddError("No raster layers with 'Weibull-k' found in the current map.")
        return

    # Deselect all currently selected features
    arcpy.SelectLayerByAttribute_management(coord_layer, "CLEAR_SELECTION")
    
    arcpy.AddMessage(f"Processing layer: {coord_layer.name}")
    
    # Convert raster layers to paths and numpy arrays
    raster_arrays_lists = {}
    raster_descs_lists = {}
    for key in raster_layer_lists.keys():
        raster_paths = [layer.dataSource for layer in raster_layer_lists[key]]
        raster_arrays_lists[key] = [arcpy.RasterToNumPyArray(path, nodata_to_value=np.nan) for path in raster_paths]
        raster_descs_lists[key] = [arcpy.Describe(layer) for layer in raster_layer_lists[key]]

    # Add fields if they do not exist in the feature layer
    fields_to_add = ["WaterDepth", "WeibullA", "WeibullK"]
    existing_fields = [field.name for field in arcpy.ListFields(coord_layer)]
    fields_to_add = [field for field in fields_to_add if field not in existing_fields]  # Filter fields that do not exist

    if fields_to_add:  # Only add fields if there are any to add
        field_infos = [[field, "DOUBLE"] for field in fields_to_add]
        arcpy.management.AddFields(coord_layer, field_infos)

    # Update the attribute table with water depth, Weibull-A, and Weibull-k values
    with arcpy.da.UpdateCursor(coord_layer, ["SHAPE@", "WaterDepth", "WeibullA", "WeibullK"]) as cursor:
        for row in cursor:
            # Get the point geometry
            point_geom = row[0]
            
            # Get the centroid of the point
            point = point_geom.centroid
            
            # Initialize values
            water_depth = np.nan
            weibull_a_value = np.nan
            weibull_k_value = np.nan

            # Iterate over raster layers
            for key in raster_arrays_lists.keys():
                for raster_array, desc in zip(raster_arrays_lists[key], raster_descs_lists[key]):
                    extent = desc.extent
                    cell_width = desc.meanCellWidth
                    cell_height = desc.meanCellHeight

                    # Calculate the column index of the cell containing the point
                    cell_column = round((point.X - extent.XMin) / cell_width)
                    
                    # Calculate the row index of the cell containing the point
                    cell_row = round((extent.YMax - point.Y) / cell_height)
                    
                    # Check if the calculated indices are within bounds
                    if 0 <= cell_row < raster_array.shape[0] and 0 <= cell_column < raster_array.shape[1]:
                        # Get the value from the numpy array
                        value = raster_array[cell_row, cell_column]

                        # Update the corresponding variable based on the key and update the attribute table with obtained values
                        if key == 'bathymetry':
                            water_depth = value
                            row[1] = float(-water_depth) if not np.isnan(water_depth) else row[1] or -999
                        elif key == 'Weibull-A':
                            weibull_a_value = value
                            row[2] = float(weibull_a_value) if not np.isnan(weibull_a_value) else row[2] or -999
                        elif key == 'Weibull-k':
                            weibull_k_value = value
                            row[3] = float(weibull_k_value) if not np.isnan(weibull_k_value) else row[3] or -999
                        cursor.updateRow(row)
                        
    arcpy.AddMessage("Water depth, Weibull-A, and Weibull-k calculation and attribute update completed.")

# Check if the script is executed standalone or as a module
if __name__ == "__main__":
    calculate_raster()