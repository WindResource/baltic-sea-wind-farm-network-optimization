import numpy as np

def present_value(equip_costs, inst_costs, ope_costs_yearly, deco_costs):
    """
    Calculate the total present value of cable costs.

    Parameters:
        equip_costs (float): Equipment costs.
        inst_costs (float): Installation costs.
        ope_costs_yearly (float): Yearly operational costs.
        deco_costs (float): Decommissioning costs.

    Returns:
        tuple: A tuple containing the equipment costs, installation costs, and total present value of costs.
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

    # Initialize total operational costs
    ope_costs = 0
    
    # Adjust costs for each year
    for year in years:
        # Adjust installation costs
        if year == inst_year:
            equip_costs *= (1 + discount_rate) ** -year
            inst_costs *= (1 + discount_rate) ** -year
        # Adjust operational costs
        if year >= inst_year and year < ope_year:
            inst_costs *= (1 + discount_rate) ** -year
        elif year >= ope_year and year < dec_year:
            ope_costs_yearly *= (1 + discount_rate) ** -year
            ope_costs += ope_costs_yearly  # Accumulate yearly operational costs
        # Adjust decommissioning costs
        if year >= dec_year and year <= end_year:
            deco_costs *= (1 + discount_rate) ** -year

    # Calculate total present value of costs
    total_costs = equip_costs + inst_costs + ope_costs + deco_costs

    return total_costs, equip_costs, inst_costs, ope_costs, deco_costs

def haversine_distance(lon1, lat1, lon2, lat2):
    """
    Calculate the great-circle distance between two points on the Earth's surface.

    Parameters:
        lon1 (float): Longitude of the first point (in degrees).
        lat1 (float): Latitude of the first point (in degrees).
        lon2 (float): Longitude of the second point (in degrees).
        lat2 (float): Latitude of the second point (in degrees).

    Returns:
        float: The distance between the two points in kilometers.
    """
    # Convert latitude and longitude from degrees to radians
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    r = 6371  # Radius of the Earth in kilometers
    distance = r * c

    return distance

def HVAC_interarray_cable_costs(distance, desired_capacity, desired_voltage, water_depth):
    """
    Calculate the costs associated with selecting HVAC interarray cables for a given distance, desired capacity, desired voltage, and water depth.

    Parameters:
        distance (float): The distance of the cable route (in meters).
        desired_capacity (float): The desired capacity of the cable (in watts).
        desired_voltage (int): The desired voltage of the cable (in kilovolts).
        water_depth (float): The water depth where the cables will be installed (in meters).

    Returns:
        tuple: A tuple containing the equipment costs, installation costs, yearly operational costs, and decommissioning costs associated with the selected HVAC interarray cables.
    """
    length = 1.1 * distance
    
    cable_data = [
        (66, 95, 0.25, 24, 180, 113, 113),
        (66, 150, 0.16, 30, 215, 134, 121),
        (66, 300, 0.08, 42, 298, 186, 149),
        (66, 400, 0.06, 49, 357, 223, 156),
        (66, 630, 0.04, 59, 456, 285, 171),
        (66, 800, 0.03, 69, 577, 361, 180),
        (132, 120, 0.2, 80, 288, 152, 114),
        (132, 150, 0.16, 87, 358, 188, 122),
        (132, 300, 0.08, 123, 747, 393, 216),
        (132, 400, 0.06, 136, 900, 474, 213),
        (132, 630, 0.04, 162, 1228, 646, 226),
        (132, 800, 0.03, 201, 1779, 936, 281)
    ]
    
    # Convert data_tuples to a NumPy array
    data_array = np.array(cable_data)
    
    # Filter data based on desired voltage
    data_array = data_array[data_array[:, 0] == desired_voltage]

    # Define the scaling factors for each column: 
    """
    Voltage (kV) > (V)
    Section (mm^2)
    Resistance (Ω/km) > (Ω/m)
    Capacity (MW)
    Equipment cost dynamic cables (floating support) (eu/m)
    Equipment cost static cables (static support) (eu/m)
    Installation cost (eu/m)
    """
    scaling_factors = np.array([1e3, 1, 1e-3, 1, 1, 1, 1])

    # Apply scaling to each column in data_array
    data_array *= scaling_factors
    
    # List to store cable rows and counts
    cable_count = []
    
    # Iterate over each row (cable)
    for cable in data_array:
        n_cables = 1  # Initialize number of cables for this row
        # Calculate total capacity for this row with increasing number of cables until desired capacity is reached
        while True:
            capacity = cable[3]
            calculated_capacity = n_cables * capacity
            if calculated_capacity >= desired_capacity:
                # Add the current row index and number of cables to valid_combinations
                cable_count.append((cable, n_cables))
                break  # Exit the loop since desired capacity is reached
            elif n_cables > 200:  # If the number of cables exceeds 200, break the loop
                break
            n_cables += 1

    # Select the equipment cost based on water depth
    equip_costs = cable[4] if water_depth < 150 else cable[5]

    # Calculate the total costs for each cable combination
    equip_costs_array = [(equip_costs * length * n_cables) for n_cables in cable_count]
    inst_costs_array = [(cable[6] * length * n_cables) for cable, n_cables in cable_count]
    
    # Calculate total costs
    total_costs_array = np.add(equip_costs_array, inst_costs_array)
    
    # Find the cable combination with the minimum total cost
    min_cost_index = np.argmin(total_costs_array)

    # Initialize costs
    equip_costs = equip_costs_array[min_cost_index]
    inst_costs = inst_costs_array[min_cost_index]
    ope_costs_yearly = 0.2 * 1e-2 * equip_costs
    deco_costs = 0.5 * inst_costs
    
    # Calculate present value
    total_costs, equip_costs, inst_costs, ope_costs, deco_costs = present_value(equip_costs, inst_costs, ope_costs_yearly, deco_costs)
    
    return total_costs


def HVDC_export_cable_costs(distance, desired_capacity):
    """
    Calculate the costs associated with selecting HVDC (High Voltage Direct Current) export cables for a given distance and capacity.

    Parameters:
        distance (float): The distance of the cable route (in meters).
        capacity (float): The capacity of the cable (in watts).

    Returns:
        tuple: A tuple containing the equipment costs, installation costs, yearly operational costs, and decommissioning costs associated with the selected HVDC cables.
    """
    length = 1.2 * distance
    
    rated_cost = 1.35 * 1e3   # (eu/(W*m))
    
    equip_costs = rated_cost * desired_capacity * length
    inst_costs = 0.5 * equip_costs
    ope_costs_yearly = 0.2 * 1e-2 * equip_costs
    deco_costs = 0.5 * inst_costs
    
    # Calculate present value
    total_costs, equip_costs, inst_costs, ope_costs, deco_costs = present_value(equip_costs, inst_costs, ope_costs_yearly, deco_costs)
    
    return total_costs

def HVAC_export_cable_costs(distance, desired_capacity, desired_voltage):
    """
    Calculate the costs associated with selecting HVAC cables for a given length, desired capacity,
    and desired voltage.

    Parameters:
        length (float): The length of the cable (in meters).
        desired_capacity (float): The desired capacity of the cable (in watts).
        desired_voltage (int): The desired voltage of the cable (in kilovolts).

    Returns:
        tuple: A tuple containing the equipment costs, installation costs, and total costs
                associated with the selected HVAC cables.
    """
    frequency = 50  # Assuming constant frequency
    
    length = 1.2 * distance
    
    desired_capacity *= 1e6 # (MW)
    
    # Define data_tuples where each column represents (tension, section, resistance, capacitance, ampacity, cost, inst_cost)
    cable_data = [
        (132, 630, 39.5, 209, 818, 406, 335),
        (132, 800, 32.4, 217, 888, 560, 340),
        (132, 1000, 27.5, 238, 949, 727, 350),
        (220, 500, 48.9, 136, 732, 362, 350),
        (220, 630, 39.1, 151, 808, 503, 360),
        (220, 800, 31.9, 163, 879, 691, 370),
        (220, 1000, 27.0, 177, 942, 920, 380),
        (400, 800, 31.4, 130, 870, 860, 540),
        (400, 1000, 26.5, 140, 932, 995, 555),
        (400, 1200, 22.1, 170, 986, 1130, 570),
        (400, 1400, 18.9, 180, 1015, 1265, 580),
        (400, 1600, 16.6, 190, 1036, 1400, 600),
        (400, 2000, 13.2, 200, 1078, 1535, 615)
    ]

    # Convert data_tuples to a NumPy array
    data_array = np.array(cable_data)
    
    # Filter data based on desired voltage
    data_array = data_array[data_array[:, 0] >= desired_voltage]

    # Define the scaling factors for each column: 
    """
    Voltage (kV) > (V)
    Section (mm^2)
    Resistance (mΩ/km) > (Ω/m)
    Capacitance (nF/km) > (F/m)
    Ampacity (A)
    Equipment cost (eu/m)
    Installation cost (eu/m)
    """
    scaling_factors = np.array([1e3, 1, 1e-6, 1e-12, 1, 1, 1])

    # Apply scaling to each column in data_array
    data_array *= scaling_factors

    # List to store cable rows and counts
    cable_count = []

    # Iterate over each row (cable)
    for cable in data_array:
        n_cables = 1  # Initialize number of cables for this row
        # Calculate total capacity for this row with increasing number of cables until desired capacity is reached
        while True:
            voltage, capacitance, ampacity = cable[0], cable[3], cable[4]
            calculated_capacity = np.sqrt(max(0, ((np.sqrt(3) * voltage * n_cables * ampacity) ** 2 - (.5 * voltage**2 * 2*np.pi * frequency * capacitance * length) ** 2)))
            if calculated_capacity >= desired_capacity:
                # Add the current row index and number of cables to valid_combinations
                cable_count.append((cable, n_cables))
                break  # Exit the loop since desired capacity is reached
            elif n_cables > 200:  # If the number of cables exceeds 200, break the loop
                break
            n_cables += 1

    # Calculate the total costs for each cable combination
    equip_costs_array = [(cable[5] * length * n_cables) for cable, n_cables in cable_count]
    inst_costs_array = [(cable[6] * length * n_cables) for cable, n_cables in cable_count]
    
    # Calculate total costs
    total_costs_array = np.add(equip_costs_array, inst_costs_array)
    
    # Find the cable combination with the minimum total cost
    min_cost_index = np.argmin(total_costs_array)

    # Initialize costs
    equip_costs = equip_costs_array[min_cost_index]
    inst_costs = inst_costs_array[min_cost_index]
    ope_costs_yearly = 0.2 * 1e-2 * equip_costs
    deco_costs = 0.5 * inst_costs
    
    # Calculate present value
    total_costs, equip_costs, inst_costs, ope_costs, deco_costs = present_value(equip_costs, inst_costs, ope_costs_yearly, deco_costs)

    return total_costs




distance = haversine_distance(lon1, lat1, lon2, lat2)

desired_capacity = 800
desired_voltage = 220
water_depth = 100

total_costs_HVAC_export = HVAC_export_cable_costs(distance, desired_capacity, desired_voltage)
total_costs_HVDC_export = HVDC_export_cable_costs(distance, desired_capacity)
total_costs_HVAC_ia = HVAC_interarray_cable_costs(distance, desired_capacity, desired_voltage, water_depth)



print(round(total_costs_HVAC_export, 3))
print(round(total_costs_HVDC_export, 3))
print(round(total_costs_HVAC_ia, 3))

