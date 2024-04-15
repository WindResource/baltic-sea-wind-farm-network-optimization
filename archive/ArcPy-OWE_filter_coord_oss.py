import arcpy

def filter_OSSC(distance: float) -> None:
    """
    Filters out offshore substation coordinates (OSSC) points that are further than a user-specified distance from all 
    wind farm coordinates (WFC) points.

    Parameters:
    - distance: Maximum distance in kilometers.
    """

    try:
        # Get the current map
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        map = aprx.activeMap

        # Get 'Offshore Substation Coordinates' (OSSC) layer
        ossc_layer = None
        for layer in map.listLayers():
            if layer.name.startswith('OSSC'):
                ossc_layer = layer
                break
        
        if ossc_layer is None:
            arcpy.AddError("No layer starting with 'OSSC' found in the current map.")
            return

        arcpy.AddMessage(f"Processing layer: {ossc_layer.name}")

        # Get 'Wind Farm Coordinates' (WFC) layer
        wfc_layer = None
        for layer in map.listLayers():
            if layer.name.startswith('WFC'):
                wfc_layer = layer
                break
        
        if wfc_layer is None:
            arcpy.AddError("No layer starting with 'WFC' found in the current map.")
            return

        arcpy.AddMessage(f"Processing layer: {wfc_layer.name}")

        # Create a new layer to store filtered OSSC points
        filtered_ossc_layer = arcpy.management.CopyFeatures(ossc_layer, f"OSSC_filtered_{round(distance)}km")[0]
        
        # List to store WFC points
        wfc_points = []

        # Iterate over WFC points and store them in the list
        with arcpy.da.SearchCursor(wfc_layer, ["SHAPE@"]) as wfc_cursor:
            for wfc_row in wfc_cursor:
                wfc_points.append(wfc_row[0])

        # Iterate over OSSC points
        with arcpy.da.UpdateCursor(filtered_ossc_layer, ["SHAPE@"]) as ossc_cursor:
            for ossc_row in ossc_cursor:
                ossc_point = ossc_row[0]

                # Flag to check if the point is within the specified distance
                within_distance = False

                # Iterate over WFC points
                for wfc_point in wfc_points:
                    # Calculate the distance between OSSC and WFC points
                    distance_between_points = ossc_point.distanceTo(wfc_point)
                    # Convert distance to kilometers
                    distance_km = distance_between_points / 1000

                    if distance_km <= distance:
                        within_distance = True
                        break  # No need to check further, exit the loop
                
                # If the point is not within the specified distance from any WFC point, delete it
                if not within_distance:
                    ossc_cursor.deleteRow()
                    
        # Add the shapefile to the map
        map.addDataFromPath(filtered_ossc_layer)
        
        # Refresh the map view
        aprx.save()

        arcpy.AddMessage("Filtered 'OSSC' layer updated.")

    except arcpy.ExecuteError as e:
        arcpy.AddError(f"Failed to filter points: {e}")
    except Exception as e:
        arcpy.AddError(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    distance = float(arcpy.GetParameterAsText(0))  # Distance in kilometers

    # Call the function with user input
    filter_OSSC(distance)
