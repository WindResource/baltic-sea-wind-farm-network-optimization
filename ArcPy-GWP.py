import arcpy
import os

def create_shapefile(input_shapefile: str, output_folder: str, country: str, approved: bool, construction: bool, planned: bool, production: bool) -> str:
    """
    Create a shapefile for the specified combination of country and selected statuses based on the input shapefile.

    Parameters:
    - input_shapefile (str): Path to the input shapefile.
    - output_folder (str): Path to the output folder where the shapefile will be saved.
    - country (str): The selected country.
    - approved (bool): True if the Approved status is selected, False otherwise.
    - construction (bool): True if the Construction status is selected, False otherwise.
    - planned (bool): True if the Planned status is selected, False otherwise.
    - production (bool): True if the Production status is selected, False otherwise.

    Returns:
    - str: A message indicating the result of the operation.
    """
    try:
        # Create a list of selected statuses
        selected_statuses = []
        if approved:
            selected_statuses.append("Approved")
        if construction:
            selected_statuses.append("Construction")
        if planned:
            selected_statuses.append("Planned")
        if production:
            selected_statuses.append("Production")

        # Create a SQL expression to select features for the specified combination
        sql_expression = (
            arcpy.AddFieldDelimiters(input_shapefile, "Country") + " = '{}' AND " +
            arcpy.AddFieldDelimiters(input_shapefile, "Status") + " IN ({})").format(
                country, ", ".join(["'{}'".format(status) for status in selected_statuses]))

        # Create the new shapefile for the specified combination
        output_shapefile = os.path.join(output_folder, f"offshore_wind_farms_{country}_{'_'.join(selected_statuses)}.shp")
        arcpy.Select_analysis(input_shapefile, output_shapefile, sql_expression)

        return f"Shapefile created successfully for {country}, {', '.join(selected_statuses)}."
    except Exception as e:
        return str(e)

if __name__ == "__main__":
        # Get the input shapefile, output folder, country, and status parameters from the user input
        input_shapefile: str = arcpy.GetParameterAsText(0)
        output_folder: str = arcpy.GetParameterAsText(1)
        country: str = arcpy.GetParameterAsText(2)
        status_approved: bool = arcpy.GetParameter(3)
        status_construction: bool = arcpy.GetParameter(4)
        status_planned: bool = arcpy.GetParameter(5)
        status_production: bool = arcpy.GetParameter(6)

        # Validate input parameters
        if not arcpy.Exists(input_shapefile):
            arcpy.AddError("Input shapefile does not exist.")
        elif not os.path.isdir(output_folder):
            arcpy.AddError("Output folder is not valid.")
        else:
            # Execute the main function
            result_message: str = create_shapefile(
                input_shapefile, output_folder, country, status_approved, status_construction, status_planned, status_production
            )

            # Set the output message
            arcpy.AddMessage(result_message)

