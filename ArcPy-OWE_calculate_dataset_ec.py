import numpy as np
import os

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

    return total_costs

def export_cable_costs(distance, desired_capacity, desired_voltage, polarity):
    """
    Calculate the costs associated with selecting export cables for a given length, desired capacity,
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
    
    desired_capacity *= 1e6 # (MW > W)
    
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
    Section (mm^2) > (m^2)
    Resistance (mΩ/km) > (Ω/m)
    Capacitance (nF/km) > (F/m)
    Ampacity (A)
    Equipment cost (eu/m)
    Installation cost (eu/m)
    """
    scaling_factors = np.array([1e3, 1e-6, 1e-6, 1e-12, 1, 1, 1])

    # Apply scaling to each column in data_array
    data_array *= scaling_factors

    # List to store cable rows and counts
    cable_count = []

    # Iterate over each row (cable)
    for cable in data_array:
        n_cables = 1  # Initialize number of cables for this row
        # Calculate total capacity for this row with increasing number of cables until desired capacity is reached
        voltage, resistance, capacitance, ampacity = cable[0], cable[2], cable[3], cable[4]
        while True:
            if polarity == "AC":
                # Ensure AC voltage is represented in RMS for comparability
                v_rms_ac = voltage / np.sqrt(3)  # Correct for line-to-line voltage to RMS.
                resistive_losses = ampacity ** 2 * resistance * length / n_cables
                apparent_power = voltage * ampacity * n_cables - resistive_losses
                reactive_power = v_rms_ac**2 * 2 * np.pi * frequency * capacitance * length
                
                active_power = max(0, np.sqrt(max(0, (apparent_power ** 2 - reactive_power ** 2))))
                
                power_losses = (resistive_losses + reactive_power) / apparent_power
            else:  # polarity == "DC"
                # DC voltage is already in the same measure, no adjustment needed
                resistive_losses = ampacity ** 2 * resistance * length / n_cables
                active_power = n_cables * voltage * ampacity  - resistive_losses
                
                power_losses = resistive_losses / active_power
            if active_power >= desired_capacity:
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
    total_costs = present_value(equip_costs, inst_costs, ope_costs_yearly, deco_costs)

    return total_costs, power_losses

def haversine_distance_np(lon1, lat1, lon2, lat2):
    """
    Calculate the Haversine distance between two sets of coordinates.

    Parameters:
        lon1 (numpy.ndarray): Longitudes of the first set of coordinates.
        lat1 (numpy.ndarray): Latitudes of the first set of coordinates.
        lon2 (numpy.ndarray): Longitudes of the second set of coordinates.
        lat2 (numpy.ndarray): Latitudes of the second set of coordinates.

    Returns:
        numpy.ndarray: Array of Haversine distances in meters.
    """
    # Radius of the Earth in meters
    r = 6371 * 1e3
    
    # Convert latitude and longitude from degrees to radians
    lon1, lat1, lon2, lat2 = np.radians(lon1), np.radians(lat1), np.radians(lon2), np.radians(lat2)

    # Calculate differences in coordinates
    dlon = lon2 - lon1
    dlat = lat2 - lat1

    # Apply Haversine formula
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))

    # Calculate the distance
    distances = c * r 

    return distances

def save_structured_array_to_txt(filename, structured_array):
    """
    Saves a structured numpy array to a text file.

    Parameters:
    - filename (str): The path to the file where the array should be saved.
    - structured_array (numpy structured array): The array to save.
    """
    # Open the file in write mode
    with open(filename, 'w') as file:
        # Write header
        header = ', '.join(structured_array.dtype.names)
        file.write(header + '\n')

        # Write data rows
        for row in structured_array:
            row_str = ', '.join(str(value) for value in row)
            file.write(row_str + '\n')

def calculate_distances(output_folder: str):
    """
    Calculate the Haversine distances between OSS and OnSS datasets within 300 km.

    Parameters:
        output_folder (str): The folder path where the OSS and OnSS datasets and the results will be saved.
    """
    capacity = 500 # MW
    voltage = 400 # kV

    # OSS and OnSS file names
    oss_filename = "oss_data.npy"
    onss_filename = "onss_data.npy"

    # Construct full file paths
    oss_file = os.path.join(output_folder, oss_filename)
    onss_file = os.path.join(output_folder, onss_filename)

    # Load OSS and OnSS data
    oss_data = np.load(oss_file, allow_pickle=True)
    onss_data = np.load(onss_file, allow_pickle=True)

    # Extract coordinates and convert to floats
    oss_coords = oss_data[['Latitude', 'Longitude']]
    onss_coords = onss_data[['Latitude', 'Longitude']]

    # Initialize dictionaries to store distances, corresponding indices, and export cable indices
    distances_dict = {}
    oss_indices_dict = {}
    onss_indices_dict = {}
    export_cable_indices_dict = {}

    # Initialize counter for export cable indices
    export_cable_index = 0

    # Initialize lists to store indices and distances
    export_cable_l= []
    oss_l = []
    onss_l = []
    dist_l = []
    total_cost_HVAC_l = []
    total_cost_HVDC_l = []
    power_losses_HVAC_l = []
    power_losses_HVDC_l = []

    # Iterate over each combination of OSS and OnSS coordinates
    for i in range(len(oss_coords)):
        for j in range(len(onss_coords)):
            # Calculate Haversine distance for current combination
            haversine_distance = haversine_distance_np(
                oss_coords[i][1],  # oss_lon
                oss_coords[i][0],  # oss_lat
                onss_coords[j][1],  # onss_lon
                onss_coords[j][0]   # onss_lat
            )
            # If distance is within 300 km, add it to the lists and dictionaries
            if haversine_distance <= 300 * 1e3:
                key = (int(i), int(j))  # Convert indices to integers
                if key not in distances_dict:
                    rounded_distance = np.round(haversine_distance)
                    distances_dict[key] = int(rounded_distance)
                    oss_indices_dict[key] = int(i)  # Convert index to integer
                    onss_indices_dict[key] = int(j)  # Convert index to integer

                    # Store export cable index and increment the counter
                    export_cable_indices_dict[key] = export_cable_index
                    export_cable_index += 1
                    
                    # Calculate HVAC and HVDC costs
                    total_costs_HVAC, power_losses_HVAC = export_cable_costs(rounded_distance, capacity, voltage, "AC")
                    total_costs_HVDC, power_losses_HVDC = export_cable_costs(rounded_distance, capacity, voltage, "DC")

                    # Append indices and distances to lists
                    export_cable_l.append(export_cable_index)
                    oss_l.append(int(i))
                    onss_l.append(int(j))
                    dist_l.append(int(rounded_distance))
                    total_cost_HVAC_l.append(int(np.round(total_costs_HVAC / 1e3)))
                    total_cost_HVDC_l.append(int(np.round(total_costs_HVDC / 1e3)))
                    power_losses_HVAC_l.append(np.round(power_losses_HVAC, 4))
                    power_losses_HVDC_l.append(np.round(power_losses_HVDC, 4))
                    

    # Create structured array with OSS and OnSS IDs, distances, and export cable indices
    dtype = [('EC_ID', int), ('OSS_ID', int), ('OnSS_ID', int), ('Distance', int), ('Total_costs_HVAC', int), ('PowerLosses_HVAC', float), ('Total_costs_HVDC', int), ('Powerlosses_HVDC', float)]
    data_list = [(export_cable_l[i], oss_data['OSS_ID'][oss_l[i]], onss_data['OnSS_ID'][onss_l[i]], dist_l[i], total_cost_HVAC_l[i], power_losses_HVAC_l[i],  total_cost_HVDC_l[i], power_losses_HVDC_l[i]) for i in range(len(dist_l))]
    data_array = np.array(data_list, dtype=dtype)

    # Save structured array to .npy file
    np.save(os.path.join(output_folder, 'ec_data.npy'), data_array)
    #arcpy.AddMessage("Data saved successfully.")

    # Save structured array to .txt file
    save_structured_array_to_txt(os.path.join(output_folder, 'ec_data.txt'), data_array)
    #arcpy.AddMessage("Data saved successfully.")

# Example usage:
output_folder = r"C:\Users\cflde\Documents\Graduation Project\ArcGIS Pro\BalticSea\Results\datasets"
calculate_distances(output_folder)

