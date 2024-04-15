import arcpy
import os

def generate_windfarm_coordinates(output_folder: str) -> None:
    """
    Generates a point feature class for wind farm connection points based on the wind farm feature layer in the current map.
    Each point represents a wind farm connection point, the midpoint of the corresponding wind farm feature.

    Parameters:
    - output_folder: Path where the output shapefile will be saved.
    """
    # Set the spatial reference to a UTM Zone using its Well-Known ID (WKID)
    wgs84 = arcpy.SpatialReference(4326)
    
    # Dictionary mapping country names to ISO 3166-1 alpha-2 country codes for Baltic Sea countries
    iso_mp = {
        "Denmark": "DK",
        "Estonia": "EE",
        "Finland": "FI",
        "Germany": "DE",
        "Latvia": "LV",
        "Lithuania": "LT",
        "Poland": "PL",
        "Sweden": "SE"
    }

    # Get the current map
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map = aprx.activeMap

    # Get the first layer in the map that starts with 'WFA'
    wfa_layer = next((layer for layer in map.listLayers() if layer.name.startswith('WFA')), None)
    if wfa_layer is None:
        arcpy.AddError("No layer starting with 'WFA' found in the current map.")
        return

    # Deselect all currently selected features
    arcpy.SelectLayerByAttribute_management(wfa_layer, "CLEAR_SELECTION")
    
    arcpy.AddMessage(f"Processing layer: {wfa_layer.name}")

    # Modify output feature class name, WFC is wind farm connection
    wfc_name = wfa_layer.name.replace('WFA', 'WFC') + ".shp"
    wfc_layer = os.path.join(output_folder, wfc_name)

    # Create one output feature class for all wind farm connection point
    arcpy.CreateFeatureclass_management(output_folder, wfc_name, "POINT", spatial_reference=wgs84)

    # Add necessary fields to the output feature class
    arcpy.AddFields_management(wfc_layer, [
        ["Country", "TEXT", "", 10],
        ["ISO", "TEXT", "", "", 50, "Country"],
        ["WF_ID", "TEXT", "", "", 50, "Wind Farm ID"],
        ["Longitude", "DOUBLE"],
        ["Latitude", "DOUBLE"],
    ])

    # Prepare to insert new connection point features
    insert_cursor_fields = ["SHAPE@", "Country", "ISO", "WF_ID", "Longitude", "Latitude"]
    insert_cursor = arcpy.da.InsertCursor(wfc_layer, insert_cursor_fields)

    # Iterate through each feature in the input layer
    search_fields = ["SHAPE@", "OID@", "country"]  # We only need the geometry and object ID
    with arcpy.da.SearchCursor(wfa_layer, search_fields) as feature_cursor:
        for shape, farm_id, country in feature_cursor:
            # Calculate the midpoint of the feature
            midpoint = shape.centroid
            
            # Get the ISO code for the country from the dictionary
            iso_code = iso_mp.get(country, None)
            
            # Extract longitude and latitude from the midpoint
            longitude, latitude = midpoint.X, midpoint.Y
            
            # Insert the new connection point with its attributes
            farm_id += 1
            row_values = (midpoint, country, iso_code, farm_id, longitude, latitude)
            insert_cursor.insertRow(row_values)

    
    # Add the generated shapefile to the current map
    map.addDataFromPath(wfc_layer)

    arcpy.AddMessage("Wind farm connection point features creation complete.")

# Test the function
if __name__ == "__main__":
    # Example output folder
    output_folder = arcpy.GetParameterAsText(0)  # The folder where the output shapefile will be saved

    # Ensure the output directory exists, create it if not
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Call the main function with the parameter collected from the user
    generate_windfarm_coordinates(output_folder)
