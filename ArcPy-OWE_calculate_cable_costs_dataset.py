import numpy as np

def HVAC_costs(length, desired_capacity, desired_voltage):
    frequency = 50  # Assuming constant frequency
    
    # Define data_tuples where each tuple represents (tension, section, resistance, capacitance, ampacity, cost, inst_cost)
    data_tuples = [
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
    data_array = np.array(data_tuples)
    
    # Filter data based on desired voltage
    data_array = data_array[data_array[:, 0] == desired_voltage]

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
    equip_costs = equip_costs_array[min_cost_index]
    inst_costs = inst_costs_array[min_cost_index]
    total_costs = total_costs_array[min_cost_index]

    return equip_costs, inst_costs, total_costs

# Example usage
desired_capacity_MW = 800  # Specify your desired capacity here
desired_capacity = desired_capacity_MW * int(1e6)
desired_voltage = 220  # Specify your desired voltage here
length = 5000 # Required length
equip_costs, inst_costs, total_costs = HVAC_costs(length, desired_capacity, desired_voltage)

print(equip_costs)
print(inst_costs)
print(total_costs)
