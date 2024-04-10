import numpy as np
from itertools import product

def HVAC_cost(length, desired_capacity):
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

    # Define the number of cables
    n_cables = 1  # You need to define this based on your system configuration

    # Set to store unique combinations of cable types
    valid_combinations = set()

    # Filter data tuples based on desired capacity using permutations with replacement
    for r in range(1, len(data_array) + 1):  # Iterate over possible number of cables to select
        for combo in product(range(len(data_array)), repeat=r):  # Allow multiple instances of the same cable type
            total_capacity = 0
            for cable_index in combo:
                cable = data_array[cable_index]
                voltage, capacitance, ampacity = cable[0], cable[3], cable[4]
                calculated_capacity = np.sqrt(max( 0, ( (np.sqrt(3) * voltage * n_cables * ampacity) ** 2 - (0.5 * voltage**2 * 2*np.pi * frequency * capacitance * length) ** 2) ) )
                total_capacity += calculated_capacity
            if total_capacity >= desired_capacity:
                # Add a tuple of cable types to the set
                valid_combinations.add(tuple(combo))

    return valid_combinations

# Example usage
desired_capacity = 5000  # Specify your desired capacity here
valid_cable_combinations = HVAC_cost(length=300, desired_capacity=desired_capacity)
print("Valid cable combinations for desired capacity of", desired_capacity, "are:")
for combination in valid_cable_combinations:
    print(combination)
