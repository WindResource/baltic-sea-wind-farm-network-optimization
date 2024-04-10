import arcpy

def identify_icecover() -> None:
    """
    Identifies whether wind turbine coordinates ("WTC") are located within areas of maximum ice extent ("Ice"). 
    Updates an "IceCover" field in the wind turbine layer accordingly.

    Returns:
        None
    """
    
    # Get the current map
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map = aprx.activeMap

    # Get the first layer in the map that starts with 'WTC' (points) and 'Ice' (polygon)
    wt_layer = next((layer for layer in map.listLayers() if layer.name.startswith('WTC')), None)
    ic_layer = next((layer for layer in map.listLayers() if layer.name.startswith('Ice')), None)

    if wt_layer is None:
        arcpy.AddError("No layer starting with 'WTC' found in the current map.")
        return
    if ic_layer is None:
        arcpy.AddError("No layer starting with 'Ice' found in the current map.")
        return

    # Deselect all currently selected features
    for layer in [wt_layer, ic_layer]:
        arcpy.SelectLayerByAttribute_management(layer, "CLEAR_SELECTION")
    
    arcpy.AddMessage(f"Processing layer: {wt_layer.name}")

    # Check if the "IceCover" field already exists
    field_names = [field.name for field in arcpy.ListFields(wt_layer)]
    if "IceCover" not in field_names:
        # Add new field to store ice cover information
        arcpy.AddField_management(wt_layer, "IceCover", "TEXT", field_length = 5)

    # Set "IceCover" field to "No" for all features
    arcpy.CalculateField_management(wt_layer, "IceCover", "'No'", "PYTHON3")

    # Select points within the ice polygon
    arcpy.SelectLayerByLocation_management(wt_layer, "WITHIN", ic_layer)

    # Update the "IceCover" field for selected points
    arcpy.CalculateField_management(wt_layer, "IceCover", "'Yes'", "PYTHON3")

    # Clear selection
    arcpy.SelectLayerByAttribute_management(wt_layer, "CLEAR_SELECTION")

    arcpy.AddMessage("Process completed successfully.")

if __name__ == "__main__":
    identify_icecover()
