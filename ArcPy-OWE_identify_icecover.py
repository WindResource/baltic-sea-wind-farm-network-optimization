import arcpy

def identify_within_polygon() -> None:
    # Get the current map
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map = aprx.activeMap

    # Get the first layer in the map that starts with 'WTC'
    wt_layer = next((layer for layer in map.listLayers() if layer.name.startswith('WTC')), None)
    ic_layer = next((layer for layer in map.listLayers() if layer.name.startswith('Ice')), None)

    if wt_layer is None:
        arcpy.AddError("No layer starting with 'WTC' found in the current map.")
    if ic_layer is None:
        arcpy.AddError("No layer starting with 'Ice' found in the current map.")    
        return

    # Deselect all currently selected features
    for layer in [wt_layer, ic_layer]:
        arcpy.SelectLayerByAttribute_management(layer, "CLEAR_SELECTION")
    
    arcpy.AddMessage(f"Processing layer: {wt_layer.name}")
    
    # Check if the "WithinIceCover" field already exists
    field_names = [field.name for field in arcpy.ListFields(wt_layer)]
    if "IceCover" not in field_names:
        # Add new field to the point feature layer to store results
        arcpy.management.AddField(wt_layer, "IceCover", "TEXT")

    # Perform a spatial join
    arcpy.analysis.SpatialJoin(wt_layer, ic_layer, "in_memory\\SpatialJoinResult", "JOIN_ONE_TO_ONE", "KEEP_ALL", "", "WITHIN")

    # Get the name of the unique identifier field of the input layer
    unique_id_field = arcpy.Describe(wt_layer).OIDFieldName

    # Update the "WithinIceCover" field based on the spatial join result
    with arcpy.da.UpdateCursor("in_memory\\SpatialJoinResult", ["IceCover", unique_id_field]) as cursor:
        for row in cursor:
            if row[0] is not None:
                row[0] = "Yes"
            else:
                row[0] = "No"
            cursor.updateRow(row)

    # Join the result back to the original point feature layer
    arcpy.management.JoinField(wt_layer, unique_id_field, "in_memory\\SpatialJoinResult", "TARGET_FID", "IceCover")

    arcpy.AddMessage("Process completed successfully.")

if __name__ == "__main__":
    identify_within_polygon()
