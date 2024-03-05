import arcpy
import os

def select_features(feature_layer: str, country_name: str) -> int:
    """Select features based on the specified country."""
    try:
        query = f"COUNTRY = '{country_name}'"
        arcpy.management.SelectLayerByAttribute(feature_layer, "NEW_SELECTION", query)

        # Check if any features were selected
        result = arcpy.management.GetCount(feature_layer)
        count = int(result.getOutput(0))

        arcpy.AddMessage(f"Selected {count} features for {country_name}")

        return count

    except arcpy.ExecuteError as e:
        arcpy.AddError(f"Error during feature selection:\n{e}")
        return 0

def project_to_utm_zone(feature_layer: str, utm_zone: int, output_shapefile: str) -> str:
    """Project the feature layer to the specified UTM Zone and save as a new shapefile."""
    try:
        # Create a temporary feature class to ensure proper data types
        temp_output_fc = arcpy.management.CopyFeatures(feature_layer, arcpy.Geometry())
        arcpy.AddMessage("Temporary feature class created.")

        # Set the spatial reference to the specified UTM Zone
        utm_wkid = 32600 + utm_zone  # UTM Zone 33N is WKID 32633
        utm_spatial_ref = arcpy.SpatialReference(utm_wkid)
        arcpy.AddMessage("Spatial reference set to UTM Zone {utm_zone}.")

        # Intermediate spatial reference: WGS 1984 geographic coordinates
        wgs84_spatial_ref = arcpy.SpatialReference(4326)

        # Project the temporary feature class to WGS 1984 geographic coordinates
        arcpy.management.Project(temp_output_fc, temp_output_fc, wgs84_spatial_ref)
        arcpy.AddMessage("Temporary feature class projected to WGS 1984.")

        # Project the temporary feature class to the UTM Zone spatial reference
        arcpy.management.Project(temp_output_fc, output_shapefile, utm_spatial_ref)
        arcpy.AddMessage(f"Temporary feature class projected to UTM Zone {utm_zone} and saved as {output_shapefile}")

        return output_shapefile

    except arcpy.ExecuteError as e:
        arcpy.AddError(f"Error during projection:\n{e}")
        return ''

    finally:
        # Clean up the temporary feature class
        if arcpy.Exists(temp_output_fc):
            arcpy.management.Delete(temp_output_fc)
            arcpy.AddMessage("Temporary feature class deleted.")

def save_shapefile(output_layer: str, output_shapefile: str) -> None:
    """Save the output layer as a shapefile."""
    try:
        # Specify the fields to keep
        fields_to_keep = ["FID", "INDEX_NO", "REGION_NO", "PORT_NAME", "COUNTRY", "LATITUDE", "LONGITUDE", "HARBORSIZE", "HARBORTYPE"]

        # Delete unnecessary fields in the output layer
        arcpy.management.DeleteField(output_layer, [field for field in arcpy.ListFields(output_layer) if field.name not in fields_to_keep and not field.required])
        arcpy.AddMessage("Unnecessary fields deleted.")

        # Copy features to the output shapefile
        arcpy.management.CopyFeatures(output_layer, output_shapefile)
        arcpy.AddMessage(f"Shapefile saved as {output_shapefile}")

    except arcpy.ExecuteError as e:
        arcpy.AddError(f"Error during shapefile saving:\n{e}")

def process_feature_service(feature_service_url: str, output_folder: str, country_name: str, utm_zone: int) -> None:
    """Process the feature service by selecting features based on the specified country,
    projecting to the user-specified UTM Zone, and saving the output as a shapefile."""
    try:
        # Create a feature layer from the feature service
        feature_layer = arcpy.management.MakeFeatureLayer(feature_service_url, "World_Port_Index").getOutput(0)

        # Check if feature layer is valid
        if not arcpy.Exists(feature_layer):
            raise ValueError("Input feature layer does not exist or is not valid.")

        arcpy.AddMessage("Feature layer created.")

        # Select features based on the user input country
        count = select_features(feature_layer, country_name)

        if count > 0:
            # Output shapefile path
            output_shapefile = os.path.join(output_folder, f"{country_name}_SelectedPorts.shp")

            # Project the feature layer to the specified UTM Zone and save as a new shapefile
            projected_layer = project_to_utm_zone(feature_layer, utm_zone, output_shapefile)

            if projected_layer:
                # Save the projected layer as a shapefile
                save_shapefile(projected_layer, output_shapefile)

        else:
            arcpy.AddMessage(f"No features found for the specified country: {country_name}")

    except ValueError as ve:
        arcpy.AddError(str(ve))
    except Exception as e:
        arcpy.AddError(f"Unexpected error:\n{e}")

# Additional parameters for UTM Zone
if __name__ == "__main__":
    feature_service_url: str = arcpy.GetParameterAsText(0)  # Feature service URL
    output_folder: str = arcpy.GetParameterAsText(1)  # User-specified output folder
    country_name: str = arcpy.GetParameterAsText(2)  # User input parameter for the country name
    utm_zone: int = int(arcpy.GetParameterAsText(3))  # User input parameter for the UTM Zone

    # Call the main processing function
    process_feature_service(feature_service_url, output_folder, country_name, utm_zone)
