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
    inst_year = 0  # First year
    ope_year = inst_year + 5
    dec_year = ope_year + 25  
    end_year = dec_year + 2  # End year

    # Discount rate
    discount_rate = 0.05

    # Define the years as a function of inst_year and end_year
    years = range(inst_year, end_year + 1)

    # Initialize total operational cost
    ope_cost = 0

    # Adjust cost for each year
    for year in years:
        # Adjust installation cost
        if year == inst_year:
            equip_cost *= (1 + discount_rate) ** -year
            inst_cost *= (1 + discount_rate) ** -year
        # Adjust operational cost
        if year >= inst_year and year < ope_year:
            inst_cost *= (1 + discount_rate) ** -year
        elif year >= ope_year and year < dec_year:
            ope_cost_yearly *= (1 + discount_rate) ** -year
            ope_cost += ope_cost_yearly  # Accumulate yearly operational cost
        # Adjust decommissioning cost
        if year >= dec_year and year <= end_year:
            deco_cost *= (1 + discount_rate) ** -year

    # Calculate total present value of cost
    total_cost = equip_cost + inst_cost + ope_cost + deco_cost

    return total_cost

def iac_cost_lin(length, capacity):
    """
    Calculate the total cost of an inter array cable section for a given length and desired capacity.

    Parameters:
        length (float): The length of the cable (in meters).
        capacity (float): Cable capacity (in MW).

    Returns:
        float: Total cost associated with the selected HVAC cables in millions of euros.
    """
    cable_length = 1.05 * length
    cable_capacity = 80 # MW
    cable_equip_cost = 152 # eu/m
    cable_inst_cost = 114 # eu/m
    capacity_factor = 0.98
    
    parallel_cables = np.ceil(capacity / (cable_capacity * capacity_factor))
    
    equip_cost = parallel_cables * cable_length * cable_equip_cost
    inst_cost = parallel_cables * cable_length * cable_inst_cost
    
    ope_cost_yearly = 0.2 * 1e-2 * equip_cost
    
    deco_cost = 0.5 * inst_cost

    # Calculate present value
    total_cost = present_value(equip_cost, inst_cost, ope_cost_yearly, deco_cost)

    return total_cost * 10e-6 # total cost in millions of euros

def update_inter_array_cable_costs():
    """
    Update the inter_array_cables feature layer with the calculated costs for each cable section.
    """
    # Get the current map
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map = aprx.activeMap

    # Find the inter-array cable layer in the map
    iac_layer = next((layer for layer in map.listLayers() if layer.name.startswith('IAC')), None)

    # Check if the inter-array cable layer exists
    if not iac_layer:
        arcpy.AddError("No layer starting with 'IAC' found in the current map.")
        return

    # Add a new field for total cost if it doesn't exist
    if "TotalCost" not in [field.name for field in arcpy.ListFields(iac_layer)]:
        arcpy.AddField_management(iac_layer, "TotalCost", "DOUBLE")

    # Update the attribute table with the calculated costs
    with arcpy.da.UpdateCursor(iac_layer, ["Length", "Capacity", "TotalCost"]) as cursor:
        for row in cursor:
            length = row[0]
            capacity = row[1]
            total_cost = iac_cost_lin(length, capacity)
            row[2] = total_cost
            cursor.updateRow(row)

if __name__ == "__main__":
    update_inter_array_cable_costs()
    print("Inter-array cable costs updated.")
