"""
This script is designed to automate the calculation and updating of cost and logistical parameters for wind turbine installations within GIS shapefiles, utilizing the ArcPy site package. It facilitates the assessment of various costs associated with wind turbine projects, including equipment, installation, decommissioning, and logistics, based on spatial and non-spatial attributes found in shapefiles for turbines and wind farms.

Functions:

    calculate_total_costs(turbine_layer, windfarm_file):
        Calculate the total costs for each category by summing the corresponding values in each row of the turbine attribute table.

        Parameters:
        - turbine_layer (str): Path to the turbine shapefile.
        - windfarm_file (str): Path to the wind farm shapefile.

        Returns:
        - dict: A dictionary containing total costs for each category.

    determine_support_structure(water_depth):
        Determines the support structure type based on water depth.

        Parameters:
        - water_depth (float): Water depth in meters.

        Returns:
        - str: Support structure type ('monopile', 'jacket', 'floating', or 'default').

    calc_equip_costs(water_depth, year, turbine_capacity):
        Calculates the equipment costs based on water depth values, year, and turbine capacity.

        Parameters:
        - water_depth (float): Water depth in meters.
        - year (str): Year for which equipment costs are calculated ('2020', '2030', or '2050').
        - turbine_capacity (float): Rated power capacity of the wind turbine.

        Returns:
        - float: Calculated equipment costs.

    calc_costs(water_depth, port_distance, turbine_capacity, operation):
        Calculate installation or decommissioning costs based on the water depth, port distance,
        and rated power of the wind turbines.

        Parameters:
        - water_depth (float): Water depth in meters.
        - port_distance (float): Distance to the port in meters.
        - turbine_capacity (float): Rated power capacity of the wind turbines in megawatts (MW).
        - operation (str): Operation type ('installation' or 'decommissioning').

        Coefficients:
        - Capacity (u/lift): Capacity of the vessel in units per lift.
        - Speed (km/h): Speed of the vessel in kilometers per hour.
        - Load time (h/lift): Load time per lift in hours per lift.
        - Inst. time (h/u): Installation time per unit in hours per unit.
        - Dayrate (keu/d): Dayrate of the vessel in thousands of euros per day.

        Vessels:
        - SPIV (Self-Propelled Installation Vessel)
        - AHV (Anchor Handling Vessel)
        - Tug (Tug Boat)

        Equation:
        Hours = (1 / c[0]) * ((2 * port_distance / 1000) / c[1] + c[2]) + c[3]
        Cost = Hours * c[4] * 1000 / 24

        Returns:
        - tuple: Calculated hours and costs in Euros.

    logi_costs(water_depth, port_distance, failure_rate=0.08):
        Calculate logistics time and costs based on water depth, port distance, and failure rate for major wind turbine repairs.

        Parameters:
        - water_depth (float): Water depth in meters.
        - port_distance (float): Distance to the port in meters.
        - failure_rate (float, optional): Failure rate for the wind turbines (/yr). Default is 0.08.

        Coefficients:
        - Speed (km/h): Speed of the vessel in kilometers per hour.
        - Repair time (h): Repair time in hours.
        - Dayrate (keu/d): Dayrate of the vessel in thousands of euros per day.
        - Roundtrips: Number of roundtrips for the logistics operation.

        Equations:
        - Logistics Time: labda * ((2 * c4 * port_distance) / c1 + c2)
        - Logistics Costs: Logistics Time * c4 / 24

        Returns:
        - tuple: Logistics time in hours per year and logistics costs in Euros.

    update_fields():
        Update the attribute table of the wind turbine coordinates shapefile (WTC) with calculated equipment, installation,
        decommissioning, logistics costs, logistics time, and Opex.

        Returns:
        - None

"""
import arcpy
import numpy as np

def determine_support_structure(water_depth):
    """
    Determines the support structure type based on water depth.

    Returns:
    - np.ndarray: Support structure type ('monopile', 'jacket', 'floating', or 'default').
    """
    # Define depth ranges for different support structures
    support_structure = np.empty_like(water_depth, dtype='<U8')
    support_structure[(0 <= water_depth) & (water_depth < 25)] = "monopile"
    support_structure[(25 <= water_depth) & (water_depth < 55)] = "jacket"
    support_structure[(55 <= water_depth) & (water_depth <= 200)] = "floating"
    support_structure[~((0 <= water_depth) & (water_depth <= 200))] = "default"

    return support_structure

def calc_equip_costs(water_depth, support_structure, year, turbine_capacity):
    """
    Calculates the equipment costs based on water depth values, year, and turbine capacity.

    Returns:
    - np.ndarray: Calculated equipment costs.
    """
    # Coefficients for equipment cost calculation based on the support structure and year
    support_structure_coeff = {
        ('monopile', '2020'): (201, 613, 812),
        ('monopile', '2030'): (181, 552, 370),
        ('monopile', '2050'): (171, 521, 170),
        ('jacket', '2020'): (114, -2270, 932),
        ('jacket', '2030'): (103, -2043, 478),
        ('jacket', '2050'): (97, -1930, 272),
        ('floating', '2020'): (0, 774, 1481),
        ('floating', '2030'): (0, 697, 1223),
        ('floating', '2050'): (0, 658, 844)
    }

    # Coefficients for wind turbine rated cost
    turbine_coeff = {
        '2020': 1500,
        '2030': 1200,
        '2050': 1000
    }

    # Look up coefficients for each element in the arrays
    c1, c2, c3 = np.vectorize(lambda ss, yr: support_structure_coeff[(ss, yr)][0])(support_structure, year)
    c2_vals = np.vectorize(lambda ss, yr: support_structure_coeff[(ss, yr)][1])(support_structure, year)
    c3_vals = np.vectorize(lambda ss, yr: support_structure_coeff[(ss, yr)][2])(support_structure, year)
    support_structure_costs = turbine_capacity * (c1 * (water_depth ** 2)) + (c2_vals * water_depth) + (c3_vals * 1000)
    turbine_costs = turbine_capacity * turbine_coeff[year]

    equip_costs = support_structure_costs + turbine_costs

    return equip_costs

def calc_costs(water_depth, support_structure, port_distance, turbine_capacity, operation):
    """
    Calculate installation or decommissioning costs based on the water depth, port distance,
    and rated power of the wind turbines.

    Returns:
    - np.ndarray: Calculated hours and costs in Euros.
    """
    # Installation coefficients for different vehicles
    inst_coeff = {
        'PSIV': (40 / turbine_capacity, 18.5, 24, 144, 200),
        'Tug': (0.3, 7.5, 5, 0, 2.5),
        'AHV': (7, 18.5, 30, 90, 40)
    }

    # Decommissioning coefficients for different vehicles
    deco_coeff = {
        'PSIV': (40 / turbine_capacity, 18.5, 24, 144, 200),
        'Tug': (0.3, 7.5, 5, 0, 2.5),
        'AHV': (7, 18.5, 30, 30, 40)
    }

    # Choose the appropriate coefficients based on the operation type
    coeff = inst_coeff if operation == 'installation' else deco_coeff

    # Vectorized support_structure calculation
    support_structure = determine_support_structure(water_depth).lower()

    if np.any((support_structure == 'monopile') | (support_structure == 'jacket')):
        c1, c2, c3, c4, c5 = np.vectorize(lambda vt: coeff['PSIV'] if vt in ['monopile', 'jacket'] else None)(support_structure)
        total_costs = ((1 / c1) * ((2 * port_distance) / c2 + c3) + c4) * (c5 * 1000) / 24
    elif np.any(support_structure == 'floating'):
        total_costs = np.zeros_like(support_structure)
        
        for vessel_type in ['Tug', 'AHV']:
            c1, c2, c3, c4, c5 = np.vectorize(lambda vt: coeff[vessel_type] if vt == 'floating' else None)(support_structure)
            vessel_costs = ((1 / c1) * ((2 * port_distance) / c2 + c3) + c4) * (c5 * 1000) / 24
            total_costs += vessel_costs
    else:
        total_costs = None
        
    return total_costs

def calc_logi_costs(water_depth, support_structure, port_distance, failure_rate=0.08):
    """
    Calculate logistics time and costs for major wind turbine repairs (part of OPEX) based on water depth, port distance, and failure rate for major wind turbine repairs.
    
    Returns:
    - np.ndarray: Logistics time in hours per year and logistics costs in Euros.
    """
    # Logistics coefficients for different vessels
    logi_coeff = {
        'JUV': (18.5, 50, 150, 1),
        'Tug': (7.5, 50, 2.5, 2)
    }

    # Determine logistics vessel based on support structure
    vessel = np.where(support_structure == 'monopile' | 'jacket', 'JUV', 'Tug')

    c1, c2, c3, c4 = np.vectorize(lambda vt: logi_coeff[vt])(vessel)

    # Calculate logistics costs
    logi_costs = failure_rate * ((2 * c4 * port_distance / 1000) / c1 + c2) * (c3 * 1000) / 24

    return logi_costs

def update_fields():
    """
    Update the attribute table of the wind turbine coordinates shapefile (WTC) with calculated equipment, installation,
    decommissioning, logistics costs, and operating expenses.

    Returns:
    - None
    """
    # Function to add a field if it does not exist in the layer
    def add_field_if_not_exists(layer, field_name, field_type):
        if field_name not in [field.name for field in arcpy.ListFields(layer)]:
            arcpy.AddField_management(layer, field_name, field_type)
            arcpy.AddMessage(f"Added field '{field_name}' to the attribute table.")

    # Access the current ArcGIS project
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

    # Check if required fields exist in the attribute table
    required_fields = ['WaterDepth', 'Capacity', 'Distance']
    existing_fields = [field.name for field in arcpy.ListFields(turbine_layer)]
    for field in required_fields:
        if field not in existing_fields:
            arcpy.AddError(f"Required field '{field}' is missing in the attribute table.")
            return

    # Get the list of fields in the attribute table
    fields = [field.name for field in arcpy.ListFields(turbine_layer)]

    # Create NumPy arrays for each required field
    water_depth = arcpy.da.FeatureClassToNumPyArray(turbine_layer, "WaterDepth")
    turbine_capacity = arcpy.da.FeatureClassToNumPyArray(turbine_layer, "Capacity")
    distance = arcpy.da.FeatureClassToNumPyArray(turbine_layer, "Distance")

    # Vectorize support structure calculation
    support_structure = determine_support_structure(water_depth)

    # Calculate equipment costs for each year
    years = np.array(['2020', '2030', '2050'])
    equi_costs = calc_equip_costs(water_depth[:, np.newaxis], support_structure[:, np.newaxis], years, turbine_capacity[:, np.newaxis])

    # Calculate installation and decommissioning costs
    inst_costs = calc_costs(water_depth[:, np.newaxis], support_structure[:, np.newaxis], distance[:, np.newaxis], turbine_capacity[:, np.newaxis], 'installation')
    deco_costs = calc_costs(water_depth[:, np.newaxis], support_structure[:, np.newaxis], distance[:, np.newaxis], turbine_capacity[:, np.newaxis], 'decommissioning')

    # Calculate and assign logistics costs
    logi_costs = calc_logi_costs(water_depth[:, np.newaxis], support_structure[:, np.newaxis], distance[:, np.newaxis])

    # Calculate and assign operating expenses
    opex_costs = 0.025 * equi_costs + logi_costs

    # Update each row in the attribute table
    with arcpy.da.UpdateCursor(turbine_layer, fields) as cursor:
        for row, eq_cost, inst_cost, deco_cost, logi_cost, opex_cost in zip(cursor, equi_costs, inst_costs, deco_costs, logi_costs, opex_costs):
            row[fields.index("SuppStruct")] = determine_support_structure(row[fields.index("WaterDepth")]).capitalize()
            row[fields.index("EquiC20")] = eq_cost[0]
            row[fields.index("EquiC30")] = eq_cost[1]
            row[fields.index("EquiC50")] = eq_cost[2]
            row[fields.index("InstC")] = inst_cost
            row[fields.index("Capex20")] = eq_cost[0] + inst_cost
            row[fields.index("Capex30")] = eq_cost[1] + inst_cost
            row[fields.index("Capex50")] = eq_cost[2] + inst_cost
            row[fields.index("Decex")] = deco_cost
            row[fields.index("LogiC")] = logi_cost
            row[fields.index("Opex20")] = opex_cost[0]
            row[fields.index("Opex30")] = opex_cost[1]
            row[fields.index("Opex50")] = opex_cost[2]
            cursor.updateRow(row)

    arcpy.AddMessage(f"Attribute table of {turbine_layer} updated successfully.")

if __name__ == "__main__":
    update_fields()
