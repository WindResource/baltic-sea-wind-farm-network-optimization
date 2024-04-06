"""
Calculate installation or decommissioning costs of offshore substations based on the water depth, and port distance.

Parameters:
- water_depth (float): Water depth at the installation site, in meters.
- port_distance (float): Distance from the installation site to the nearest port, in kilometers.
- oss_capacity (float): Capacity of the offshore substation, in units.
- HVC_type (str, optional): Type of high-voltage converter ('AC' or 'DC'). Defaults to 'AC'.
- operation (str, optional): Type of operation ('inst' for installation or 'deco' for decommissioning). Defaults to 'inst'.

Returns:
- float: Calculated installation or decommissioning costs in Euros.

Coefficients:
- Capacity (u/lift): Capacity of the vessel in units per lift.
- Speed (km/h): Speed of the vessel in kilometers per hour.
- Load time (h/lift): Load time per lift in hours per lift.
- Inst. time (h/u): Installation time per unit in hours per unit.
- Dayrate (keu/d): Dayrate of the vessel in thousands of euros per day.

Vessels:
- SUBV (Self-Unloading Bulk Vessels)
- SPIV (Self-Propelled Installation Vessel)
- HLCV (Heavy-Lift Cargo Vessels)
- AHV (Anchor Handling Vessel)

Notes:
- The function supports both installation and decommissioning operations.
- Costs are calculated based on predefined coefficients for different support structures and vessels.
- If the support structure is unrecognized, the function returns None.
"""
"""
Calculate logistics time and costs for major wind turbine repairs (part of OPEX) based on water depth, port distance, and failure rate for major wind turbine repairs.

Coefficients:
    - Speed (km/h): Speed of the vessel in kilometers per hour.
    - Repair time (h): Repair time in hours.
    - Dayrate (keu/d): Dayrate of the vessel in thousands of euros per day.
    - Roundtrips: Number of roundtrips for the logistics operation.

Returns:
- tuple: Logistics time in hours per year and logistics costs in Euros.
"""
"""
Add new fields to the attribute table if they do not exist.

Parameters:
- layer: The layer to which fields will be added.
- fields_to_add: A list of tuples containing field definitions. Each tuple should contain:
    - Field name (str): The name of the field.
    - Field type (str): The data type of the field.
    - Field label (str): The label or description of the field.

Returns:
None
"""

import arcpy
import numpy as np
import os
import matplotlib.pyplot as plt

def plot_capital_expenses():
    """
    Plot the capital expenses for different support structures and export cable types based on predefined water depths, capacities, and HVC types.
    Save each plot to a separate file in the specified output folder.

    Returns:
    - None
    """
    # Specify the output folder where the plot image will be saved
    output_folder = arcpy.GetParameterAsText(0)
    
    water_depths = np.arange(0, 50, step=1)  # Water depths with a step of 1 meter
    capacities = [500, 750, 1000, 1250, 1500]  # Capacities in MW
    HVC_types = ['AC', 'DC']  # Export cable types AC and DC
    port_distance = 1000  # Port distance in meters
    
    # Initialize lists to store capital expenses for each support structure, capacity, and export cable type
    support_structures = ['sandisland', 'jacket', 'floating']
    colors = {'AC': ['blue', 'orange', 'green'], 'DC': ['lightblue', 'lightsalmon', 'lightgreen']}
    
    legend_order = ['Sandisland (AC)', 'Sandisland (DC)', 'Jacket (AC)', 'Jacket (DC)', 'Floating (AC)', 'Floating (DC)']
    
    for capacity in capacities:
        plt.figure(figsize=(12, 8))
        
        for HVC_type in HVC_types:
            for index, support_structure in enumerate(support_structures):
                capital_expenses = []
                
                for depth in water_depths:
                    # Calculate equipment costs for each support structure, capacity, and export cable type
                    equip_costs = calc_equip_costs(depth, support_structure, capacity, HVC_type)
                    
                    # Calculate installation costs for each support structure, capacity, and export cable type
                    inst_costs = calc_costs(depth, support_structure, port_distance, capacity, HVC_type, operation="installation")
                    
                    # Calculate total capital expenses (equipment costs + installation costs)
                    total_costs = (equip_costs + inst_costs) / int(1e6)
                    
                    capital_expenses.append(total_costs)
                
                # Plot the capital expenses for the current support structure, capacity, and export cable type
                label = f"{support_structure.capitalize()} ({HVC_type})"
                plt.plot(water_depths, capital_expenses, label=label, color=colors[HVC_type][index])
        
        # Customize the plot
        plt.xlabel('Water Depth (m)')
        plt.ylabel('Capital Expenses (Million EU)')
        plt.title(f'Capital Expenses vs. Water Depth for Capacity {capacity} MW')
        plt.legend()
        plt.grid(True)
        
        # Sort the legend entries
        handles, labels = plt.gca().get_legend_handles_labels()
        sorted_handles = [handles[labels.index(label)] for label in legend_order]
        sorted_labels = [label for label in legend_order]
        
        # Display the legend with sorted entries
        plt.legend(sorted_handles, sorted_labels)
        
        # Set minor gridlines for every 1 meter of water depth
        plt.minorticks_on()
        plt.xticks(np.arange(0, 50, 5))  # Set major ticks every 5 meters
        plt.xticks(np.arange(0, 50, 1), minor=True)  # Set minor ticks every 1 meter
        plt.grid(which='both', linestyle=':', linewidth='0.5', color='gray')
                
        # Set the limits for both axes to start from 0
        plt.xlim(0)  # Water depth range
        plt.ylim(0)  # Capital expenses range
        
        # Save the plot to the specified output folder
        output_file = os.path.join(output_folder, f"capital_expenses_plot_capacity_{capacity}.png")
        plt.savefig(output_file)
        
        # Clear the plot to release memory
        plt.close()
        
    arcpy.AddMessage(f"Figures saved succesfully.")
    
def determine_support_structure(water_depth):
    """
    Determines the support structure type based on water depth.

    Returns:
    - str: Support structure type ('monopile', 'jacket', 'floating', or 'default').
    """
    # Define depth ranges for different support structures
    if 0 <= water_depth < 30:
        return "sandisland"
    elif 30 <= water_depth < 150:
        return "jacket"
    elif 150 <= water_depth:
        return "floating"
    else:
        # If water depth is outside specified ranges, assign default support structure
        arcpy.AddWarning(f"Water depth {water_depth} does not fall within specified ranges for support structures. Assigning default support structure.")
        return "default"

def calc_equip_costs(water_depth, support_structure, oss_capacity, HVC_type="AC"):
    """
    Calculates the offshore substation equipment costs based on water depth, capacity, and export cable type.

    Returns:
    - float: Calculated equipment costs.
    """
    # Coefficients for equipment cost calculation based on the support structure and year
    support_structure_coeff = {
        'sandisland': (3.26, 804, 0, 0),
        'jacket': (233, 47, 309, 62),
        'floating': (87, 68, 116, 91)
    }

    equip_coeff = {
        'AC': (22.87, 7.06),
        'DC': (102.93, 31.75)
    }
    
    # Define parameters
    c1, c2, c3, c4 = support_structure_coeff[support_structure]
    
    c5, c6 = equip_coeff[HVC_type]
    
    # Define equivalent electrical power
    equiv_capacity = 0.5 * oss_capacity if HVC_type == "AC" else oss_capacity

    if support_structure == 'sandisland':
        # Calculate foundation costs for sand island
        area_island = (equiv_capacity * 5)
        slope = 0.75
        r_hub = np.sqrt(area_island/np.pi)
        r_seabed = r_hub + (water_depth + 3) / slope
        volume_island = (1/3) * slope * np.pi * (r_seabed ** 3 - r_hub ** 3)
        
        supp_costs = c1 * volume_island + c2 * area_island
    else:
        # Calculate foundation costs for jacket/floating
        supp_costs = (c1 * water_depth + c2 * 1000) * equiv_capacity + (c3 * water_depth + c4 * 1000)
    
    # Power converter costs
    conv_costs = c5 * oss_capacity * int(1e3) + c6 * int(1e6) #* int(1e3)
    equip_costs = supp_costs + conv_costs
    
    return supp_costs, conv_costs, equip_costs

def calc_costs(water_depth, support_structure, port_distance, oss_capacity, HVC_type = "AC", operation = "inst"):
    """
    Calculate installation or decommissioning costs of offshore substations based on the water depth, and port distance.

    Returns:
    - float: Calculated installation or decommissioning costs.
    """
    # Installation coefficients for different vehicles
    inst_coeff = {
        ('sandisland','SUBV'): (20000, 25, 2000, 6000, 15),
        ('jacket' 'PSIV'): (1, 18.5, 24, 96, 200),
        ('floating','HLCV'): (1, 22.5, 10, 0, 40),
        ('floating','AHV'): (3, 18.5, 30, 90, 40)
    }

    # Decommissioning coefficients for different vehicles
    deco_coeff = {
        ('sandisland','SUBV'): (20000, 25, 2000, 6000, 15),
        ('jacket' 'PSIV'): (1, 18.5, 24, 96, 200),
        ('floating','HLCV'): (1, 22.5, 10, 0, 40),
        ('floating','AHV'): (3, 18.5, 30, 30, 40)
    }

    # Choose the appropriate coefficients based on the operation type
    coeff = inst_coeff if operation == 'inst' else deco_coeff

    if support_structure == 'sandisland':
        c1, c2, c3, c4, c5 = coeff[('sandisland','SUBV')]
        # Define equivalent electrical power
        equiv_capacity = 0.5 * oss_capacity if HVC_type == "AC" else oss_capacity
        
        # Calculate installation costs for sand island
        area_island = (equiv_capacity * 5)
        slope = 0.75
        r_hub = np.sqrt(area_island/np.pi)
        r_seabed = r_hub + (water_depth + 3) / slope
        volume_island = (1/3) * slope * np.pi * (r_seabed ** 3 - r_hub ** 3)
        
        total_costs = ((volume_island / c1) * ((2 * port_distance) / c2) + (volume_island / c3) + (volume_island / c4)) * (c5 * 1000) / 24
        arcpy.AddMessage(f"1 {volume_island}")
    elif support_structure == 'jacket':
        c1, c2, c3, c4, c5 = coeff[('jacket' 'PSIV')]
        # Calculate installation costs for jacket
        total_costs = ((1 / c1) * ((2 * port_distance) / c2 + c3) + c4) * (c5 * 1000) / 24
    elif support_structure == 'floating':
        total_costs = 0
        
        # Iterate over the coefficients for floating (HLCV and AHV)
        for vessel_type in [('floating', 'HLCV'), ('floating', 'AHV')]:
            c1, c2, c3, c4, c5 = coeff[vessel_type]
            
            # Calculate installation costs for the current vessel type
            vessel_costs = ((1 / c1) * ((2 * port_distance) / c2 + c3) + c4) * (c5 * 1000) / 24
            
            # Add the costs for the current vessel type to the total costs
            total_costs += vessel_costs
    else:
        total_costs = None
        
    return total_costs

def update_fields():
    """
    Update the attribute table of the Offshore SubStation Coordinates (OSSC) layer.

    Returns:
    - None
    """
    # Function to add a field if it does not exist in the layer
    def add_field_if_not_exists(layer, field_name, field_type):
        if field_name not in [field.name for field in arcpy.ListFields(layer)]:
            arcpy.AddField_management(layer, field_name, field_type)
    
    # Define the capacities for which fields are to be added
    capacities = [500, 750, 1000, 1250, 1500, 1750, 2000, 2250, 2500]

    # Define the expense categories
    expense_categories = ['Sup', 'Cnv', 'Equ', 'Ins', 'Cap', 'Ope', 'Dec'] # Equipment costs, Installation costs, Capital expenses, Operating expenses, decommissioning expenses

    # Define fields to be added if they don't exist
    fields_to_add = [('SuppStruct', 'TEXT')]

    # Generate field definitions for each capacity and expense category for both AC and DC
    for capacity in capacities:
        for category in expense_categories:
            for sub_type in ['AC', 'DC']:
                field_name = f'{category}{capacity}_{sub_type}'
                fields_to_add.append((field_name, 'DOUBLE'))

    # Access the current ArcGIS project
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map = aprx.activeMap

    # Find the offshore substation layer
    oss_layers = [layer for layer in map.listLayers() if layer.name.startswith('OSSC')]

    # Check if any OSSC layer exists
    if not oss_layers:
        arcpy.AddError("No layer starting with 'OSSC' found in the current map.")
        return

    # Select the first OSSC layer
    oss_layer = oss_layers[0]

    # Deselect all currently selected features
    arcpy.SelectLayerByAttribute_management(oss_layer, "CLEAR_SELECTION")

    arcpy.AddMessage(f"Processing layer: {oss_layer.name}")

    # Check if required fields exist in the attribute table
    fields = arcpy.ListFields(oss_layer)
    field_names = {field.name for field in fields}
    required_fields = ['WaterDepth', 'Distance']
    for field in required_fields:
        if field not in field_names:
            arcpy.AddError(f"Required field '{field}' is missing in the attribute table.")
            return

    # Add new fields to the attribute table if they do not exist
    for field_name, field_type in fields_to_add:
        add_field_if_not_exists(oss_layer, field_name, field_type)

    # Update each row in the attribute table
    with arcpy.da.UpdateCursor(oss_layer, [field.name for field in fields]) as cursor:
        for row in cursor:
            water_depth = row[field_names.index("WaterDepth")]
            port_distance = row[field_names.index("Distance")]
            
            # Determine and assign Support structure
            support_structure = determine_support_structure(water_depth)
            row[field_names.index('SuppStruct')] = support_structure.capitalize()

            for capacity in capacities:
                for sub_type in ['AC', 'DC']:
                    # Round function
                    def rnd(r):
                        return round(r / int(1e6), 6)
                    
                    # Material Costs
                    supp_costs, conv_costs, equip_costs = calc_equip_costs(water_depth, support_structure, capacity, HVC_type=sub_type)
                    row[field_names.index(f'Sup{capacity}_{sub_type}')] = rnd(supp_costs)
                    row[field_names.index(f'Cnv{capacity}_{sub_type}')] = rnd(conv_costs)
                    row[field_names.index(f'Equ{capacity}_{sub_type}')] = rnd(equip_costs)

                    # Installation and Decommissioning Costs
                    inst_costs = calc_costs(water_depth, support_structure, port_distance, capacity, HVC_type=sub_type, operation="inst")
                    deco_costs = calc_costs(water_depth, support_structure, port_distance, capacity, HVC_type=sub_type, operation="deco")
                    row[field_names.index(f'Ins{capacity}_{sub_type}')] = rnd(inst_costs)
                    row[field_names.index(f'Dec{capacity}_{sub_type}')] = rnd(deco_costs)

                    # Calculate and assign the capital expenses (the sum of the equipment and installation costs)
                    capital_expenses = equip_costs + inst_costs
                    row[field_names.index(f'Cap{capacity}_{sub_type}')] = rnd(capital_expenses)

                    # Calculate and assign operating expenses
                    operating_expenses = 0.03 * conv_costs + 0.015 * supp_costs if support_structure == 'sandisland' else 0.03 * conv_costs
                    row[field_names.index(f'Ope{capacity}_{sub_type}')] = rnd(operating_expenses)

            cursor.updateRow(row)

    arcpy.AddMessage(f"Attribute table of {oss_layer.name} updated successfully.")


if __name__ == "__main__":
    update_fields()
    
    plot_capital_expenses()







