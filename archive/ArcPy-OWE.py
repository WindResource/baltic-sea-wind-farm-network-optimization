import arcpy
import os
import shutil
import time

def clear_output_folder(output_folder):
    def remove_raster_layers_from_project():
        # Get the current ArcGIS Pro project
        aprx = arcpy.mp.ArcGISProject("CURRENT")

        # Loop through all maps in the project
        for map_obj in aprx.listMaps():
            # Loop through all layers in the map
            for layer in map_obj.listLayers():
                # Check if the layer is a raster layer
                if layer.isRasterLayer:
                    # Remove the raster layer from the map
                    map_obj.removeLayer(layer)

    # Remove raster layers from the project
    remove_raster_layers_from_project()

    # Create the output folder with necessary permissions
    os.makedirs(output_folder, exist_ok=True)

    # Wait for a short time to release any locks
    time.sleep(2)

    # Clear the output folder if it exists
    shutil.rmtree(output_folder, ignore_errors=True)
    
    # Create the output folder again (in case it wasn't removed successfully)
    os.makedirs(output_folder, exist_ok=True)


def create_coordinate_rasters(shapefile, output_folder):
    # Create raster files for X and Y coordinates based on a point shapefile
    arcpy.env.workspace = output_folder

    # Create a temporary feature layer from the shapefile
    temp_feature_layer = "in_memory/temp_layer"
    arcpy.management.MakeFeatureLayer(shapefile, temp_feature_layer)

    # Specify the Web Mercator coordinate system
    spatial_ref = arcpy.SpatialReference(3857)  # WGS 1984 Web Mercator (auxiliary sphere)

    # Get extent based on the shapefile
    extent = arcpy.management.GetRasterProperties(temp_feature_layer, "MAXIMUM_EXTENT")

    # Create raster for X (horizontal) coordinates
    x_raster_path = os.path.join(output_folder, "x_coordinates.tif")
    arcpy.management.CreateFeatureclass(output_folder, "x_points.shp", "POINT", spatial_reference=spatial_ref)
    arcpy.management.AddField("x_points.shp", "X", "DOUBLE")
    arcpy.management.CalculateField("x_points.shp", "X", "!SHAPE!.firstPoint.X", "PYTHON3")
    arcpy.analysis.PointToRaster("x_points.shp", "X", x_raster_path, "CELL_CENTER", "", extent)

    # Create raster for Y (vertical) coordinates
    y_raster_path = os.path.join(output_folder, "y_coordinates.tif")
    arcpy.management.CreateFeatureclass(output_folder, "y_points.shp", "POINT", spatial_reference=spatial_ref)
    arcpy.management.AddField("y_points.shp", "Y", "DOUBLE")
    arcpy.management.CalculateField("y_points.shp", "Y", "!SHAPE!.firstPoint.Y", "PYTHON3")
    arcpy.analysis.PointToRaster("y_points.shp", "Y", y_raster_path, "CELL_CENTER", "", extent)

    return x_raster_path, y_raster_path


def calculate_port_distance(x_raster, y_raster, port_location):
    # Calculate the distance between each pixel in the rasters and the port location
    x_array = arcpy.RasterToNumPyArray(x_raster)
    y_array = arcpy.RasterToNumPyArray(y_raster)

    port_x, port_y = port_location
    distances = ((x_array - port_x)**2 + (y_array - port_y)**2)**0.5

    # Save the distance raster to a file
    distance_raster_path = os.path.join(os.path.dirname(x_raster), "port_distance.tif")
    distance_raster = arcpy.NumPyArrayToRaster(distances, arcpy.Point(*arcpy.PointGeometry(x_raster).extent.lowerLeft), x_raster)
    distance_raster.save(distance_raster_path)

    return distance_raster_path


def calc_vehicle_installation_costs(vehicle, port_distance_raster, n_wind_turbines, WT_rated_power):
    # Installation coefficients for different vehicles
    installation_coeff = {
        'PSIV': (40 / WT_rated_power, 18.5, 24, 144, 200),
        'Tug': (0.3, 7.5, 5, 0, 0),
        'AHV': (7, 18.5, 30, 90, 40)
    }
    
    # Extract coefficients based on the vehicle
    vehicle_coefficients = installation_coeff.get(vehicle)
    
    if vehicle_coefficients is None:
        raise ValueError(f"Invalid vehicle type: {vehicle}")

    vehicle_capacity, vehicle_speed, t_load, t_inst, day_rate = vehicle_coefficients
    
    # Calculate installation costs
    n_lifts = n_wind_turbines / vehicle_capacity

    # Use port_distance raster to adjust the installation costs based on distance
    distance_array = arcpy.RasterToNumPyArray(port_distance_raster)
    adjusted_costs = (n_lifts * (distance_array / vehicle_speed + t_load) + t_inst * n_wind_turbines) * day_rate * 1000 / 24

    # Save the adjusted costs raster to a file
    adjusted_costs_raster_path = os.path.join(os.path.dirname(port_distance_raster), f"{vehicle}_adjusted_costs.tif")
    adjusted_costs_raster = arcpy.NumPyArrayToRaster(adjusted_costs, arcpy.Point(*arcpy.PointGeometry(port_distance_raster).extent.lowerLeft), port_distance_raster)
    adjusted_costs_raster.save(adjusted_costs_raster_path)

    return adjusted_costs_raster_path

def calc_installation_costs(support_structure, port_distance, n_wind_turbines, WT_rated_power):
    # Check if the support structure is floating
    if support_structure == 'floating':
        # Calculate installation costs for both Tug and AHV and sum them
        vehicles = ['Tug', 'AHV']
        installation_costs = sum(calc_vehicle_installation_costs(vehicle, port_distance, n_wind_turbines, WT_rated_power) for vehicle in vehicles)
    else:
        # For other support structures
        vehicle = 'PSIV'
        # Calculate installation costs using the specified vehicle
        installation_costs = calc_vehicle_installation_costs(vehicle, port_distance, n_wind_turbines, WT_rated_power)

    return installation_costs

def calc_equipment_costs(year, support_structure, in_raster, n_wind_turbines, WT_rated_power):
    # Coefficients for different support structures and wind turbine costs
    support_structure_coeff = {
        ('2020', 'monopile'): (201, 613, 812),
        ('2030', 'monopile'): (181, 552, 370),
        ('2050', 'monopile'): (171, 521, 170),
        ('2020', 'jacket'): (114, -2270, 932),
        ('2030', 'jacket'): (103, -2043, 478),
        ('2050', 'jacket'): (97, -1930, 272),
        ('2020', 'floating'): (0, 774, 1481),
        ('2030', 'floating'): (0, 697, 1223),
        ('2050', 'floating'): (0, 658, 844)
    }
    wind_turbine_coeff = {
        '2020': (1500),
        '2030': (1200),
        '2050': (1000)
    }

    key = (year, support_structure)
    c1, c2, c3 = support_structure_coeff[key]
    WT_rated_cost = wind_turbine_coeff[year]
    # Calculate equipment costs
    return n_wind_turbines * WT_rated_power * ((c1 * (in_raster ** 2)) + (c2 * in_raster) + (c3 * 1000) + (WT_rated_cost))

def calc_total_costs(year, support_structure, in_raster, port_distance, n_wind_turbines, WT_rated_power, include_install_costs):
    installation_costs = 0
    if include_install_costs:
        installation_costs = calc_installation_costs(support_structure, port_distance, n_wind_turbines, WT_rated_power)

    equipment_costs = calc_equipment_costs(year, support_structure, in_raster, n_wind_turbines, WT_rated_power)

    return installation_costs + equipment_costs

def save_raster(output_folder, base_name, data, suffix):
    # Save raster to a file
    filename = os.path.splitext(base_name)[0] + suffix + ".tif"
    output_path = os.path.join(output_folder, filename)
    data.save(output_path)

def calc_raster(year, raster_path, output_folder, shapefile, water_depth_1, water_depth_2, water_depth_3, water_depth_4, WT_rated_power, n_wind_turbines, include_install_costs):
    # Clip the input raster based on the shapefile
    clipped_raster = os.path.join(output_folder, "clipped_raster.tif")
    arcpy.Clip_management(raster_path, "#", clipped_raster, shapefile, "-9999", "ClippingGeometry")

    # Load the clipped raster and calculate the negative water depth
    raster = arcpy.sa.Raster(clipped_raster)
    water_depth = -raster

    # Initialize variables
    clipped_raster_paths = []
    valid_rasters_found = False  # Flag to track if any valid rasters were found

    # Define support structures
    support_structures = ['monopile', 'jacket', 'floating']

    # Loop through each support structure
    for support_structure in support_structures:
        # Determine the mask condition based on the support structure
        mask_condition = None
        if support_structure == 'monopile':
            mask_condition = (water_depth_1 <= water_depth) & (water_depth < water_depth_2)
        elif support_structure == 'jacket':
            mask_condition = (water_depth_2 <= water_depth) & (water_depth <= water_depth_3)
        elif support_structure == 'floating':
            mask_condition = (water_depth_3 <= water_depth) & (water_depth <= water_depth_4)

        # Check if the mask condition contains any valid values
        if arcpy.RasterToNumPyArray(mask_condition).any():
            # Apply the mask condition to the raster
            masked_raster = arcpy.sa.Con(mask_condition, raster)
            # Check if the masked raster is not None
            if masked_raster is not None:
                # Check if the masked raster contains valid values
                if masked_raster.maximum is not None and masked_raster.maximum > -9999:
                    # Calculate total costs for the support structure
                    costs = calc_total_costs(year, support_structure, masked_raster, port_distance, n_wind_turbines, WT_rated_power, include_install_costs)
                    if costs is not None:
                        # Apply additional conditions to the costs raster
                        costs = arcpy.sa.Con((costs >= 0) & (costs <= 1E9), costs)
                        # Define the output path for the clipped raster
                        clipped_output_raster = os.path.join(output_folder, f"{support_structure}_costs.tif")
                        # Clip the costs raster based on the shapefile
                        arcpy.Clip_management(costs, "#", clipped_output_raster, shapefile, "0", "ClippingGeometry")
                        # Append the path of the clipped raster to the list
                        clipped_raster_paths.append(clipped_output_raster)
                        # Set the flag to indicate a valid raster was found
                        valid_rasters_found = True

    # If any valid rasters were found, calculate the total raster
    if valid_rasters_found:
        total_raster = arcpy.sa.CellStatistics(clipped_raster_paths, "SUM", "DATA")
        # Define the output path for the total raster
        total_output_raster = os.path.join(output_folder, "support_structure_costs.tif")
        # Clip the total raster based on the shapefile
        arcpy.Clip_management(total_raster, "#", total_output_raster, shapefile, "0", "ClippingGeometry")
        return total_output_raster
    else:
        return None

def add_all_rasters_to_map(output_folder, map_frame_name):
    # Add all raster files from the output folder to the map
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    
    # Check if the map with the specified name exists
    map_list = aprx.listMaps(map_frame_name)
    
    if not map_list:
        arcpy.AddError(f"Map '{map_frame_name}' not found in the project.")
        return

    map_object = map_list[0]

    # Get a list of all .tif raster files in the output folder
    raster_files = [f for f in os.listdir(output_folder) if f.endswith(".tif")]

    # Iterate through the raster files and add each to the map
    for raster_file in raster_files:
        raster_path = os.path.join(output_folder, raster_file)
        
        # Create a temporary raster layer in memory
        temp_raster_layer = arcpy.management.MakeRasterLayer(raster_path, raster_file[:-4])[0]  # Use the file name without extension as layer name
        
        # Add the temporary raster layer to the map
        map_object.addLayer(temp_raster_layer, "AUTO_ARRANGE")


if __name__ == "__main__":
    # Parameters from user input in ArcGIS Pro
    year, raster_path, output_folder, shapefile = [arcpy.GetParameterAsText(i) for i in range(4)]
    water_depth_1, water_depth_2, water_depth_3, water_depth_4 = map(float, [arcpy.GetParameterAsText(i) for i in range(4, 8)])
    n_wind_turbines = int(arcpy.GetParameterAsText(8))
    project_path = arcpy.GetParameterAsText(9)
    map_frame_name = arcpy.GetParameterAsText(10)
    port_distance = float(arcpy.GetParameterAsText(11))
    WT_rated_power = float(arcpy.GetParameterAsText(12))
    include_install_costs = arcpy.GetParameter(13)
    port_location_x = float(arcpy.GetParameterAsText(14).replace(',', '.'))
    port_location_y = float(arcpy.GetParameterAsText(15).replace(',', '.'))
    port_location = (port_location_x, port_location_y)
    

    # Create rasters for X and Y coordinates
    x_raster, y_raster = create_coordinate_rasters(shapefile, output_folder)

    # Calculate port distance raster
    port_distance_raster = calculate_port_distance(x_raster, y_raster, port_location)

    # Calculate installation costs
    installation_costs = calc_installation_costs(port_distance_raster, n_wind_turbines, WT_rated_power)
    arcpy.AddMessage(f"Installation costs for {support_structure}: {installation_costs}")

    # Calculate and print equipment costs for each support structure
    for structure in ['monopile', 'jacket', 'floating']:
        equipment_costs = calc_equipment_costs(year, structure, port_distance_raster, n_wind_turbines, WT_rated_power)
        arcpy.AddMessage(f"Equipment costs for {structure}: {equipment_costs}")

    # Rest of your script...
    result_raster = calc_raster(year, raster_path, output_folder, shapefile, water_depth_1, water_depth_2, water_depth_3, water_depth_4, WT_rated_power, n_wind_turbines, include_install_costs)

    if result_raster is not None:
        add_all_rasters_to_map(output_folder, map_frame_name)
        arcpy.AddMessage("All raster layers added to the map.")
    else:
        arcpy.AddMessage("No valid rasters found.")