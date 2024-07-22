def check_supp(water_depth):
        """
        Determines the support structure type based on water depth.

        Returns:
        - str: Support structure type ('monopile', 'jacket', 'floating', or 'default').
        """
        # Define depth ranges for different support structures
        if water_depth < 120:
            return "jacket"
        elif 120 <= water_depth:
            return "floating"

def equip_cost_lin(water_depth, support_structure, ice_cover, eh_capacity):
    """
    Calculates the energy hub equipment cost based on water depth, capacity, and export cable type.

    Returns:
    - float: Calculated equipment cost.
    """
    # Coefficients for equipment cost calculation based on the support structure and year
    support_structure_coeff = {
        'jacket': (233, 47, 309, 62),
        'floating': (87, 68, 116, 91)
    }

    equip_coeff = (22.87 * 1e3, 7.06 * 1e6)
        
    # Define parameters
    c1, c2, c3, c4 = support_structure_coeff[support_structure]
    
    c5, c6 = equip_coeff
    
    # Define equivalent electrical power
    equiv_capacity = 0.5 * eh_capacity

    # Calculate foundation cost for jacket/floating
    supp_cost = (c1 * water_depth + c2 * 1e3) * equiv_capacity + (c3 * water_depth + c4 * 1e3)
    
    # Power converter cost
    conv_cost = c5 * eh_capacity + c6
    
    if ice_cover == 1:
        conv_cost *= 1.5714
    
    supp_cost *= 1e-6
    conv_cost *= 1e-6
    
    return supp_cost, conv_cost

def inst_deco_cost_lin(supp_structure, port_distance, operation):
    """
    Calculate installation or decommissioning cost of offshore substations based on the water depth, and port distance.

    Returns:
    - float: Calculated installation or decommissioning cost.
    """
    port_distance *= 1e-3 # Port distance in km
    
    # Installation coefficients for different vehicles
    inst_coeff = {
        ('jacket' 'PSIV'): (1, 18.5, 24, 96, 200),
        ('floating','HLCV'): (1, 22.5, 10, 0, 40),
        ('floating','AHV'): (3, 18.5, 30, 90, 40)
    }

    # Decommissioning coefficients for different vehicles
    deco_coeff = {
        ('jacket' 'PSIV'): (1, 18.5, 24, 96, 200),
        ('floating','HLCV'): (1, 22.5, 10, 0, 40),
        ('floating','AHV'): (3, 18.5, 30, 30, 40)
    }

    # Choose the appropriate coefficients based on the operation type
    coeff = inst_coeff if operation == 'inst' else deco_coeff
        
    if supp_structure == 'jacket':
        c1, c2, c3, c4, c5 = coeff[('jacket' 'PSIV')]
        # Calculate installation cost for jacket
        total_cost = ((1 / c1) * ((2 * port_distance) / c2 + c3) + c4) * (c5 * 1e3) / 24
    elif supp_structure == 'floating':
        total_cost = 0
        
        # Iterate over the coefficients for floating (HLCV and AHV)
        for vessel_type in [('floating', 'HLCV'), ('floating', 'AHV')]:
            c1, c2, c3, c4, c5 = coeff[vessel_type]
            # Calculate installation cost for the current vessel type
            vessel_cost = ((1 / c1) * ((2 * port_distance) / c2 + c3) + c4) * (c5 * 1e3) / 24
            # Add the cost for the current vessel type to the total cost
            total_cost += vessel_cost
    
    total_cost *= 1e-6
    
    return total_cost