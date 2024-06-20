import arcpy
import os
from scripts.present_value import present_value_single
from scripts.wt_cost import check_supp, calc_equip_cost, calc_inst_deco_cost

def calculate_costs(first_year, water_depth, ice_cover, port_distance, turbine_capacity):
    """
    Calculate various costs for a given set of parameters.

    Parameters:
        first_year (int): The year of installation (2030, 2040, or 2050).
        water_depth (float): Water depth at the turbine location.
        ice_cover (int): Indicator if the area is ice-covered (1 for Yes, 0 for No).
        port_distance (float): Distance to the port.
        turbine_capacity (float): Capacity of the turbine.

    Returns:
        tuple: Total cost, equipment cost, installation cost, total operational cost, decommissioning cost in millions of Euros.
    """
    support_structure = check_supp(water_depth)  # Determine support structure

    supp_cost, turbine_cost = calc_equip_cost(first_year, water_depth, support_structure, ice_cover, turbine_capacity)  # Calculate equipment cost

    equip_cost = supp_cost + turbine_cost
    
    inst_cost = calc_inst_deco_cost(water_depth, port_distance, turbine_capacity, "installation")  # Calculate installation cost
    deco_cost = calc_inst_deco_cost(water_depth, port_distance, turbine_capacity, "decommissioning")  # Calculate decommissioning cost

    ope_cost_yearly = 0.025 * turbine_cost  # Calculate yearly operational cost

    total_cost = present_value_single(first_year, equip_cost, inst_cost, ope_cost_yearly, deco_cost)  # Calculate present value of cost

    return total_cost

def update_fields():
    """
    Function to update the fields in the wind turbine layer with calculated total cost.
    """
    # Get the current map
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map = aprx.activeMap
    
    # Find the wind turbine layer in the map
    turbine_layer = next((layer for layer in map.listLayers() if layer.name.startswith('WTC')), None)
    
    # Check if the turbine layer exists
    if not turbine_layer:
        arcpy.AddError("No layer starting with 'WTC' found in the current map.")
        return

    # Deselect all currently selected features
    arcpy.SelectLayerByAttribute_management(turbine_layer, "CLEAR_SELECTION")
    
    arcpy.AddMessage(f"Processing layer: {turbine_layer.name}")

    # Check if required fields exist in the attribute table using a search cursor
    required_fields = ['WaterDepth', 'Capacity', 'Distance', 'IceCover']
    existing_fields = []
    
    with arcpy.da.SearchCursor(turbine_layer, ["*"]) as cursor:
        existing_fields = cursor.fields
    
    for field in required_fields:
        if field not in existing_fields:
            arcpy.AddError(f"Required field '{field}' is missing in the attribute table.")
            return

    # Check if TotalCost fields exist for 2030, 2040, and 2050, create them if they don't
    total_cost_fields = ['TC_2030', 'TC_2040', 'TC_2050']
    for total_cost_field in total_cost_fields:
        if total_cost_field not in existing_fields:
            arcpy.AddField_management(turbine_layer, total_cost_field, "DOUBLE")
            arcpy.AddMessage(f"Field '{total_cost_field}' added to the attribute table.")

    # Calculate the total cost for each feature and update the attribute table
    with arcpy.da.UpdateCursor(turbine_layer, ['WaterDepth', 'Capacity', 'Distance', 'IceCover'] + total_cost_fields) as cursor:
        for row in cursor:
            water_depth = row[0]
            turbine_capacity = row[1]
            port_distance = row[2] * 1e-3 # port distance in km
            ice_cover = 1 if row[3] == 'Yes' else 0

            total_cost_2030 = calculate_costs(2030, water_depth, ice_cover, port_distance, turbine_capacity)
            total_cost_2040 = calculate_costs(2040, water_depth, ice_cover, port_distance, turbine_capacity)
            total_cost_2050 = calculate_costs(2050, water_depth, ice_cover, port_distance, turbine_capacity)

            row[4] = round(total_cost_2030, 3)
            row[5] = round(total_cost_2040, 3)
            row[6] = round(total_cost_2050, 3)

            cursor.updateRow(row)

if __name__ == "__main__":
    update_fields()