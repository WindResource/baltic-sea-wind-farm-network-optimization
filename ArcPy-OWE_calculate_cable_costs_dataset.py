import numpy as np

def HVAC_cost(length, desired_capacity, desired_voltage):
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

    # Define the scaling factors for each column: (Tension (kV), Section (mm^2), Resistance (mΩ/km), Capacitance (nF/km), Ampacity (A), Equipment cost (eu/m), Installation cost (eu/m))
    scaling_factors = np.array([1e3, 1, 1e-3, 1e-9, 1, 1e3, 1e3])

    # Apply scaling to each column in data_array
    data_array *= scaling_factors

    # Filter data based on desired voltage
    data_array = data_array[data_array[:, 0] >= desired_voltage]

    # List to store valid combinations
    valid_combinations = []

    # Iterate over each row (cable)
    for cable_index, cable in enumerate(data_array):
        total_capacity = 0
        n_cables = 1  # Initialize number of cables for this row
        # Calculate total capacity for this row with increasing number of cables until desired capacity is reached
        while total_capacity < desired_capacity:
            voltage, capacitance, ampacity = cable[0], cable[3], cable[4]
            calculated_capacity = np.sqrt(max(0, ((np.sqrt(3) * voltage * n_cables * ampacity) ** 2 - (0.5 * voltage**2 * 2*np.pi * frequency * capacitance * length) ** 2))))
            total_capacity += calculated_capacity
            if total_capacity >= desired_capacity:
                # Add the current row index and number of cables to valid_combinations
                valid_combinations.append((cable_index, n_cables))
                break  # Exit the loop since desired capacity is reached
            n_cables += 1

    return valid_combinations

# Example usage
desired_capacity = 5000  # Specify your desired capacity here
desired_voltage = 220  # Specify your desired voltage here
valid_cable_combinations = HVAC_cost(length=300, desired_capacity=desired_capacity, desired_voltage=desired_voltage)
print("Valid cable combinations for desired capacity of", desired_capacity, "and voltage of", desired_voltage, "are:")
for row_index, n_cables in valid_cable_combinations:
    print("Row:", row_index, "- Number of cables:", n_cables)
