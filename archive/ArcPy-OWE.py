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

def calculate_costs(year, raster_path, output_folder, shapefile, water_depth_min, water_depth_max):
    # Create Raster object
    in_raster = arcpy.Raster(raster_path)
    
    # Calculate water depth based on the raster data (negative of raster values)
    water_depth = -in_raster

    # Loop through each support structure and calculate costs
    support_structures = ['monopile', 'jacket', 'floating']
    output_rasters = []

    for support_structure in support_structures:
        costs = calculate_support_structure_costs(year, support_structure, in_raster)
        if costs is not None:
            # Mask the raster based on the water depth condition
            if support_structure == 'monopile':
                masked_costs = arcpy.sa.Con(water_depth < water_depth_min, costs)
            elif support_structure == 'jacket':
                masked_costs = arcpy.sa.Con((water_depth_min <= water_depth) & (water_depth <= water_depth_max), costs)
            else:  # support_structure == 'floating'
                masked_costs = arcpy.sa.Con(water_depth > water_depth_max, costs)

            output_rasters.append(masked_costs)

            # Save the masked raster
            save_raster(output_folder, os.path.basename(raster_path), masked_costs, f"_{support_structure}_costs")

    return [os.path.join(output_folder, os.path.splitext(os.path.basename(raster_path))[0] + f"_{support_structure}_costs.tif") for support_structure in support_structures]

if __name__ == "__main__":
    # Parameters from user input in ArcGIS Pro
    year = arcpy.GetParameterAsText(0)
    raster_path = arcpy.GetParameterAsText(1)
    output_folder = arcpy.GetParameterAsText(2)
    shapefile = arcpy.GetParameterAsText(3)
    water_depth_min = float(arcpy.GetParameterAsText(4))  # Min water depth parameter
    water_depth_max = float(arcpy.GetParameterAsText(5))  # Max water depth parameter

    # Call the function
    result_rasters = calculate_costs(year, raster_path, output_folder, shapefile, water_depth_min, water_depth_max)

    for i, result in enumerate(result_rasters):
        support_structure = ['monopile', 'jacket', 'floating'][i]
        arcpy.AddMessage(f"{support_structure.capitalize()} costs saved to: {result}")
