class ToolValidator:
    def __init__(self):
        # Set self.params for use in other validation methods.
        self.params = arcpy.GetParameterInfo()

    def initializeParameters(self):
        # Customize parameter properties. This method gets called when the tool is opened.

        # Parameter 0: Year
        self.params[0].name = "year"
        self.params[0].displayName = "Year"
        self.params[0].parameterType = "Required"
        self.params[0].dataType = "GPString"
        self.params[0].filter.type = "ValueList"
        self.params[0].filter.list = ["2020", "2030", "2050"]
        self.params[0].value = "2020"

        # Parameter 1: Raster Path
        self.params[1].name = "raster_path"
        self.params[1].displayName = "Input Raster"
        self.params[1].parameterType = "Required"
        self.params[1].dataType = "DEFile"
        self.params[1].value = r"C:\path\to\your\raster.tif"  # Set a default raster path

        # Parameter 2: Output Folder
        self.params[2].name = "output_folder"
        self.params[2].displayName = "Output Folder"
        self.params[2].parameterType = "Required"
        self.params[2].dataType = "DEFolder"
        self.params[2].value = r"C:\path\to\your\output\folder"  # Set a default output folder

        # Parameter 3-6: Water Depths
        for i in range(3, 7):
            self.params[i].name = f"water_depth_{i-2}"
            self.params[i].displayName = f"Water Depth {i-2}"
            self.params[i].parameterType = "Required"
            self.params[i].dataType = "GPLong"
            self.params[i].value = 0  # Set a default value

        # Parameter 7: Number of Wind Turbines
        self.params[7].name = "n_wind_turbines"
        self.params[7].displayName = "Number of Wind Turbines"
        self.params[7].parameterType = "Required"
        self.params[7].dataType = "GPLong"
        self.params[7].value = 1  # Set a default value

        # Parameter 8: Project Path
        self.params[8].name = "project_path"
        self.params[8].displayName = "Project Path"
        self.params[8].parameterType = "Required"
        self.params[8].dataType = "DEWorkspace"
        self.params[8].value = r"C:\path\to\your\project.gdb"  # Set a default project path

        # Parameter 9: Map Frame Name
        self.params[9].name = "map_frame_name"
        self.params[9].displayName = "Map Frame Name"
        self.params[9].parameterType = "Required"
        self.params[9].dataType = "GPString"
        self.params[9].value = "Default_Map_Frame"  # Set a default map frame name

        # Parameter 10: Port Distance
        self.params[10].name = "port_distance"
        self.params[10].displayName = "Port Distance"
        self.params[10].parameterType = "Required"
        self.params[10].dataType = "GPDouble"
        self.params[10].value = 10.0  # Set a default value

        # Parameter 11: Wind Turbine Rated Power
        self.params[11].name = "WT_rated_power"
        self.params[11].displayName = "Wind Turbine Rated Power"
        self.params[11].parameterType = "Required"
        self.params[11].dataType = "GPDouble"
        self.params[11].value = 2.0  # Set a default value

        # Parameter 12: Include Installation Costs
        self.params[12].name = "include_install_costs"
        self.params[12].displayName = "Include Installation Costs"
        self.params[12].parameterType = "Optional"
        self.params[12].dataType = "GPBoolean"
        self.params[12].value = True  # Set a default value

        return
