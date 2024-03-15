import arcpy
import os
import shutil
import time
from typing import Optional, Tuple, List

def clear_output_folder(output_folder: str) -> None:
    def remove_raster_layers_from_project() -> None:
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

def calc_vehicle_installation_costs(vehicle: str, port_distance: float,
                                    n_wind_turbines: int, WT_rated_power: float,
                                    raster: arcpy.Raster) -> arcpy.Raster:
    # Installation coefficients for different vehicles
    installation_coeff = {
        'PSIV': (40 / WT_rated_power, 18.5, 24, 144, 200),
        'Tug': (0.3, 7.5, 5, 0, 0),
        'AHV': (7, 18.5, 30, 90, 40)
    }
    
    # Extract coefficients based on the support structure
    vehicle_coefficients = installation_coeff.get(vehicle)
    
    if vehicle_coefficients is None:
        raise ValueError(f"Invalid support structure: {vehicle}")

    vehicle_capacity, vehicle_speed, t_load, t_inst, day_rate = vehicle_coefficients
    
    # Create a raster with the same extent as masked_raster, and all values set to 1
    ones_raster = arcpy.Raster(raster) * 0 + 1

    # Calculate installation costs
    n_lifts = 1 / vehicle_capacity
    vehicle_installation_costs = (n_lifts * ((2 * port_distance) / vehicle_speed + t_load) + t_inst * n_wind_turbines) * day_rate * 1000 / 24 * ones_raster

    return vehicle_installation_costs

def calc_installation_costs(raster: arcpy.Raster, support_structure: str,
                            port_distance: float, n_wind_turbines: int,
                            WT_rated_power: float) -> arcpy.Raster:
    # Check if the support structure is floating
    if support_structure == 'floating':
        # Calculate installation costs for both Tug and AHV and sum them
        vehicles = ['Tug', 'AHV']
        installation_costs = sum(calc_vehicle_installation_costs(vehicle, port_distance, n_wind_turbines, WT_rated_power, raster) for vehicle in vehicles)
    else:
        # For other support structures
        vehicle = 'PSIV'
        # Calculate installation costs using the specified vehicle
        installation_costs = calc_vehicle_installation_costs(vehicle, port_distance, n_wind_turbines, WT_rated_power, raster)

    return installation_costs

def calc_equipment_costs(water_depth: float, year: str, support_structure: str,
                         n_wind_turbines: int, WT_rated_power: float) -> float:
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
        '2020': 1500,
        '2030': 1200,
        '2050': 1000
    }

    key = (year, support_structure)
    c1, c2, c3 = support_structure_coeff[key]
    WT_rated_cost = wind_turbine_coeff[year]
    
    # Calculate equipment costs
    return n_wind_turbines * WT_rated_power * ((c1 * (water_depth ** 2)) + (c2 * water_depth) + (c3 * 1000) + (WT_rated_cost))

def calc_operation_costs(support_structure: str, n_wind_turbines: int, DP_WF: float, labda: float) -> arcpy.Raster:
    # Operation coefficients for different vessels
    operation_coeff = {
        'JUV': (18.5, 50, 150, 1),
        'Tug': (7.5, 50, 2.5, 2)
    }
    
    # Determine the vessel based on the support structure
    if support_structure in ['jacket', 'monopile']:
        vessel_type = 'JUV'
    elif support_structure == 'floating':
        vessel_type = 'Tug'
    else:
        raise ValueError(f"Invalid support structure: {support_structure}")

    # Extract coefficients based on the determined vessel type
    vessel_coefficients = operation_coeff.get(vessel_type)
    
    if vessel_coefficients is None:
        raise ValueError(f"Invalid vessel: {vessel_type}")

    v, t_rep, DR, n = vessel_coefficients

    # Calculate operation costs
    operation_costs = n_wind_turbines * labda * ((2 * n * DP_WF) / v + t_rep) * DR / 24 * ones_raster

    return operation_costs


def save_raster(output_folder: str, base_name: str, data: arcpy.Raster, suffix: str) -> None:
    # Save raster to a file
    filename = os.path.splitext(base_name)[0] + suffix + ".tif"
    output_path = os.path.join(output_folder, filename)
    data.save(output_path)

def calc_total_costs(raster: arcpy.Raster, year: str, support_structure: str,
                     port_distance: float, n_wind_turbines: int,
                     WT_rated_power: float, include_capex_equipment: bool,
                     include_capex_installation: bool, include_opex: bool,
                     labda: float) -> Tuple[arcpy.Raster, arcpy.Raster, arcpy.Raster, arcpy.Raster]:
    # Calculate Capex Equipment, Capex Installation, Opex, and Capex
    capex_equipment = arcpy.sa.Null()
    capex_installation = arcpy.sa.Null()
    opex = arcpy.sa.Null()
    capex = arcpy.sa.Null()

    if include_capex_equipment:
        capex_equipment = calc_equipment_costs(raster, year, support_structure, n_wind_turbines, WT_rated_power)

    if include_capex_installation:
        capex_installation = calc_installation_costs(raster, support_structure, port_distance, n_wind_turbines, WT_rated_power)

    if include_opex:
        opex = calc_operation_costs(support_structure, n_wind_turbines, raster, labda)

    if include_capex_equipment and include_capex_installation:
        capex = capex_equipment + capex_installation

    return capex_equipment, capex_installation, opex, capex


def calc_raster(year: str, raster_path: str, output_folder: str, shapefile: str,
                water_depth_1: float, water_depth_2: float, water_depth_3: float,
                water_depth_4: float, WT_rated_power: float,
                n_wind_turbines: int, include_capex_equipment: bool,
                include_capex_installation: bool, include_opex: bool,
                labda: float) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    # Clear the output folder
    clear_output_folder(output_folder)

    # Clip the input raster based on the shapefile
    clipped_raster = os.path.join(output_folder, "clipped_raster.tif")
    arcpy.Clip_management(raster_path, "#", clipped_raster, shapefile, "-9999", "ClippingGeometry")

    # Load the clipped raster and calculate the negative water depth
    raster = arcpy.sa.Raster(clipped_raster)
    water_depth = -raster

    # Initialize variables
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
                    capex_equipment, capex_installation, opex, capex = calc_total_costs(masked_raster, year, support_structure, port_distance, n_wind_turbines, WT_rated_power, include_capex_equipment, include_opex, include_capex_installation, labda)

                    if capex is not None:
                        # Apply additional conditions to the costs raster
                        capex = arcpy.sa.Con((capex >= 0) & (capex <= 1E9), capex)
                        # Define output paths for separate raster layers
                        capex_equipment_output_raster = os.path.join(output_folder, f"{support_structure}_capex_equipment.tif")
                        capex_installation_output_raster = os.path.join(output_folder, f"{support_structure}_capex_installation.tif")
                        opex_output_raster = os.path.join(output_folder, f"{support_structure}_opex.tif")
                        capex_output_raster = os.path.join(output_folder, f"{support_structure}_capex.tif")

                        # Save separate raster layers for Capex Equipment, Capex Installation, and Opex
                        if include_capex_equipment:
                            arcpy.Clip_management(capex_equipment, "#", capex_equipment_output_raster, shapefile, "0", "ClippingGeometry")
                        if include_capex_installation:
                            arcpy.Clip_management(capex_installation, "#", capex_installation_output_raster, shapefile, "0", "ClippingGeometry")
                        if include_opex:
                            arcpy.Clip_management(opex, "#", opex_output_raster, shapefile, "0", "ClippingGeometry")

                        # Calculate and save Capex (sum of Capex Equipment and Capex Installation)
                        if include_capex_equipment and include_capex_installation:
                            capex = capex_equipment + capex_installation
                            arcpy.Clip_management(capex, "#", capex_output_raster, shapefile, "0", "ClippingGeometry")

                        # Set the flag to indicate a valid raster was found
                        valid_rasters_found = True

    if valid_rasters_found:
        # Combine separate raster layers into a single total raster layer
        capex_equipment_total_raster = arcpy.sa.CellStatistics([capex_equipment_output_raster], "SUM", "DATA") if include_capex_equipment else None
        capex_installation_total_raster = arcpy.sa.CellStatistics([capex_installation_output_raster], "SUM", "DATA") if include_capex_installation else None
        opex_total_raster = arcpy.sa.CellStatistics([opex_output_raster], "SUM", "DATA") if include_opex else None
        capex_total_raster = arcpy.sa.CellStatistics([capex_output_raster], "SUM", "DATA") if include_capex_equipment and include_capex_installation else None

        # Define the output paths for the total raster layers
        capex_equipment_total_output_raster = os.path.join(output_folder, "support_structure_capex_equipment.tif") if include_capex_equipment else None
        capex_installation_total_output_raster = os.path.join(output_folder, "support_structure_capex_installation.tif") if include_capex_installation else None
        opex_total_output_raster = os.path.join(output_folder, "support_structure_opex.tif") if include_opex else None
        capex_total_output_raster = os.path.join(output_folder, "support_structure_capex.tif") if include_capex_equipment and include_capex_installation else None

        # Save the combined raster layers
        if include_capex_equipment:
            arcpy.Clip_management(capex_equipment_total_raster, "#", capex_equipment_total_output_raster, shapefile, "0", "ClippingGeometry")
        if include_capex_installation:
            arcpy.Clip_management(capex_installation_total_raster, "#", capex_installation_total_output_raster, shapefile, "0", "ClippingGeometry")
        if include_opex:
            arcpy.Clip_management(opex_total_raster, "#", opex_total_output_raster, shapefile, "0", "ClippingGeometry")
        if include_capex_equipment and include_capex_installation:
            arcpy.Clip_management(capex_total_raster, "#", capex_total_output_raster, shapefile, "0", "ClippingGeometry")

        # Return the paths of the total raster layers
        return capex_equipment_total_output_raster, capex_installation_total_output_raster, opex_total_output_raster, capex_total_output_raster
    else:
        # Return None for all paths if no valid rasters were found
        return None, None, None, None


def add_all_rasters_to_map(output_folder: str, map_frame_name: str) -> None:
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
    # Prompt the user for the necessary parameters
    year: str = arcpy.GetParameterAsText(0)
    raster_path: str = arcpy.GetParameterAsText(1)
    output_folder: str = arcpy.GetParameterAsText(2)
    shapefile: str = arcpy.GetParameterAsText(3)
    water_depth_1, water_depth_2, water_depth_3, water_depth_4 = map(float, [arcpy.GetParameterAsText(i) for i in range(4, 8)])
    n_wind_turbines: int = int(arcpy.GetParameterAsText(8))
    project_path: str = arcpy.GetParameterAsText(9) 
    map_frame_name: str = arcpy.GetParameterAsText(10)
    port_distance: float = float(arcpy.GetParameterAsText(11))
    WT_rated_power: float = float(arcpy.GetParameterAsText(12))
    include_install_costs: bool = arcpy.GetParameter(13)

    result_raster: Tuple[Optional[str], Optional[str], Optional[str], Optional[str]] = calc_raster(year, raster_path, output_folder, shapefile, water_depth_1, water_depth_2, water_depth_3, water_depth_4, WT_rated_power, n_wind_turbines, include_install_costs)

    if result_raster is not None:
        add_all_rasters_to_map(output_folder, map_frame_name)
        arcpy.AddMessage("All raster layers added to the map.")
    else:
        arcpy.AddMessage("No valid rasters found.")
