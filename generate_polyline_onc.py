import arcpy
import pandas as pd
import time
import os
import networkx as nx

def parse_wkt(wkt: str):
    """
    Parse WKT string to get the coordinates for polyline creation.
    """
    # Remove the 'SRID=4326;LINESTRING(' prefix and the closing ')'
    wkt = wkt.replace('SRID=4326;LINESTRING(', '').rstrip(')')
    # Split the coordinate pairs
    coordinates = wkt.split(',')
    # Convert to list of arcpy.Point objects
    points = [arcpy.Point(float(coord.split()[0]), float(coord.split()[1])) for coord in coordinates]
    return points

def get_max_voltage(voltage_str):
    """
    Get the maximum voltage from the voltage string. If the voltage string is empty or NaN, return 0.
    """
    if pd.isnull(voltage_str) or voltage_str == '':
        return 0
    try:
        if isinstance(voltage_str, (int, float)):
            return int(voltage_str)
        voltages = list(map(int, str(voltage_str).split(';')))
        return max(voltages)
    except ValueError:
        return 0

def build_graph_from_shapefile(shapefile):
    """
    Build a graph from the shapefile where nodes are substations and edges are polylines.
    """
    G = nx.Graph()
    with arcpy.da.SearchCursor(shapefile, ["SHAPE@", "Voltage", "MaxVoltage"]) as cursor:
        for row in cursor:
            line = row[0]
            voltage = row[1]
            max_voltage = row[2]
            start_point = (line.firstPoint.X, line.firstPoint.Y)
            end_point = (line.lastPoint.X, line.lastPoint.Y)
            length = line.length
            G.add_edge(start_point, end_point, weight=length, voltage=voltage, max_voltage=max_voltage, line=line)
    return G

def create_single_polyline_from_path(G, path, spatial_ref):
    """
    Create a single polyline from the given path in the graph.
    """
    points = []
    for i in range(len(path) - 1):
        edge_data = G.get_edge_data(path[i], path[i + 1])
        line = edge_data['line']
        points.extend(line.getPart(0))
    return arcpy.Polyline(arcpy.Array(points), spatial_ref)

def excel_to_polyline_shapefile(excel_file: str, output_folder: str) -> None:
    """
    Convert data from an Excel file to a polyline shapefile.

    Parameters:
        excel_file (str): Path to the Excel file.
        output_folder (str): Path to the output folder for the shapefile.
    """
    # Define the spatial reference for EPSG:4326 (WGS84)
    spatial_ref = arcpy.SpatialReference(4326)
    start_time = time.time()

    arcpy.AddMessage("Reading Excel data...")
    # Read Excel data using pandas
    df = pd.read_excel(excel_file)

    # Create a new shapefile to store the polyline features with EPSG:4326 spatial reference
    temp_shapefile = os.path.join(output_folder, "Temp_HighVoltage_Links.shp")
    if arcpy.Exists(temp_shapefile):
        arcpy.Delete_management(temp_shapefile)
    arcpy.management.CreateFeatureclass(output_folder, "Temp_HighVoltage_Links.shp", "POLYLINE", spatial_reference=spatial_ref)

    # Define fields to store attributes
    fields = [
        ("Voltage", "TEXT"),
        ("MaxVoltage", "LONG")
    ]
    arcpy.management.AddFields(temp_shapefile, fields)

    with arcpy.da.InsertCursor(temp_shapefile, ["SHAPE@", "Voltage", "MaxVoltage"]) as cursor:
        for row in df.itertuples():
            voltage = str(row.voltage) if pd.notnull(row.voltage) else '0'
            max_voltage = get_max_voltage(voltage)
            points = parse_wkt(row.wkt_srid_4326)
            polyline = arcpy.Polyline(arcpy.Array(points), spatial_ref)
            cursor.insertRow([polyline, voltage, max_voltage])

    arcpy.AddMessage("Performing spatial join...")
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map_object = aprx.activeMap
    onss_layer = next(layer for layer in map_object.listLayers() if layer.name.startswith("OnSS"))

    output_shapefile = os.path.join(output_folder, "HighVoltage_Links.shp")
    if arcpy.Exists(output_shapefile):
        arcpy.Delete_management(output_shapefile)
    
    arcpy.analysis.SpatialJoin(
        target_features=temp_shapefile,
        join_features=onss_layer,
        out_feature_class=output_shapefile,
        join_type="KEEP_COMMON",
        match_option="WITHIN_A_DISTANCE",
        search_radius="50 Kilometers",
        distance_field_name="DISTANCE"
    )

    arcpy.AddMessage("Building graph from shapefile...")
    G = build_graph_from_shapefile(output_shapefile)

    connection_shapefile = os.path.join(output_folder, "Substation_Connections.shp")
    if arcpy.Exists(connection_shapefile):
        arcpy.Delete_management(connection_shapefile)
    arcpy.management.CreateFeatureclass(output_folder, "Substation_Connections.shp", "POLYLINE", spatial_reference=spatial_ref)

    connection_fields = [
        ("Voltage", "TEXT"),
        ("MaxVoltage", "LONG")
    ]
    arcpy.management.AddFields(connection_shapefile, connection_fields)

    with arcpy.da.InsertCursor(connection_shapefile, ["SHAPE@", "Voltage", "MaxVoltage"]) as cursor:
        for connection in nx.connected_components(G):
            subgraph = G.subgraph(connection)
            for u, v, data in subgraph.edges(data=True):
                path = nx.shortest_path(subgraph, source=u, target=v, weight='weight')
                single_polyline = create_single_polyline_from_path(G, path, spatial_ref)
                cursor.insertRow([single_polyline, data['voltage'], data['max_voltage']])

    arcpy.AddMessage("Adding shapefile to the map...")
    map_object.addDataFromPath(connection_shapefile)

    arcpy.Delete_management(temp_shapefile)
    arcpy.Delete_management(output_shapefile)

    end_time = time.time()
    arcpy.AddMessage(f"Total processing time: {end_time - start_time} seconds")

if __name__ == "__main__":
    excel_file = "C:\\Users\\cflde\\Documents\\Graduation Project\\ArcGIS Pro\\BalticSea\\Data\\gridkit_europe\\gridkit_europe-highvoltage-links1.xlsx"
    output_folder = "C:\\Users\\cflde\\Documents\\Graduation Project\\ArcGIS Pro\\BalticSea\\Results\\highvoltage_links_folder"
    excel_to_polyline_shapefile(excel_file, output_folder)