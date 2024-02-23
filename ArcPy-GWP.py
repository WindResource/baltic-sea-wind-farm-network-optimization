import os
import arcpy

def select_and_save_polygons_by_country(input_shapefile, output_shapefile, country_name):
    # Set the workspace
    arcpy.env.workspace = os.path.dirname(input_shapefile)

    # Ensure the input shapefile has an attribute field for the country
    country_field = "Country"  # Change this to the actual field name in your shapefile
    if country_field not in [field.name for field in arcpy.ListFields(input_shapefile)]:
        arcpy.AddError(f"The specified field '{country_field}' does not exist in the shapefile.")
        return

    # Build a SQL expression to select features based on the country
    sql_expression = f"{arcpy.AddFieldDelimiters(input_shapefile, country_field)} = '{country_name}'"

    # Make a feature layer to perform the selection
    arcpy.MakeFeatureLayer_management(input_shapefile, "temp_layer", sql_expression)

    # Select features based on the SQL expression
    arcpy.SelectLayerByAttribute_management("temp_layer", "NEW_SELECTION", sql_expression)

    # Construct the output shapefile path in the specified Results folder
    script_directory = os.path.dirname(os.path.abspath(__file__))
    output_folder = os.path.join(script_directory, "Results")
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    output_shapefile = os.path.join(output_folder, f"{country_name}_selected_features.shp")

    # Copy the selected features to a new shapefile
    arcpy.CopyFeatures_management("temp_layer", output_shapefile)

    # Clean up
    arcpy.Delete_management("temp_layer")

    arcpy.AddMessage(f"Selected features for {country_name} saved to {output_shapefile}.")

# Set default file paths relative to the script location
default_input_shapefile = os.path.join("Data", "Wind Farms (polygons)", "windfarmspolyPolygon.shp")
default_output_folder = os.path.join("Results")
default_country_to_select = "YourCountry"  # Replace with the actual country name

# Create parameters for the script tool
input_shapefile_param = arcpy.Parameter(
    displayName="Input Shapefile",
    name="input_shapefile",
    datatype="DEShapefile",
    parameterType="Required",
    direction="Input",
    defaultValue=default_input_shapefile,
    multiValue=False
)

output_shapefile_param = arcpy.Parameter(
    displayName="Output Shapefile",
    name="output_shapefile",
    datatype="DEShapefile",
    parameterType="Required",
    direction="Output",
    defaultValue=default_output_folder,
    multiValue=False
)

country_param = arcpy.Parameter(
    displayName="Country Name",
    name="country_name",
    datatype="GPString",
    parameterType="Required",
    direction="Input",
    defaultValue=default_country_to_select,
    multiValue=False
)

# Set the parameter list
parameters = [input_shapefile_param, output_shapefile_param, country_param]

# Get user inputs using arcpy
arcpy.GetParameterAsText(0)  # Input shapefile
arcpy.GetParameterAsText(1)  # Output shapefile
arcpy.GetParameterAsText(2)  # Country name

# Call the function with user inputs
select_and_save_polygons_by_country(
    input_shapefile=input_shapefile_param.valueAsText,
    output_shapefile=output_shapefile_param.valueAsText,
    country_name=country_param.valueAsText
)
