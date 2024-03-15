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

def calculate_costs(year, raster_path, output_folder, shapefile):
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
            output_rasters.append(costs)

    # Save the result rasters in the specified output folder
    base_name = os.path.basename(raster_path)
    for i, support_structure in enumerate(support_structures):
        save_raster(output_folder, base_name, output_rasters[i], f"_{support_structure}_costs")

    # Create a raster where each cell is assigned values 1 for monopile, 2 for jacket, and 3 for floating based on water depth
    support_structure_raster = arcpy.sa.Con(water_depth < 25, 1, arcpy.sa.Con((25 <= water_depth) & (water_depth <= 55), 2, 3))

    # Save the support structure raster
    save_raster(output_folder, base_name, support_structure_raster, "_support_structure")

    return [os.path.join(output_folder, os.path.splitext(base_name)[0] + f"_{support_structure}_costs.tif") for support_structure in support_structures] + [os.path.join(output_folder, os.path.splitext(base_name)[0] + "_support_structure.tif")]

if __name__ == "__main__":
    # Parameters from user input in ArcGIS Pro
    year = arcpy.GetParameterAsText(0)
    raster_path = arcpy.GetParameterAsText(1)
    output_folder = arcpy.GetParameterAsText(2)
    shapefile = arcpy.GetParameterAsText(3)

    # Call the function
    result_rasters = calculate_costs(year, raster_path, output_folder, shapefile)

    for i, result in enumerate(result_rasters):
        support_structure = ['monopile', 'jacket', 'floating', 'support_structure'][i]
        arcpy.AddMessage(f"{support_structure.capitalize()} costs saved to: {result}")
