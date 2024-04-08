import arcpy
import numpy as np

def calculate_raster() -> None:
    """
    Calculate water depth from a projected bathymetry raster and add it to the attribute table of a offshore substation feature layer.

    Parameters:
    - projected_raster (Union[str, arcpy.Raster]): Either a path to the projected bathymetry raster or an arcpy Raster object.

    Returns:
    - None
    """
    
    # Get the current map
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map = aprx.activeMap

    # Get the first feature layer in the map that starts with 'WTC'
    input_layer = None
    for layer in map.listLayers():
        if layer.isFeatureLayer:
            if layer.name.startswith('OSSC'):
                coord_layer = layer
            if 'bathymetry' in layer.name:
                raster_layer = layer
                break
    
    if coord_layer is None:
        arcpy.AddError("No feature layer starting with 'OSSC' found in the current map.")
    if raster_layer is None:
        arcpy.AddError("No feature layer with 'bathymetry' found in the current map.")
        return

    arcpy.AddMessage(f"Processing layer: {input_layer.name}")
    
    # Convert raster to numpy array
    raster_array = arcpy.RasterToNumPyArray(raster_layer, nodata_to_value=np.nan)

    # Invert the sign of the water depth values
    raster_array = - raster_array
    
    # Get raster properties
    extent = raster_layer.extent
    cell_width = raster_layer.meanCellWidth
    cell_height = raster_layer.meanCellHeight

    # Add 'WaterDepth' field if it does not exist in the feature layer
    field_name = "WaterDepth"
    if field_name not in [field.name for field in arcpy.ListFields(input_layer)]:
        arcpy.management.AddField(input_layer, field_name, "DOUBLE")

    # Get the X and Y coordinates of all points in the input layer
    xy_points = np.array([[point.X, point.Y] for point, in arcpy.da.SearchCursor(input_layer, "SHAPE@XY")])

    # Calculate the column indices of the cells containing all points
    cell_columns = np.round((xy_points[:, 0] - extent.XMin) / cell_width).astype(int)

    # Calculate the row indices of the cells containing all points
    cell_rows = np.round((extent.YMax - xy_points[:, 1]) / cell_height).astype(int)

    # Get water depth values for all points using numpy indexing
    water_depths = raster_array[cell_rows, cell_columns]

    # Update the 'WaterDepth' field in the attribute table for all points
    with arcpy.da.UpdateCursor(input_layer, ["OID@", field_name]) as cursor:
        for i, row in enumerate(cursor):
            # Extract water depth value for the current point
            water_depth = water_depths[i]
            
            # Update the 'WaterDepth' field
            row[1] = float(water_depth) if not np.isnan(water_depth) else None
            cursor.updateRow(row)

    arcpy.AddMessage(f"Water depth calculation and attribute update for {input_layer.name} completed.")

# Check if the script is executed standalone or as a module
if __name__ == "__main__":
    calculate_raster()