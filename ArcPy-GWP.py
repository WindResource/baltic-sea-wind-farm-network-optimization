import arcpy
import os

def create_shapefile(input_shapefile: str, output_folder: str, selected_country: str, selected_statuses: list) -> str:
    """
    Create shapefiles for the specified combination of country and statuses based on the input shapefile.

    Parameters:
    - input_shapefile (str): Path to the input shapefile.
    - output_folder (str): Path to the output folder where shapefiles will be saved.
    - selected_country (str): The selected country.
    - selected_statuses (list): List of selected statuses.

    Returns:
    - str: A message indicating the result of the operation.
    """
    try:
        # Create a SQL expression to select features for the specified combination and statuses
        status_conditions = " OR ".join([arcpy.AddFieldDelimiters(input_shapefile, "Status") + " = '{}'".format(status) for status in selected_statuses])
        sql_expression = (
            arcpy.AddFieldDelimiters(input_shapefile, "Country") + " = '{}' AND (" + status_conditions + ")"
        ).format(selected_country)

        # Create the new shapefile for the specified combination and statuses
        output_shapefile = os.path.join(output_folder, f"offshore_wind_farms_{selected_country}_{'_'.join(selected_statuses)}.shp")
        arcpy.Select_analysis(input_shapefile, output_shapefile, sql_expression)

        return f"Shapefile created successfully for {selected_country}, {', '.join(selected_statuses)}."
    except Exception as e:
        return str(e)

if __name__ == "__main__":
        # Get the input shapefile, output folder, country, and statuses from the user input
        input_shapefile: str = arcpy.GetParameterAsText(0)
        output_folder: str = arcpy.GetParameterAsText(1)
        selected_country: str = arcpy.GetParameterAsText(2)
        selected_statuses: list = arcpy.GetParameterAsText(3).split(";")  # Use MultiValue input, separated by semicolon

        # Validate input parameters
        if not arcpy.Exists(input_shapefile):
            arcpy.AddError("Input shapefile does not exist.")
        elif not os.path.isdir(output_folder):
            arcpy.AddError("Output folder is not valid.")
        else:
            # Execute the main function
            result_message: str = create_shapefile(input_shapefile, output_folder, selected_country, selected_statuses)

            # Set the output message
            arcpy.AddMessage(result_message)
