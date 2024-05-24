import arcpy
import os

def generate_turbine_areas(windfarm_folder: str):
    """
    Create a single shapefile for selected countries and status based on the input shapefile, utilizing in-memory workspaces.
    The created shapefile is added to the current map in ArcGIS Pro.

    Parameters:
    - windfarm_folder (str): Path to the output folder where the shapefile will be saved.

    Returns:
    - str: Path to the created shapefile.
    """
    # Default to all Baltic Sea countries if countries_input is None or empty
    countries = ['Denmark', 'Estonia', 'Finland', 'Germany', 'Latvia', 'Lithuania', 'Poland', 'Sweden']
    status = "Planned"

    # Get the current map
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map = aprx.activeMap

    # Get the first layer in the map that starts with 'windfarmspoly'
    wf_layer = next((layer for layer in map.listLayers() if layer.name.startswith('windfarmspoly')), None)
    if wf_layer is None:
        arcpy.AddError("No layer starting with 'windfarmspoly' found in the current map.")
        return

    arcpy.AddMessage(f"Processing layer: {wf_layer.name}")

    # Processing for EEZ
    arcpy.management.SelectLayerByAttribute(wf_layer, "NEW_SELECTION", f"country IN {tuple(countries)} AND status = '{status}'")
    arcpy.management.CopyFeatures(wf_layer, "in_memory\\selected_wf_layer")

    # Iterate through features and select those that meet the longitude condition
    with arcpy.da.UpdateCursor("in_memory\\selected_wf_layer", ['SHAPE@X']) as cursor:
        for row in cursor:
            if row[0] < 9:  # Check if longitude is greater than 9
                cursor.deleteRow()

    # Define the output shapefile path
    output_shapefile = os.path.join(windfarm_folder, f"WFA_BalticSea_{status}.shp")

    # Copy the selected features to a new shapefile
    arcpy.management.CopyFeatures("in_memory\\selected_wf_layer", "in_memory\\non_overlapping_wf_layer")

    # Add an area field and calculate the area for each feature
    arcpy.management.AddField("in_memory\\non_overlapping_wf_layer", "AREA", "DOUBLE")
    arcpy.management.CalculateGeometryAttributes("in_memory\\non_overlapping_wf_layer", [["AREA", "AREA_GEODESIC"]])

    # Make a feature layer for selection
    arcpy.management.MakeFeatureLayer("in_memory\\non_overlapping_wf_layer", "layer_to_check")

    delete_oids = set()
    all_polygons = [row for row in arcpy.da.SearchCursor("layer_to_check", ['OID@', 'SHAPE@', 'AREA'])]

    for i, (oid1, shape1, area1) in enumerate(all_polygons):
        arcpy.AddMessage(f"Checking polygon with OID {oid1} and area {area1}")
        for oid2, shape2, area2 in all_polygons[i+1:]:
            if shape1.overlaps(shape2) or shape1.contains(shape2) or shape1.within(shape2):
                arcpy.AddMessage(f"Comparing with polygon OID {oid2} and area {area2}")
                if area1 < area2:
                    arcpy.AddMessage(f"Marking polygon with OID {oid1} for deletion (smaller than polygon with OID {oid2})")
                    delete_oids.add(oid1)
                    break
                elif area2 < area1:
                    arcpy.AddMessage(f"Marking polygon with OID {oid2} for deletion (smaller than polygon with OID {oid1})")
                    delete_oids.add(oid2)

    arcpy.AddMessage(f"Total polygons marked for deletion: {len(delete_oids)}")

    # Delete marked polygons
    with arcpy.da.UpdateCursor("in_memory\\non_overlapping_wf_layer", ['OID@']) as cursor:
        for row in cursor:
            if row[0] in delete_oids:
                arcpy.AddMessage(f"Deleting polygon with OID {row[0]}")
                cursor.deleteRow()

    # Copy the filtered features to the final output shapefile
    arcpy.management.CopyFeatures("in_memory\\non_overlapping_wf_layer", output_shapefile)

    # Add the shapefile to the current map in ArcGIS Pro
    map.addDataFromPath(output_shapefile)

    # Return the path to the created shapefile
    return output_shapefile

if __name__ == "__main__":
    windfarm_folder = "C:\\Users\\cflde\\Documents\\Graduation Project\\ArcGIS Pro\\BalticSea\\Results\\windfarm_folder"

    # Call the function with default status as 'Planned'
    output_shapefile = generate_turbine_areas(windfarm_folder)

    if output_shapefile:
        arcpy.AddMessage(f"Shapefile created and saved to: {output_shapefile}")
        arcpy.AddMessage("Shapefile added to the current map.")
    else:
        arcpy.AddMessage("No shapefile was created.")
