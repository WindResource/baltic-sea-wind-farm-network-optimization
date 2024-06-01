import arcpy
import numpy as np

def present_value(equip_cost, inst_cost, ope_cost_yearly, deco_cost):
    """
    Calculate the total present value of cable cost.

    Parameters:
        equip_cost (float): Equipment cost.
        inst_cost (float): Installation cost.
        ope_cost_yearly (float): Yearly operational cost.
        deco_cost (float): Decommissioning cost.

    Returns:
        float: Total present value of cost.
    """
    # Define years for installation, operational, and decommissioning
    inst_year = 0  # First year (installation year)
    ope_year = inst_year + 5  # Operational costs start year
    dec_year = ope_year + 25  # Decommissioning year
    end_year = dec_year + 2  # End year

    # Discount rate
    discount_rate = 0.05

    # Initialize total operational cost
    total_ope_cost = 0

    # Adjust cost for each year
    for year in range(inst_year, end_year + 1):
        discount_factor = (1 + discount_rate) ** -year  # Calculate the discount factor for the year
        if year == inst_year:
            equip_cost *= discount_factor  # Discount equipment cost for the installation year
            inst_cost *= discount_factor  # Discount installation cost for the installation year
        elif ope_year <= year < dec_year:
            total_ope_cost += ope_cost_yearly * discount_factor  # Accumulate discounted operational cost for each year
        elif year == dec_year:
            deco_cost *= discount_factor  # Discount decommissioning cost for the decommissioning year

    # Calculate total present value of cost
    total_cost = equip_cost + inst_cost + total_ope_cost + deco_cost

    return total_cost

def oss_cost_lin(water_depth, ice_cover, port_distance, oss_capacity):
    """
    Estimate the cost associated with an offshore substation based on various parameters.

    Parameters:
    - water_depth (float): Water depth at the location of the offshore substation.
    - ice_cover (int): Indicator of ice cover presence (1 for presence, 0 for absence).
    - port_distance (float): Distance from the offshore location to the nearest port.
    - oss_capacity (float): Capacity of the offshore substation.
    - polarity (str, optional): Polarity of the substation ('AC' or 'DC'). Defaults to 'AC'.

    Returns:
    - float: Estimated total cost of the offshore substation.
    """
    
    def supp_struct_cond(water_depth):
        """
        Determines the support structure type based on water depth.

        Returns:
        - str: Support structure type ('monopile', 'jacket', 'floating', or 'default').
        """
        # Define depth ranges for different support structures
        if water_depth < 150:
            return "jacket"
        elif 150 <= water_depth:
            return "floating"

    def equip_cost_lin(water_depth, support_structure, ice_cover, oss_capacity):
        """
        Calculates the offshore substation equipment cost based on water depth, capacity, and export cable type.

        Returns:
        - float: Calculated equipment cost.
        """
        # Coefficients for equipment cost calculation based on the support structure and year
        support_structure_coeff = {
            'jacket': (233, 47, 309, 62),
            'floating': (87, 68, 116, 91)
        }

        equip_coeff = (22.87, 7.06)
        
        # Define parameters
        c1, c2, c3, c4 = support_structure_coeff[support_structure]
        
        c5, c6 = equip_coeff
        
        # Define equivalent electrical power
        equiv_capacity = 0.5 * oss_capacity

        # Calculate foundation cost for jacket/floating
        supp_cost = (c1 * water_depth + c2 * 1000) * equiv_capacity + (c3 * water_depth + c4 * 1000)
        
        # Add support structure cost for ice cover adaptation
        supp_cost = 1.10 * supp_cost if ice_cover == 1 else supp_cost
        
        # Power converter cost
        conv_cost = c5 * oss_capacity * int(1e3) + c6 * int(1e6) #* int(1e3)
        
        # Calculate equipment cost
        equip_cost = supp_cost + conv_cost
        
        return conv_cost, equip_cost

    def inst_deco_cost_lin(support_structure, port_distance, operation):
        """
        Calculate installation or decommissioning cost of offshore substations based on the water depth, and port distance.

        Returns:
        - float: Calculated installation or decommissioning cost.
        """
        # Installation coefficients for different vehicles
        inst_coeff = {
            ('jacket' 'PSIV'): (1, 18.5, 24, 96, 200),
            ('floating','HLCV'): (1, 22.5, 10, 0, 40),
            ('floating','AHV'): (3, 18.5, 30, 90, 40)
        }

        # Decommissioning coefficients for different vehicles
        deco_coeff = {
            ('jacket' 'PSIV'): (1, 18.5, 24, 96, 200),
            ('floating','HLCV'): (1, 22.5, 10, 0, 40),
            ('floating','AHV'): (3, 18.5, 30, 30, 40)
        }

        # Choose the appropriate coefficients based on the operation type
        coeff = inst_coeff if operation == 'inst' else deco_coeff
            
        if support_structure == 'jacket':
            c1, c2, c3, c4, c5 = coeff[('jacket' 'PSIV')]
            # Calculate installation cost for jacket
            total_cost = ((1 / c1) * ((2 * port_distance) / c2 + c3) + c4) * (c5 * 1000) / 24
        elif support_structure == 'floating':
            total_cost = 0
            
            # Iterate over the coefficients for floating (HLCV and AHV)
            for vessel_type in [('floating', 'HLCV'), ('floating', 'AHV')]:
                c1, c2, c3, c4, c5 = coeff[vessel_type]
                # Calculate installation cost for the current vessel type
                vessel_cost = ((1 / c1) * ((2 * port_distance) / c2 + c3) + c4) * (c5 * 1000) / 24
                # Add the cost for the current vessel type to the total cost
                total_cost += vessel_cost
        
        return total_cost

    # Determine support structure
    supp_structure = supp_struct_cond(water_depth)
    
    # Calculate equipment cost
    conv_cost, equip_cost = equip_cost_lin(water_depth, supp_structure, ice_cover, oss_capacity)

    # Calculate installation and decommissioning cost
    inst_cost = inst_deco_cost_lin(supp_structure, port_distance, "inst")
    deco_cost = inst_deco_cost_lin(supp_structure, port_distance, "deco")

    # Calculate yearly operational cost
    ope_cost_yearly = 0.03 * conv_cost
    
    # Calculate present value of cost    
    oss_cost = present_value(equip_cost, inst_cost, ope_cost_yearly, deco_cost)
    
    # Offshore substation cost in million Euros
    oss_cost *= 1e-6
    
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







