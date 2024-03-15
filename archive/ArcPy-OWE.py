import arcpy
import os

# Define a dictionary to map year to c1, c2, and c3 values for each support structure
coefficients = {
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

def calculate_support_structure_costs(year, support_structure, in_raster):
    key = (year, support_structure)
    if key not in coefficients:
        arcpy.AddError(f"No matching data found for year {year} and support structure {support_structure}.")
        return None
    c1, c2, c3 = coefficients[key]
    return (c1 * (in_raster ** 2)) + (c2 * in_raster) + (c3 * 1000)

def save_raster(output_folder, base_name, data, suffix):
    filename = os.path.splitext(base_name)[0] + suffix + ".tif"
    output_path = os.path.join(output_folder, filename)
    data.save(output_path)

def calculate_costs(year, raster_path, output_folder, shapefile, water_depth_1, water_depth_2, water_depth_3, water_depth_4):
    # Clip the raster based on the shapefile
    clipped_raster = arcpy.sa.ExtractByMask(raster_path, shapefile)
    
    # Calculate water depth based on the clipped raster data (negative of raster values)
    water_depth = -clipped_raster

    # Create an empty cumulative raster with the same extent and spatial reference as the clipped raster
    cumulative_raster = arcpy.sa.Raster(raster_path) * 0

    # List to store paths of all clipped rasters
    clipped_raster_paths = []

    # Loop through each support structure and calculate costs
    support_structures = ['monopile', 'jacket', 'floating']

    for support_structure in support_structures:
        # Mask the clipped raster based on the water depth condition for the current support structure
        if support_structure == 'monopile':
            mask_condition = (water_depth_1 <= water_depth) & (water_depth < water_depth_2)
        elif support_structure == 'jacket':
            mask_condition = (water_depth_2 <= water_depth) & (water_depth <= water_depth_3)
        else:  # support_structure == 'floating'
            mask_condition = (water_depth_3 <= water_depth) & (water_depth <= water_depth_4)
        
        # Check if the mask condition is satisfied
        if arcpy.RasterToNumPyArray(mask_condition).any():
            masked_raster = arcpy.sa.Con(mask_condition, clipped_raster)
            # Check if there are any valid cells within the masked area
            if arcpy.RasterToNumPyArray(masked_raster).any():
                # Calculate costs for the masked raster
                costs = calculate_support_structure_costs(year, support_structure, masked_raster)
                if costs is not None:
                    # Set NoData for values below 0 and above 1E9
                    costs = arcpy.sa.Con((costs >= 0) & (costs <= 1E9), costs)
                    # Clip the raster
                    clipped_output_raster = os.path.join(output_folder, f"{os.path.splitext(os.path.basename(raster_path))[0]}_{support_structure}_costs_clipped.tif")
                    arcpy.Clip_management(costs, "#", clipped_output_raster, shapefile, "0", "ClippingGeometry")
                    clipped_raster_paths.append(clipped_output_raster)
                    # Add the costs to the cumulative raster
                    cumulative_raster += costs

    # Clip the cumulative raster
    cumulative_output_raster = os.path.join(output_folder, "cumulative_costs_clipped.tif")
    arcpy.Clip_management(cumulative_raster, "#", cumulative_output_raster, shapefile, "0", "ClippingGeometry")
    clipped_raster_paths.append(cumulative_output_raster)

    return clipped_raster_paths




if __name__ == "__main__":
    # Parameters from user input in ArcGIS Pro
    year = arcpy.GetParameterAsText(0)
    raster_path = arcpy.GetParameterAsText(1)
    output_folder = arcpy.GetParameterAsText(2)
    shapefile = arcpy.GetParameterAsText(3)
    water_depth_1 = float(arcpy.GetParameterAsText(4))
    water_depth_2 = float(arcpy.GetParameterAsText(5))
    water_depth_3 = float(arcpy.GetParameterAsText(6))
    water_depth_4 = float(arcpy.GetParameterAsText(7))

    # Call the function
    result_rasters = calculate_costs(year, raster_path, output_folder, shapefile, water_depth_1, water_depth_2, water_depth_3, water_depth_4)

    for result in result_rasters:
        arcpy.AddMessage(f"Raster saved to: {result}")
