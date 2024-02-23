import os
import arcpy

class ToolValidator:
    def __init__(self):
        self.params = arcpy.GetParameterInfo()

    def initializeParameters(self):
        # Get the project folder
        self.params[0].value = r"C:\Users\cflde\Documents\Graduation Project\ArcGIS Pro\BalticSea" # project_folder

        # Set default values for other parameters relative to the project folder
        self.params[1].value = os.path.join(self.params[0].valueAsText, "Data", "countries", "DEU_elevation_w_bathymetry.tif")
        self.params[2].value = os.path.join(self.params[0].valueAsText, "Data", "Wind Farms (polygons)", "windfarmspolyPolygon.shp")
        self.params[3].value = os.path.join(self.params[0].valueAsText, "Results")

        # Set default values for other parameters
        self.params[4].value = 0.0  # water_depth_1
        self.params[5].value = 10.0  # water_depth_2
        self.params[6].value = 20.0  # water_depth_3
        self.params[7].value = 30.0  # water_depth_4
        self.params[8].value = 10  # n_wind_turbines

        self.params[9].value = 2020  # Set default value for the 'year' parameter
        self.params[9].filter.list = [2020, 2030, 2050]  # year

        self.params[10].value = "Baltic Sea Region"  # map_frame_name

        self.params[11].value = 100.0  # port_distance
        self.params[12].value = 2.0  # WT_rated_power
        self.params[13].value = True  # include_install_costs

        return

    def updateParameters(self):
        # Modify the values and properties of parameters before internal
        # validation is performed.
        return

    def updateMessages(self):
        # Modify the messages created by internal validation for each tool
        # parameter. This method is called after internal validation.
        return
