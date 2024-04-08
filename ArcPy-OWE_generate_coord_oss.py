import arcpy
import os
import numpy as np

def generate_offshore_substation_coordinates(output_folder: str, spacing: float) -> None:
    """
    Generates a point feature class for offshore substations based on the feature class in the current map.
    Each point represents a substation, placed according to specified spacing.

    Parameters:
    - output_folder: Path where the output shapefile will be saved.
    - spacing: Desired spacing between substations, in kilometers.
    """
    
    # Set the spatial reference to a UTM Zone using its Well-Known ID (WKID)
    utm33 = arcpy.SpatialReference(32633)
    wgs84 = arcpy.SpatialReference(4326)

    # Get the current map
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map = aprx.activeMap

    # Get the first layer in the map that starts with 'OSSA'
    input_layer = None
    for layer in map.listLayers():
        if layer.name.startswith('OSSA'):
            input_layer = layer
            break
    
    if input_layer is None:
        arcpy.AddError("No layer starting with 'OSSA' found in the current map.")
        return

    arcpy.AddMessage(f"Processing layer: {input_layer.name}")
    
    # Output feature class name based on the input layer
    output_feature_class_name = input_layer.name.replace('OSSA', 'OSSC') + ".shp"
    output_feature_class = os.path.join(output_folder, output_feature_class_name)
    
    # Reproject input_layer to UTM
    input_layer = arcpy.management.Project(input_layer, os.path.join("in_memory\\input_layer"), utm33)[0]

    # Create the output feature class for substations
    arcpy.CreateFeatureclass_management(output_folder, output_feature_class_name, "POINT", spatial_reference=wgs84)

    # Prepare to insert new substation point features
    insert_cursor_fields = ["SHAPE@", "StationID", "XCoord", "YCoord", "Territory", "ISO"]
    insert_cursor = arcpy.da.InsertCursor(output_feature_class, insert_cursor_fields)
    
    # Add fields to store substation attributes
    arcpy.AddFields_management(output_feature_class, [
        ["StationID", "TEXT"],
        ["XCoord", "DOUBLE"],
        ["YCoord", "DOUBLE"],
        ["Territory","TEXT"],
        ["ISO","TEXT"]
    ])

    # Initialize substation index counter
    substation_index = 1

    # Generate points within the bounding box of the input layer's extent
    # considering the specified spacing using NumPy
    with arcpy.da.SearchCursor(input_layer, ["SHAPE@", "TERRITORY1", "ISO_TER1"]) as cursor:
        for row in cursor:
            shape = row[0]
            territory = row[1]
            iso_territory = row[2]
            extent = shape.extent

            # Calculate number of points in x and y directions
            num_points_x = int((extent.width / (spacing * 1000)) + 1)
            num_points_y = int((extent.height / (spacing * 1000)) + 1)

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

            # Initialize substation index counter
            substation_index = 1

            # Create rows to insert into feature class
            rows = []
            for point in projected_points:
                rows.append((
                    point,
                    f"{iso_territory}_{substation_index}",
                    round(point.centroid.X, 3),
                    round(point.centroid.Y, 3),
                    territory,
                    iso_territory
                ))
                substation_index += 1  # Increment the substation index for each point

            # Create insert cursor outside of the loop
            with arcpy.da.InsertCursor(output_feature_class, insert_cursor_fields) as insert_cursor:
                # Insert rows in batches of 100
                batch_size = 100
                for i in range(0, len(rows), batch_size):
                    batch_rows = rows[i:i + batch_size]
                    for row in batch_rows:
                        insert_cursor.insertRow(row)

    # Add the generated shapefile to the current map
    map.addDataFromPath(output_feature_class)
        
if __name__ == "__main__":
    output_folder = str(arcpy.GetParameterAsText(0))  # Output folder path
    spacing = float(arcpy.GetParameterAsText(1))  # Spacing in kilometers

    # Ensure the output directory exists, create it if not
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Call the function with user inputs
    generate_offshore_substation_coordinates(output_folder, spacing)
