import numpy as np
class IAC_cost:
    def iac_cost_ceil(self, distance, capacity):
        """
        Calculate the total cost of an inter array cable section for a given distance and desired capacity.

        Parameters:
            distance (float): The distance of the cable (in meters).
            capacity (float): Cable capacity (in MW).

        Returns:
            float: Total cost associated with the selected HVAC cables in millions of euros.
        """
        cable_length = 1.05 * distance
        cable_capacity = 80 # MW
        cable_equip_cost = 0.152 # MEU/km
        cable_inst_cost = 0.114 # MEU/km
        capacity_factor = 0.98
        
        parallel_cables = np.ceil(capacity / (cable_capacity * capacity_factor))
        
        equip_cost = parallel_cables * cable_length * cable_equip_cost
        inst_cost = parallel_cables * cable_length * cable_inst_cost

        return equip_cost, inst_cost