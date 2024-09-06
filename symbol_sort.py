import re

def sorting_key(symbol):
    """
    Define the sorting order based on the letter and LaTeX style, ensuring that
    uppercase symbols are followed by their corresponding lowercase variants for each letter.
    """
    # Unpack the symbol tuple
    symbol_name, description = symbol

    # Remove LaTeX commands and extract the base letter for sorting
    clean_symbol = re.sub(r"(\\mathcal|\\mathbb|\{|\}|_|\^|\(|\))", "", symbol_name)

    # Define sorting priority for uppercase followed by lowercase:
    # 1. Uppercase Latin: A-Z
    # 2. Calligraphic Uppercase: \mathcal{A} - \mathcal{Z}
    # 3. Blackboard Uppercase: \mathbb{A} - \mathbb{Z}
    # 4. Lowercase Latin: a-z
    # 5. Greek letters

    if clean_symbol[0].isalpha():
        base_char = clean_symbol[0].upper()  # Uppercase version of the base letter for sorting

        # Sort Uppercase first
        if clean_symbol[0].isupper():
            if not ("mathcal" in symbol_name or "mathbb" in symbol_name):
                return (base_char, 0, 0)  # Plain uppercase
            elif "mathcal" in symbol_name:
                return (base_char, 0, 1)  # Calligraphic uppercase
            elif "mathbb" in symbol_name:
                return (base_char, 0, 2)  # Blackboard uppercase

        # Sort Lowercase second
        elif clean_symbol[0].islower():
            return (base_char, 1, 0)  # Plain lowercase

    # Greek letters at the end
    greek_letter_order = {
        'alpha': 0, 'beta': 1, 'gamma': 2, 'delta': 3, 'epsilon': 4, 'zeta': 5, 'eta': 6, 'theta': 7,
        'iota': 8, 'kappa': 9, 'lambda': 10, 'mu': 11, 'nu': 12, 'xi': 13, 'omicron': 14, 'pi': 15,
        'rho': 16, 'sigma': 17, 'tau': 18, 'upsilon': 19, 'phi': 20, 'chi': 21, 'psi': 22, 'omega': 23
    }
    if re.match(r'\\[a-zA-Z]+', symbol_name):
        greek_symbol = re.sub(r'\\', '', symbol_name)
        if greek_symbol in greek_letter_order:
            return ("Z", 2, greek_letter_order[greek_symbol])  # Greek letters after Latin letters

    return (symbol_name, 2, 0)  # Default catch-all


def sort_symbols(symbols_definitions):
    """
    Sort the symbols based on the custom LaTeX-style grouping and ordering.
    """
    return sorted(symbols_definitions, key=sorting_key)


# List of symbols and definitions (for reference)
symbols_definitions = [
    ("A_{wb}", "Weibull scale parameter, in meters per second"),
    ("D", "Distance between points, in kilometers"),
    ("Delta v", "Step size between wind speeds, in meters per second"),
    ("D_p", "Distance to the closest port, in kilometers"),
    ("D_{wt}", "Wind turbine rotor diameter, in meters"),
    ("E", "Electrical energy, in megawatt-hours"),
    ("F_i", "Contribution to energy production at wind speed v_i, in megawatts"),
    ("H", "Height parameter, in meters"),
    ("I_c", "Binary indicator variable for ice cover presence"),
    ("K_{max}", "Capacity limit factor"),
    ("K_{vs}", "Vessel's loading capacity, in units per lift"),
    ("L_c", "Length of a cable, in kilometers"),
    ("N_c", "Number of parallel cables"),
    ("P", "Power capacity parameter, in megawatts"),
    ("P_F", "Power factor"),
    ("Phi^{(s)}", "Progression level for stage s"),
    ("P_i", "Geographic coordinates of point P_i, in radians"),
    ("P_{th}", "Capacity threshold, in megawatts"),
    ("R", "Power capacity ratio"),
    ("R_{d,vs}", "Vessel's day rate, in thousands of euros per day"),
    ("R_E", "Radius of the Earth, in kilometers"),
    ("S", "Spacing, in meters or kilometers"),
    ("T_y", "Hours in a year"),
    ("Y", "Year"),
    ("Z", "Buffer zone, in kilometers"),
    ("C", "Cost parameter, in millions of euros"),
    ("\\mathcal{C}", "Set of all countries within the scope of the study"),
    ("\\mathcal{G}", "Set of all feasible energy system components within the system"),
    ("\\mathcal{N}", "Set of feasible wind farms, energy hubs or onshore substations within the system"),
    ("\\mathcal{V}", "Set of feasible export, or onshore cables within the system"),
    ("\\mathbb{R}_{geq 0}", "Set of non-negative real numbers"),
    ("c", "Cost variable, in millions of euros"),
    ("f_{pdf}", "Probability Density Function"),
    ("k", "Coefficient or factor"),
    ("k_{ice}", "Ice cover cost factor"),
    ("k_{wb}", "Weibull shape parameter"),
    ("n", "Natural number"),
    ("r", "Discount rate"),
    ("s", "Stage in the multi-stage optimization model"),
    ("v", "Speed parameter, in meters per second"),
    ("v_{cut-in}", "Cut-in wind speed for wind turbine, in meters per second"),
    ("v_{cut-out}", "Cut-out wind speed for wind turbine, in meters per second"),
    ("y", "Year"),
    ("\\alpha", "Power law exponent"),
    ("\\alpha_{wf}", "Wind farm power capacity allocation variable, in megawatts"),
    ("\\beta_{eh}", "Energy hub activation variable"),
    ("\\epsilon_0", "Zero threshold parameter"),
    ("\\lambda_i", "Longitude of point P_i, in radians"),
    ("\\phi_i", "Latitude of point P_i, in radians")
]

# Sort the symbols
sorted_symbols = sort_symbols(symbols_definitions)

# Display the sorted list
for symbol, description in sorted_symbols:
    print(f"{symbol}: {description}")