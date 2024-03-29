import arcpy

def filter_OnSSC(distance: float) -> None:
    """
    This filter removes onshore substation coordinates (OnSSC) points that are further than a user-specified distance from the offshore wind farm area (OSSA) polygon feature.

    Parameters:
    - distance: Maximum distance in kilometers.
    """

    try:
        # Get the current map
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        map = aprx.activeMap

        # Get 'Onshore Substation Coordinates' (OnSSC) layer
        onssc_layer = None
        for layer in map.listLayers():
            if layer.name.startswith('OnSSC'):
                onssc_layer = layer
                break
        
        if onssc_layer is None:
            arcpy.AddError("No layer starting with 'OnSSC' found in the current map.")
            return

        arcpy.AddMessage(f"Processing layer: {onssc_layer.name}")

        # Get 'Offshore Wind Farm Area' (OSSA) layer
        ossa_layer = None
        for layer in map.listLayers():
            if layer.name.startswith('OSSA'):
                ossa_layer = layer
                break
        
        if ossa_layer is None:
            arcpy.AddError("No layer starting with 'OSSA' found in the current map.")
            return

        arcpy.AddMessage(f"Processing layer: {ossa_layer.name}")

        # Retrieve the single polygon feature representing the OSSA
        with arcpy.da.SearchCursor(ossa_layer, ["SHAPE@"]) as ossa_cursor:
            for ossa_row in ossa_cursor:
                ossa_polygon = ossa_row[0]
                break

        # Create a new layer to store filtered OnSSC points
        filtered_onssc_layer = arcpy.management.CopyFeatures(onssc_layer, f"OnSSC_filtered_{round(distance)}km")[0]

        # Iterate over OnSSC points
        with arcpy.da.UpdateCursor(filtered_onssc_layer, ["SHAPE@"]) as onssc_cursor:
            for onssc_row in onssc_cursor:
                onssc_point = onssc_row[0]

                # Calculate the distance from the point to the nearest boundary of the OSSA polygon
                distance_to_boundary = onssc_point.distanceTo(ossa_polygon.boundary())
                
                # Check if the distance to the boundary is within the specified distance
                if distance_to_boundary <= distance * 1000:
                    # Point is within the specified distance to the nearest boundary of the OSSA polygon
                    # No action needed, continue to the next point
                    pass
                else:
                    # Delete the point if it's further than the specified distance from the nearest boundary
                    onssc_cursor.deleteRow()

        # Add the shapefile to the map
        map.addDataFromPath(filtered_onssc_layer)
        
        # Refresh the map view
        aprx.save()

        arcpy.AddMessage("Filtered 'OnSSC' layer updated.")

    except arcpy.ExecuteError as e:
        arcpy.AddError(f"Failed to filter points: {e}")
    except Exception as e:
        arcpy.AddError(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    distance = float(arcpy.GetParameterAsText(0))  # Distance in kilometers

    # Call the function with user input
    filter_OnSSC(distance)
