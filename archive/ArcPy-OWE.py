import arcpy
import os

# Define a dictionary to map year to c1, c2, and c3 values for each support structure
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
    '2020': (8, 1500),
    '2030': (15, 1200),
    '2050': (20, 1000)
}


# Function to calculate equipment costs based on year, support structure, and input raster
def calculate_equipment_costs(year, support_structure, in_raster):
    # Get the coefficients for the support structure based on the year
    key = (year, support_structure)
    c1, c2, c3 = support_structure_coeff[key]
    
    # Get the rated power and cost of wind turbine based on the year
    rated_power, WT_rated_cost = wind_turbine_coeff[year]
    
    # Calculate the equipment costs
    return n_wind_turbines * rated_power * ((c1 * (in_raster ** 2)) + (c2 * in_raster) + (c3 * 1000) + (WT_rated_cost))



def save_raster(output_folder, base_name, data, suffix):
    filename = os.path.splitext(base_name)[0] + suffix + ".tif"
    output_path = os.path.join(output_folder, filename)
    data.save(output_path)

def calculate_costs(year, raster_path, output_folder, shapefile, water_depth_1, water_depth_2, water_depth_3, water_depth_4):
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
                    # Calculate equipment costs for the support structure
                    costs = calculate_equipment_costs(year, support_structure, masked_raster)
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

    # Call the function
    result_raster = calculate_costs(year, raster_path, output_folder, shapefile, water_depth_1, water_depth_2, water_depth_3, water_depth_4)

    if result_raster is not None:
        # Call the function to add all raster files to the map
        add_all_rasters_to_map(output_folder, map_frame_name)
        arcpy.AddMessage("All raster layers added to the map.")
    else:
        arcpy.AddMessage("No valid rasters found.")