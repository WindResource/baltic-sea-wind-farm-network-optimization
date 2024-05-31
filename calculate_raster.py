import arcpy
import numpy as np

def calculate_raster() -> None:
    """
    Calculate water depth, Weibull-A, and Weibull-k values for a point from projected raster layers and add them to the
    attribute table of offshore substation feature layers.

    Returns:
    - None
    """
    
    # Get the current map
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map_layer = aprx.activeMap

    # Initialize variables
    wtc_layers = []
    ossc_layers = []
    ehc_layers = []
    raster_layer_lists = {'bathymetry': [], 'Weibull-A': [], 'Weibull-k': []}
    
    # Find layers
    for layer in map_layer.listLayers():
        if layer.isFeatureLayer:
            if layer.name.startswith('WTC'):
                wtc_layers.append(layer)
            elif layer.name.startswith('OSSC'):
                ossc_layers.append(layer)
            elif layer.name.startswith('EHC'):
                ehc_layers.append(layer)
        elif layer.isRasterLayer:
            for key in raster_layer_lists.keys():
                if key in layer.name:
                    raster_layer_lists[key].append(layer)
    
    # Error handling
    if not wtc_layers:
        arcpy.AddError("No feature layers starting with 'WTC' found in the current map.")
        return
    if not ossc_layers:
        arcpy.AddError("No feature layers starting with 'OSSC' found in the current map.")
        return
    if not ehc_layers:
        arcpy.AddError("No feature layers starting with 'EHC' found in the current map.")
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
    for layer in wtc_layers + ossc_layers + ehc_layers:
        arcpy.SelectLayerByAttribute_management(layer, "CLEAR_SELECTION")
    
    arcpy.AddMessage(f"Processing WTC layers: {[layer.name for layer in wtc_layers]}")
    arcpy.AddMessage(f"Processing OSSC layers: {[layer.name for layer in ossc_layers]}")
    arcpy.AddMessage(f"Processing EHC layers: {[layer.name for layer in ehc_layers]}")
    
    # Convert raster layers to paths and numpy arrays
    raster_arrays_lists = {}
    raster_descs_lists = {}
    for key in raster_layer_lists.keys():
        raster_paths = [layer.dataSource for layer in raster_layer_lists[key]]
        raster_arrays_lists[key] = [arcpy.RasterToNumPyArray(path, nodata_to_value=np.nan) for path in raster_paths]
        raster_descs_lists[key] = [arcpy.Describe(layer) for layer in raster_layer_lists[key]]

    def update_attributes(layer, update_weibull=False):
        """ Helper function to update attributes for a given layer. """
        # Add fields if they do not exist in the feature layer
        fields_to_add = ["WaterDepth"]
        if update_weibull:
            fields_to_add.extend(["WeibullA", "WeibullK"])
        
        existing_fields = [field.name for field in arcpy.ListFields(layer)]
        fields_to_add = [field for field in fields_to_add if field not in existing_fields]  # Filter fields that do not exist

        if fields_to_add:  # Only add fields if there are any to add
            field_infos = [[field, "DOUBLE"] for field in fields_to_add]
            arcpy.management.AddFields(layer, field_infos)

        field_names = ["SHAPE@", "WaterDepth"]
        if update_weibull:
            field_names.extend(["WeibullA", "WeibullK"])

        # Update the attribute table with water depth, Weibull-A, and Weibull-k values
        with arcpy.da.UpdateCursor(layer, field_names) as cursor:
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
                                row[1] = float(max(0 , - water_depth)) if not np.isnan(water_depth) else row[1] or 0
                            elif key == 'Weibull-A' and update_weibull:
                                weibull_a_value = value
                                row[2] = float(round(weibull_a_value, 3)) if not np.isnan(weibull_a_value) else row[2] or 0
                            elif key == 'Weibull-k' and update_weibull:
                                weibull_k_value = value
                                row[3] = float(round(weibull_k_value, 3)) if not np.isnan(weibull_k_value) else row[3] or 0
                            
                            if not np.isnan(value): cursor.updateRow(row)

    # Update attributes for each layer
    for layer in wtc_layers:
        update_attributes(layer, update_weibull=True)
    
    for layer in ossc_layers + ehc_layers:
        update_attributes(layer, update_weibull=False)

    # Deselect all currently selected features
    for layer in wtc_layers + ossc_layers + ehc_layers:
        arcpy.SelectLayerByAttribute_management(layer, "CLEAR_SELECTION")

    arcpy.AddMessage("Water depth, Weibull-A, and Weibull-k calculation and attribute update completed.")

# Check if the script is executed standalone or as a module
if __name__ == "__main__":
    calculate_raster()