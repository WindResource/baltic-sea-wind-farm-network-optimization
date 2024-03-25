import arcpy
import os

def process_feature_service(output_folder: str, country_name: str) -> None:
    """
    Process the feature service by selecting features based on the specified country,
    convert them to point features, project to UTM Zone 33N, and save the output as a shapefile.

    Parameters:
        output_folder (str): The folder where the output shapefile will be saved.
        country_name (str): The name of the country to select features for.

    Returns:
        None
    """
    try:
        # Feature service URL
        feature_service_url = "https://services.arcgis.com/hRUr1F8lE8Jq2uJo/ArcGIS/rest/services/World_Port_Index/FeatureServer/0"

        # UTM Zone
        utm_wkid = 32633  # UTM Zone 33N

        # Create a feature layer from the feature service
        feature_layer = arcpy.management.MakeFeatureLayer(feature_service_url, "World_Port_Index").getOutput(0)

        # Select features based on the user input country
        query = f"COUNTRY = '{country_name}'"
        arcpy.management.SelectLayerByAttribute(feature_layer, "NEW_SELECTION", query)

        # Check if any features were selected
        result = arcpy.management.GetCount(feature_layer)
        count = int(result.getOutput(0))

        if count > 0:
            # Convert the feature layer to a point feature layer
            arcpy.management.FeatureToPoint(feature_layer, f"in_memory\\{country_name}_Points", "INSIDE")

            # Project the point feature layer to the specified UTM Zone
            utm_spatial_ref = arcpy.SpatialReference(utm_wkid)
            arcpy.management.Project(f"in_memory\\{country_name}_Points", f"in_memory\\{country_name}_Projected", utm_spatial_ref)

            # Create a new shapefile in the user-specified output folder
            output_shapefile = os.path.join(output_folder, f"{country_name}_SelectedPorts.shp")

            # Check if the output shapefile already exists and delete it
            if arcpy.Exists(output_shapefile):
                arcpy.management.Delete(output_shapefile)

            arcpy.management.CopyFeatures(f"in_memory\\{country_name}_Projected", output_shapefile)

            # Open the newly created shapefile
            output_layer = arcpy.management.MakeFeatureLayer(output_shapefile, f"{country_name}_SelectedPorts").getOutput(0)

            # Delete unnecessary fields in the output shapefile
            fields_to_keep = ["FID", "INDEX_NO", "REGION_NO", "PORT_NAME", "COUNTRY", "LATITUDE", "LONGITUDE", "HARBORSIZE", "HARBORTYPE"]
            fields_to_delete = [field.name for field in arcpy.ListFields(output_layer) if field.name not in fields_to_keep and not field.required]
            arcpy.management.DeleteField(output_layer, fields_to_delete)

            arcpy.AddMessage(f"{count} features selected, projected to UTM Zone 33N, and exported to {output_shapefile}")

            # Use arcpy.mp to add the layer to the map
            aprx = arcpy.mp.ArcGISProject("CURRENT")
            map_object = aprx.activeMap

            # Add the layer to the map
            map_object.addLayer(output_layer)

        else:
            arcpy.AddMessage(f"No features found for the specified country: {country_name}")

    except arcpy.ExecuteError:
        arcpy.AddError(arcpy.GetMessages(2))
    except Exception as e:
        arcpy.AddError(str(e))

if __name__ == "__main__":
    # Input parameters
    port_folder: str = arcpy.GetParameterAsText(0)  # User-specified output folder
    country_name: str = arcpy.GetParameterAsText(1)  # User input parameter for the country name

    # Call the main processing function
    process_feature_service(port_folder, country_name)
