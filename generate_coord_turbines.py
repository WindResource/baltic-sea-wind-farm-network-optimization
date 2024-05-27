import arcpy
import os
import numpy as np

def create_wind_turbine_shapefile(output_folder: str) -> None:
    """
    Generates a point feature class for wind turbines based on the feature class in the current map.
    Each point represents a wind turbine, placed according to specified spacing, and includes attributes for identification and characteristics.

    Parameters:
    - output_folder: Path where the output shapefile will be saved.
    - turbine_capacity: Capacity of each wind turbine in megawatts (MW).
    - turbine_diameter: Diameter of each wind turbine in meters.
    - turbine_spacing: Desired spacing between turbines, in terms of turbine diameters.
    """

    turbine_capacity = 15 # MW
    turbine_diameter = 240 # m
    turbine_spacing = 7 # turbine diameters
    
    # Set the spatial reference to a UTM Zone using its Well-Known ID (WKID)
    utm33 = arcpy.SpatialReference(32633)  # Example: UTM Zone 33N
    wgs84 = arcpy.SpatialReference(4326)
    
    # Define a dictionary mapping country names to their corresponding two-letter country codes
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
    wfa_layer = None
    for layer in map.listLayers():
        if layer.name.startswith('WFA'):
            wfa_layer = layer
            break
    
    if wfa_layer is None:
        arcpy.AddError("No layer starting with 'WFA' found in the current map.")
        return
    
    # Deselect all currently selected features
    arcpy.SelectLayerByAttribute_management(wfa_layer, "CLEAR_SELECTION")
    
    arcpy.AddMessage(f"Processing layer: {wfa_layer.name}")

    # Modify output feature class name
    wtc_name = wfa_layer.name.replace('WFA', 'WTC') + ".shp"
    wtc_layer = os.path.join(output_folder, wtc_name)

    # Reproject input_layer to UTM
    wfa_layer = arcpy.management.Project(wfa_layer, os.path.join("in_memory\\input_layer"), utm33)[0]
    
    # Create one output feature class for all turbine points
    arcpy.CreateFeatureclass_management(output_folder, wtc_name, "POINT", spatial_reference=wgs84)

    # Add necessary fields to the output feature class
    arcpy.AddFields_management(wtc_layer, [
        ["Country", "TEXT", "", 10],
        ["ISO", "TEXT", "", 5],       
        ["Name", "TEXT", "", 80],
        ["WF_ID", "TEXT", "", 10],
        ["WT_ID", "TEXT", "", 10],
        ["Status", "TEXT", "", 10],
        ["Longitude", "DOUBLE"],
        ["Latitude", "DOUBLE"],
        ["Capacity", "DOUBLE"],
        ["Diameter", "DOUBLE"]
    ])

    # Prepare to insert new turbine point features
    insert_cursor_fields = ["SHAPE@", "Country", "ISO", "Name", "WF_ID", "WT_ID",  "Status", "Longitude", "Latitude", "Capacity", "Diameter"]
    insert_cursor = arcpy.da.InsertCursor(wtc_layer, insert_cursor_fields)
    wt_id = 0
    
    # Calculate the spacing in meters
    spacing = turbine_spacing * turbine_diameter
        
    # Generate points within the bounding box of the input layer's extent
    # considering the specified spacing using NumPy
    search_fields = ["SHAPE@", "OID@", "Country", "Name", "Status"]
    with arcpy.da.SearchCursor(wfa_layer, search_fields) as feature_cursor:
        for row, (shape, wf_id, country, name, status) in enumerate(feature_cursor):
            extent = shape.extent

            # Calculate number of points in x and y directions
            num_points_x = int((extent.width / (spacing)) + 1)
            num_points_y = int((extent.height / (spacing)) + 1)

            # Generate points within the extent directly
            x_coords = np.linspace(extent.XMin, extent.XMax, num_points_x)
            y_coords = np.linspace(extent.YMin, extent.YMax, num_points_y)

            # Create grid of x and y coordinates using meshgrid
            xx, yy = np.meshgrid(x_coords, y_coords)

            # Flatten the grid to create a 2D array of points
            points = np.column_stack((xx.flatten(), yy.flatten()))

            # Create point geometries for all points
            point_geometries = [arcpy.PointGeometry(arcpy.Point(*point), utm33) for point in points]

            # Check containment of all points using vectorized operation
            contains_mask = np.array([shape.contains(pt.centroid) for pt in point_geometries])

            # Filter points using the containment mask
            contained_points = points[contains_mask]

            # Project the contained points to WGS 1984 spatial reference
            projected_points = [arcpy.PointGeometry(arcpy.Point(*point), utm33).projectAs(wgs84) for point in contained_points]
            
            # Create rows to insert into feature class
            rows = []
            wt_id = 0
            for point in projected_points:
                iso = iso_mp.get(country, "XX")  # Default to "XX" if country code is not found
                wt_id += 1
                rows.append((
                    point,
                    country,
                    iso,
                    name,
                    wf_id,
                    wt_id,
                    status,
                    round(point.centroid.X, 6),
                    round(point.centroid.Y, 6),
                    turbine_capacity,
                    turbine_diameter
                ))

            # Insert rows in batches of 100
            batch_size = 100
            for i in range(0, len(rows), batch_size):
                
                batch_rows = rows[i:i + batch_size]
                for row in batch_rows:
                    insert_cursor.insertRow(row)
            
    # Add the generated shapefile to the current map
    map.addDataFromPath(wtc_layer)
    

if __name__ == "__main__":
    turbine_folder = "C:\\Users\\cflde\\Documents\\Graduation Project\\ArcGIS Pro\\BalticSea\\Results\\turbine_folder"

    # Ensure the output directory exists, create it if not
    if not os.path.exists(turbine_folder):
        os.makedirs(turbine_folder)

    # Call the main function with the parameters collected from the user
    create_wind_turbine_shapefile(turbine_folder)
    
    arcpy.AddMessage("Wind turbine point features creation complete.")
