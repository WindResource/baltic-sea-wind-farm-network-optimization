import arcpy
import os

def calculate_distance(point1, point2):
    """Calculate the geodetic distance between two point geometries."""
    return point1.distanceTo(point2)

def find_closest_substation(onshore_substation_file, windfarm_centroid):
    """Find the closest onshore substation to the windfarm centroid."""
    substation_cursor = arcpy.da.SearchCursor(onshore_substation_file, ["SHAPE@"])
    closest_substation = None
    closest_distance = float('inf')

    for substation_row in substation_cursor:
        substation_geometry = substation_row[0]
        distance = calculate_distance(windfarm_centroid, substation_geometry)

        if distance < closest_distance:
            closest_distance = distance
            closest_substation = substation_geometry

    del substation_cursor
    return closest_substation

def find_closest_turbine(turbine_folder, substation_geometry):
    """Find the wind turbine point feature closest to the substation."""
    arcpy.env.workspace = turbine_folder  # Set the workspace to the turbine folder
    closest_turbine = None
    closest_distance = float('inf')

    for turbine_file in arcpy.ListFiles("*.shp"):
        turbine_path = os.path.join(turbine_folder, turbine_file)
        turbine_cursor = arcpy.da.SearchCursor(turbine_path, ["SHAPE@"])

        for turbine_row in turbine_cursor:
            turbine_geometry = turbine_row[0]
            distance = calculate_distance(turbine_geometry, substation_geometry)

            if distance < closest_distance:
                closest_distance = distance
                closest_turbine = turbine_geometry

        del turbine_cursor

    return closest_turbine

def create_shapefile(array_connect_folder, array_connect_name, spatial_reference, point_features):
    """Create a shapefile containing point features."""
    arcpy.CreateFeatureclass_management(array_connect_folder, array_connect_name, "POINT", spatial_reference)
    output_path = os.path.join(array_connect_folder, array_connect_name)

    with arcpy.da.InsertCursor(output_path, ["SHAPE@"]) as cursor:
        for point_feature in point_features:
            cursor.insertRow([point_feature])

    arcpy.AddMessage("Shapefile created: {}".format(output_path))

    # Create layer from the created shapefile
    output_layer = os.path.join(array_connect_folder, array_connect_name + ".lyr")
    arcpy.MakeFeatureLayer_management(output_path, output_layer)

    # Use arcpy.mp to add the layer to the map
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map_object = aprx.activeMap

    # Add the layer to the map
    map_object.addLayer(output_layer)

if __name__ == "__main__":
    # Get user input parameters using arcpy.GetParameterAsText()
    windfarm_folder = arcpy.GetParameterAsText(0)
    turbine_folder = arcpy.GetParameterAsText(1)
    onshore_substation_file = arcpy.GetParameterAsText(2)
    array_coordinate_folder = arcpy.GetParameterAsText(3)

    # Iterate through all windfarm shapefiles in the specified folder
    arcpy.env.workspace = windfarm_folder
    for windfarm_file in arcpy.ListFiles("*.shp"):
        windfarm_path = os.path.join(windfarm_folder, windfarm_file)
        arcpy.AddMessage(f"Processing windfarm shapefile: {windfarm_path}")

        # Open the windfarm shapefile and get its centroid
        windfarm_cursor = arcpy.da.SearchCursor(windfarm_path, ["SHAPE@"])
        windfarm_row = next(windfarm_cursor, None)
        windfarm_centroid = windfarm_row[0].centroid
        del windfarm_cursor

        # Find the closest substation to the windfarm centroid
        closest_substation = find_closest_substation(onshore_substation_file, windfarm_centroid)

        # Find the wind turbine closest to the substation
        closest_turbine = find_closest_turbine(turbine_folder, closest_substation)

        # Create output file name and directory
        array_connect_name = os.path.basename(windfarm_file).replace("WFA_", "IAC_")
        array_connect_file = os.path.join(array_coordinate_folder, array_connect_name)

        # Create a shapefile containing all point features of the wind turbines closest to the substation
        create_shapefile(array_coordinate_folder, array_connect_name, closest_substation.spatialReference, [closest_turbine])
