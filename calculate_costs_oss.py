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
    inst_year = 0  # First year
    ope_year = inst_year + 5
    dec_year = ope_year + 25  
    end_year = dec_year + 2  # End year

    # Discount rate
    discount_rate = 0.05

    # Define the years as a function of inst_year and end_year
    years = range(inst_year, end_year + 1)

    # Initialize total operational cost
    ope_cost = 0

    # Adjust cost for each year
    for year in years:
        # Adjust installation cost
        if year == inst_year:
            equip_cost *= (1 + discount_rate) ** -year
            inst_cost *= (1 + discount_rate) ** -year
        # Adjust operational cost
        if year >= inst_year and year < ope_year:
            inst_cost *= (1 + discount_rate) ** -year
        elif year >= ope_year and year < dec_year:
            ope_cost_yearly *= (1 + discount_rate) ** -year
            ope_cost += ope_cost_yearly  # Accumulate yearly operational cost
        # Adjust decommissioning cost
        if year >= dec_year and year <= end_year:
            deco_cost *= (1 + discount_rate) ** -year

    # Calculate total present value of cost
    total_cost = equip_cost + inst_cost + ope_cost + deco_cost

    return total_cost

def eh_cost_lin(water_depth, ice_cover, port_distance, eh_capacity, polarity = "AC"):
    """
    Estimate the cost associated with an energy hub based on various parameters.

    Parameters:
    - water_depth (float): Water depth at the location of the energy hub.
    - ice_cover (int): Indicator of ice cover presence (1 for presence, 0 for absence).
    - port_distance (float): Distance from the offshore location to the nearest port.
    - eh_capacity (float): Capacity of the energy hub.
    - polarity (str, optional): Polarity of the substation ('AC' or 'DC'). Defaults to 'AC'.

    Returns:
    - float: Estimated total cost of the energy hub.
    """
    
    def supp_struct_cond(water_depth):
        """
        Determines the support structure type based on water depth.

        Returns:
        - str: Support structure type ('monopile', 'jacket', 'floating', or 'default').
        """
        # Define depth ranges for different support structures
        if water_depth < 150:
            return "jacket"
        elif 150 <= water_depth:
            return "floating"

    def equip_cost_lin(water_depth, support_structure, ice_cover, eh_capacity, polarity = "AC"):
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

        equip_coeff = {
            'AC': (22.87, 7.06),
            'DC': (102.93, 31.75)
        }
        
        # Define parameters
        c1, c2, c3, c4 = support_structure_coeff[support_structure]
        
        c5, c6 = equip_coeff[polarity]
        
        # Define equivalent electrical power
        equiv_capacity = 0.5 * eh_capacity if polarity == "AC" else eh_capacity

        # Calculate foundation cost for jacket/floating
        supp_cost = (c1 * water_depth + c2 * 1000) * equiv_capacity + (c3 * water_depth + c4 * 1000)
        
        # Add support structure cost for ice cover adaptation
        supp_cost = 1.10 * supp_cost if ice_cover == 1 else supp_cost
        
        # Power converter cost
        conv_cost = c5 * eh_capacity * int(1e3) + c6 * int(1e6) #* int(1e3)
        
        # Calculate equipment cost
        equip_cost = supp_cost + conv_cost
        
        return conv_cost, equip_cost

    def inst_deco_cost_lin(support_structure, port_distance, operation):
        """
        Calculate installation or decommissioning cost of offshore substations based on the water depth, and port distance.

        Returns:
        - float: Calculated installation or decommissioning cost.
        """
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
            
        if support_structure == 'jacket':
            c1, c2, c3, c4, c5 = coeff[('jacket' 'PSIV')]
            # Calculate installation cost for jacket
            total_cost = ((1 / c1) * ((2 * port_distance) / c2 + c3) + c4) * (c5 * 1000) / 24
        elif support_structure == 'floating':
            total_cost = 0
            
            # Iterate over the coefficients for floating (HLCV and AHV)
            for vessel_type in [('floating', 'HLCV'), ('floating', 'AHV')]:
                c1, c2, c3, c4, c5 = coeff[vessel_type]
                # Calculate installation cost for the current vessel type
                vessel_cost = ((1 / c1) * ((2 * port_distance) / c2 + c3) + c4) * (c5 * 1000) / 24
                # Add the cost for the current vessel type to the total cost
                total_cost += vessel_cost
        
        return total_cost

    # Determine support structure
    supp_structure = supp_struct_cond(water_depth)
    
    # Calculate equipment cost
    conv_cost, equip_cost = equip_cost_lin(water_depth, supp_structure, ice_cover, eh_capacity, polarity)

    # Calculate installation and decommissioning cost
    inst_cost = inst_deco_cost_lin(supp_structure, port_distance, "inst")
    deco_cost = inst_deco_cost_lin(supp_structure, port_distance, "deco")

    # Calculate yearly operational cost
    ope_cost_yearly = 0.03 * conv_cost
    
    # Calculate present value of cost    
    eh_cost = present_value(equip_cost, inst_cost, ope_cost_yearly, deco_cost)
    
    # Offshore substation cost in million Euros
    eh_cost *= 1e-6
    
    return eh_cost

if __name__ == "__main__":
    update_fields()







