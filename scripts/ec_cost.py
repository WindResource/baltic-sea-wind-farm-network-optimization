import numpy as np
from scripts.present_value import PV
class EC_cost:
    
    def __init__(self):
        # Initialize instance of PV within the class constructor
        self.pv = PV()
    
    def ec1_cost_lin(self, distance, capacity):
        """
        Calculate the cost associated with selecting export cables for a given length, desired capacity,
        and desired voltage.

        Parameters:
            length (float): The length of the cable (in meters).
            desired_capacity (float): The desired capacity of the cable (in watts).
            desired_voltage (int): The desired voltage of the cable (in kilovolts).

        Returns:
            tuple: A tuple containing the equipment cost, installation cost, and total cost
                    associated with the selected HVAC cables.
        """

        cable_length = 1.1 * distance
        cable_capacity = 348 # MW
        cable_equip_cost = 0.860 #Meu/km
        cable_inst_cost = 0.540 #Meu/km
        capacity_factor = 0.95
        
        parallel_cables = capacity / (cable_capacity * capacity_factor) + 0.5
        
        equip_cost = parallel_cables * cable_length * cable_equip_cost
        inst_cost = parallel_cables * cable_length * cable_inst_cost
        
        ope_cost_yearly = 0.2 * 1e-2 * equip_cost
        
        deco_cost = 0.5 * inst_cost

        # Calculate present value
        total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost = self.pv.present_value(equip_cost, inst_cost, ope_cost_yearly, deco_cost)
        
        return total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost

    def ec1_cost_ceil(self, distance, capacity):
        """
        Calculate the cost associated with selecting export cables for a given length, desired capacity,
        and desired voltage.

        Parameters:
            length (float): The length of the cable (in meters).
            desired_capacity (float): The desired capacity of the cable (in watts).
            desired_voltage (int): The desired voltage of the cable (in kilovolts).

        Returns:
            tuple: A tuple containing the equipment cost, installation cost, and total cost
                    associated with the selected HVAC cables.
        """

        cable_length = 1.1 * distance
        cable_capacity = 348 # MW
        cable_equip_cost = 0.860 #Meu/km
        cable_inst_cost = 0.540 #Meu/km
        capacity_factor = 0.95
        
        parallel_cables = np.ceil(capacity / (cable_capacity * capacity_factor))
        
        equip_cost = parallel_cables * cable_length * cable_equip_cost
        inst_cost = parallel_cables * cable_length * cable_inst_cost
        
        ope_cost_yearly = 0.002 * equip_cost
        
        deco_cost = 0.5 * inst_cost

        # Calculate present value
        total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost = self.pv.present_value(equip_cost, inst_cost, ope_cost_yearly, deco_cost)
        
        return total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost

    def ec2_cost_lin(self, distance, capacity):
        """
        Calculate the cost associated with selecting export cables for a given length, desired capacity,
        and desired voltage.
        """

        cable_length = 1.2 * distance
        cable_capacity = 348 # MW
        cable_equip_cost = 0.860 # Million EU/km
        cable_inst_cost = 0.540 # Million EU/km
        capacity_factor = 0.90
        
        parallel_cables = capacity / (cable_capacity * capacity_factor) + 0.5
        
        equip_cost = parallel_cables * cable_length * cable_equip_cost
        inst_cost = parallel_cables * cable_length * cable_inst_cost

        ope_cost_yearly = 0.2 * 1e-2 * equip_cost
        
        deco_cost = 0.5 * inst_cost

        # Calculate present value
        total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost = self.pv.present_value(equip_cost, inst_cost, ope_cost_yearly, deco_cost)
        
        return total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost

    def ec2_cost_ceil(self, distance, capacity):
        """
        Calculate the cost associated with selecting export cables for a given length, desired capacity,
        and desired voltage.
        """

        cable_length = 1.2 * distance
        cable_capacity = 348 # MW
        cable_equip_cost = 0.860 # Million EU/km
        cable_inst_cost = 0.540 # Million EU/km
        capacity_factor = 0.90
        
        parallel_cables = np.ceil(capacity / (cable_capacity * capacity_factor))
        
        equip_cost = parallel_cables * cable_length * cable_equip_cost
        inst_cost = parallel_cables * cable_length * cable_inst_cost

        ope_cost_yearly = 0.2 * 1e-2 * equip_cost
        
        deco_cost = 0.5 * inst_cost

        # Calculate present value
        total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost = self.pv.present_value(equip_cost, inst_cost, ope_cost_yearly, deco_cost)
        
        return total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost