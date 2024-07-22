import arcpy
import numpy as np
from scripts.present_value import present_value_single
from scripts.eh_cost import check_supp, equip_cost_lin, inst_deco_cost_lin

def oss_cost_lin(first_year, water_depth, ice_cover, port_distance, eh_capacity):
    """
    Estimate the cost associated with an energy hub based on various parameters.

    Parameters:
    - water_depth (float): Water depth at the location of the energy hub.
    - ice_cover (int): Indicator of ice cover presence (1 for presence, 0 for absence).
    - port_distance (float): Distance from the offshore location to the nearest port.
    - eh_capacity (float): Capacity of the energy hub.
    - polarity (str, optional): Polarity of the substation ('AC' or 'DC'). Defaults to 'AC'.

    Returns:
    - float: Estimated total cost of the energy hub.
    """

    # Determine support structure
    supp_structure = check_supp(water_depth)
    
    # Calculate equipment cost
    conv_cost, equip_cost = equip_cost_lin(water_depth, supp_structure, ice_cover, eh_capacity)

    # Calculate installation and decommissioning cost
    inst_cost = inst_deco_cost_lin(supp_structure, port_distance, "inst")
    deco_cost = inst_deco_cost_lin(supp_structure, port_distance, "deco")

    # Calculate yearly operational cost
    ope_cost_yearly = 0.03 * conv_cost
    
    # Calculate present value of cost    
    oss_cost = present_value_single(first_year, equip_cost, inst_cost, ope_cost_yearly, deco_cost)
    
    return oss_cost

def update_fields():
    """
    Update the attribute table of the OSSC feature layer with the calculated TotalCost and TotalCapacity.
    """
    # Access the current ArcGIS project
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map = aprx.activeMap

    # Find the offshore substation layer
    oss_layer = [layer for layer in map.listLayers() if layer.name.startswith('OSSC')]

    # Check if any OSSC layer exists
    if not oss_layer:
        arcpy.AddError("No layer starting with 'OSSC' found in the current map.")
        return
    
    # Find the wind farm coordinates layer
    wtc_layer = [layer for layer in map.listLayers() if layer.name.startswith('WTC')]

    # Check if any WTC layer exists
    if not wtc_layer:
        arcpy.AddError("No layer starting with 'WTC' found in the current map.")
        return

    # Select the first OSSC layer and WTC layer
    oss_layer = oss_layer[0]
    wtc_layer = wtc_layer[0]

    # Deselect all currently selected features
    arcpy.SelectLayerByAttribute_management(oss_layer, "CLEAR_SELECTION")

    arcpy.AddMessage(f"Processing layer: {oss_layer.name}")

    # Check if required fields exist in OSSC layer
    required_fields_oss = ['WF_ID', 'ISO', 'Longitude', 'Latitude', 'WaterDepth', 'IceCover', 'Distance']
    for field in required_fields_oss:
        if field not in [f.name for f in arcpy.ListFields(oss_layer)]:
            arcpy.AddError(f"Required field '{field}' is missing in the OSSC attribute table.")
            return

    # Check if required fields exist in WTC layer
    required_fields_wtc = ['WF_ID', 'Capacity']
    for field in required_fields_wtc:
        if field not in [f.name for f in arcpy.ListFields(wtc_layer)]:
            arcpy.AddError(f"Required field '{field}' is missing in the WTC attribute table.")
            return

    # Add new fields for TotalCapacity and TotalCost if they don't already exist
    if 'TotalCapacity' not in [f.name for f in arcpy.ListFields(oss_layer)]:
        arcpy.AddField_management(oss_layer, 'TotalCap', 'DOUBLE')
    
    if 'TotalCost' not in [f.name for f in arcpy.ListFields(oss_layer)]:
        arcpy.AddField_management(oss_layer, 'TotalCost', 'DOUBLE')

    # Create a dictionary to store the sum of Capacities for each WF_ID
    wf_id_to_capacity = {}

    # Calculate the sum of Capacities for each WF_ID in the WTC layer
    with arcpy.da.SearchCursor(wtc_layer, ['WF_ID', 'Capacity']) as cursor:
        for row in cursor:
            wf_id = row[0]
            capacity = row[1]
            if wf_id in wf_id_to_capacity:
                wf_id_to_capacity[wf_id] += capacity
            else:
                wf_id_to_capacity[wf_id] = capacity

    # Create an update cursor to calculate and update the TotalCapacity and TotalCost for each feature in the OSSC layer
    with arcpy.da.UpdateCursor(oss_layer, ['WaterDepth', 'IceCover', 'Distance', 'WF_ID', 'TotalCap', 'TotalCost']) as cursor:
        for row in cursor:
            water_depth = row[0]
            ice_cover = row[1]
            port_distance = row[2]
            wf_id = row[3]

            # Get the oss_capacity from the dictionary
            oss_capacity = wf_id_to_capacity.get(wf_id, 0)

            # Calculate the total cost using the oss_cost_lin function if oss_capacity is not zero
            total_cost = oss_cost_lin(water_depth, ice_cover, port_distance, oss_capacity) if oss_capacity > 0 else 0

            # Update the TotalCapacity and TotalCost fields
            row[4] = oss_capacity
            row[5] = round(total_cost, 3)
            cursor.updateRow(row)

    arcpy.AddMessage("TotalCapacity and TotalCost fields updated successfully.")

# Call the update_fields function
update_fields()







