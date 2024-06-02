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

def iac_cost_lin(distance, capacity):
    """
    Calculate the total cost of an inter array cable section for a given distance and desired capacity.

    Parameters:
        distance (float): The distance of the cable (in meters).
        capacity (float): Cable capacity (in MW).

    Returns:
        float: Total cost associated with the selected HVAC cables in millions of euros.
    """
    cable_length = 1.05 * distance
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

    return total_cost

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
    with arcpy.da.UpdateCursor(iac_layer, ["Distance", "Capacity", "TotalCost"]) as cursor:
        for row in cursor:
            distance = row[0]
            capacity = row[1]
            total_cost = iac_cost_lin(distance, capacity)
            row[2] = round(total_cost * 1e-6, 3) # Cost in millions of EU
            cursor.updateRow(row)

if __name__ == "__main__":
    update_inter_array_cable_costs()
    print("Inter-array cable costs updated.")
