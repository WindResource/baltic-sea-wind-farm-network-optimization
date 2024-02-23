import arcpy
import os

class ToolValidator:
    # Class to add custom behavior and properties to the tool and tool parameters.

    def __init__(self):
        # Set self.params for use in other validation methods.
        self.params = arcpy.GetParameterInfo()

    def initializeParameters(self):
        # Always define parameters in the validation properties page.

        # Define parameters
        input_shapefile_param = arcpy.Parameter(
            displayName="Input Shapefile",
            name="input_shapefile",
            datatype="DEShapefile",
            parameterType="Required",
            direction="Input"
        )

        output_shapefile_param = arcpy.Parameter(
            displayName="Output Shapefile",
            name="output_shapefile",
            datatype="DEShapefile",
            parameterType="Required",
            direction="Output"
        )

        country_param = arcpy.Parameter(
            displayName="Country Name",
            name="country_name",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )

        # Add parameters to the parameters object
        self.params = [input_shapefile_param, output_shapefile_param, country_param]

        # Set default values for parameters
        default_input_shapefile = os.path.join("Data", "Wind Farms (polygons)", "windfarmspolyPolygon.shp")
        default_output_folder = os.path.join("Results")
        default_country_to_select = "YourCountry"  # Replace with the actual country name

        self.params[0].value = default_input_shapefile
        self.params[1].value = os.path.join(default_output_folder, "selected_features.shp")
        self.params[2].value = default_country_to_select

        # Set parameter properties
        self.params[0].filter.list = ["Shapefile"]  # Input shapefile filter
        self.params[1].filter.list = ["Shapefile"]  # Output shapefile filter
        self.params[1].parameterDependencies = [self.params[0].name]  # Output shapefile depends on the input shapefile
        self.params[2].filter.type = "ValueList"  # Country name is a value list
        self.params[2].filter.list = ["Country1", "Country2", "Country3"]  # Replace with actual country names

        return

    def updateParameters(self):
        # Modify the values and properties of parameters before internal
        # validation is performed.
        return

    def updateMessages(self):
        # Modify the messages created by internal validation for each tool
        # parameter. This method is called after internal validation.
        return
