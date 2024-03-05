import arcpy

def process_feature_service(feature_service_url: str, output_folder: str, country_name: str) -> None:
    """Process the feature service by selecting features based on the specified country and save the output as a shapefile."""
    try:
        # Create a feature layer from the feature service
        feature_layer = arcpy.management.MakeFeatureLayer(feature_service_url, "World_Port_Index").getOutput(0)

        # Select features based on the user input country
        query = f"COUNTRY = '{country_name}'"
        arcpy.management.SelectLayerByAttribute(feature_layer, "NEW_SELECTION", query)

        # Check if any features were selected
        result = arcpy.management.GetCount(feature_layer)
        count = int(result.getOutput(0))

        if count > 0:
            # Specify the fields to keep
            fields_to_keep = ["FID", "INDEX_NO", "REGION_NO", "PORT_NAME", "COUNTRY", "LATITUDE", "LONGITUDE", "HARBORSIZE", "HARBORTYPE"]

            # Create a list of field names to delete (excluding required fields)
            fields_to_delete = [field.name for field in arcpy.ListFields(feature_layer) if field.name not in fields_to_keep and not field.required]

            # Create a new shapefile in the user-specified output folder
            output_shapefile = arcpy.ValidateTableName(f"{country_name}_SelectedPorts", output_folder)
            arcpy.management.CopyFeatures(feature_layer, output_shapefile)

            # Open the newly created shapefile
            output_layer = arcpy.management.MakeFeatureLayer(output_shapefile, f"{country_name}_SelectedPorts").getOutput(0)

            # Delete unnecessary fields in the output shapefile
            arcpy.management.DeleteField(output_layer, fields_to_delete)

            arcpy.AddMessage(f"{count} features selected and exported to {output_shapefile}")

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
    feature_service_url: str = arcpy.GetParameterAsText(0)  # Feature service URL
    output_folder: str = arcpy.GetParameterAsText(1)  # User-specified output folder
    country_name: str = arcpy.GetParameterAsText(2)  # User input parameter for the country name

    # Call the main processing function
    process_feature_service(feature_service_url, output_folder, country_name)
