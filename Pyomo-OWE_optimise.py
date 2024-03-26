"""
Wind Farm Optimization Model Setup

This script sets up and solves an optimization problem for selecting wind farms, offshore substations,
and their connections to minimize total costs while adhering to operational constraints. It considers
the costs of selecting wind farms and substations, plus the costs associated with connecting these
entities based on distances. It ensures configurations meet specified requirements, including
connection feasibility, capacity limitations, and distance constraints.

- generate_connections_and_costs(wind_farms, offshore_ss, onshore_ss, cost_per_distance_unit): Generates
    possible connections between entities and calculates associated costs based on distances.
    Parameters:
    - wind_farms (dict): Dictionary of wind farms with 'coordinates'.
    - offshore_ss (dict): Dictionary of offshore substations with 'coordinates'.
    - onshore_ss (dict): Dictionary of onshore substations with 'coordinates'.
    - cost_per_distance_unit (float): Cost factor per unit of distance (e.g., per kilometer).
    Returns:
    - tuple of (dict, dict): Two dictionaries, one for connection costs and one for distances, 
    with tuple keys representing connections (e.g., ('WF1', 'OSS1')).

- add_constraints(model, wind_farms, offshore_ss, onshore_ss, connections_costs, distances,
        min_total_capacity, max_wf_oss_dist, max_oss_ss_dist, universal_offshore_ss_max_capacity):
    Adds operational constraints to the optimization model, including capacity and distance limitations.
    Parameters:
    - model (ConcreteModel): The Pyomo model.
    - wind_farms (dict): Dictionary of wind farms.
    - offshore_ss (dict): Dictionary of offshore substations.
    - onshore_ss (dict): Dictionary of onshore substations.
    - connections_costs (dict): Dictionary of connection costs.
    - distances (dict): Dictionary of distances between entities.
    - min_total_capacity (float): Minimum total capacity requirement for selected wind farms.
    - max_wf_oss_dist (float): Maximum allowed distance from wind farms to offshore substations.
    - max_oss_ss_dist (float): Maximum allowed distance from offshore substations to onshore substations.
    - universal_offshore_ss_max_capacity (float): Maximum capacity for any offshore substation.
    
The optimization model is solved using Pyomo with GLPK as the solver. The solution includes selected
wind farms, offshore substations, and connections between them, adhering to defined constraints.
"""

import math
from pyomo.environ import *

# Define entities with costs, coordinates, and capacities
wind_farms = {
    'WF1': {'cost': 1000, 'coordinates': (10, 20), 'capacity': 150},
    'WF2': {'cost': 1500, 'coordinates': (15, 25), 'capacity': 200},
    'WF3': {'cost': 1100, 'coordinates': (10, 30), 'capacity': 100},
}

offshore_ss = {
    'OSS1': {'cost': 500, 'coordinates': (12, 22)},
    'OSS2': {'cost': 700, 'coordinates': (14, 26)},
}

onshore_ss = {
    'SS1': {'coordinates': (20, 40)},
    'SS2': {'coordinates': (25, 45)},
}

# Functions
def generate_connections_and_costs(wind_farms, offshore_ss, onshore_ss, cost_per_km_per_MW=0.5):
    """
    Generates all possible connections between wind farms, offshore substations, and onshore substations,
    along with their associated costs based on distance and capacity.
    """
    # Helper function to calculate Euclidean distance
    def calculate_distance(coord1, coord2):
        return math.sqrt((coord1[0] - coord2[0])**2 + (coord1[1] - coord2[1])**2)

    # Helper function to calculate connection cost
    def calculate_connection_cost(distance, capacity):
        return distance * capacity * cost_per_km_per_MW

    connections_costs = {}
    distances = {}
    total_capacity_per_oss = {oss: 0 for oss in offshore_ss}  # Track total capacity connected to each OSS

    # Calculate Wind Farm to Offshore Substation Connections
    for wf, wf_info in wind_farms.items():
        for oss, oss_info in offshore_ss.items():
            distance = calculate_distance(wf_info['coordinates'], oss_info['coordinates'])
            cost = calculate_connection_cost(distance, wf_info['capacity'])
            distances[(wf, oss)] = distance
            connections_costs[(wf, oss)] = cost
            total_capacity_per_oss[oss] += wf_info['capacity']  # Sum capacities for later calculation

    # Calculate Offshore Substation to Onshore Substation Connections
    for oss, oss_info in offshore_ss.items():
        for ss, ss_info in onshore_ss.items():
            distance = calculate_distance(oss_info['coordinates'], ss_info['coordinates'])
            capacity = total_capacity_per_oss[oss]  # Use total connected capacity for this connection
            cost = calculate_connection_cost(distance, capacity)
            distances[(oss,ss)] = distance
            connections_costs[(oss, ss)] = cost

    return distances, connections_costs

def create_decision_variables(model, wind_farms, offshore_ss, connections_costs):
    """
    Creates decision variables for the model.
    """
    model.select_wf = Var(wind_farms.keys(), within=Binary, initialize=0)  # Selection of Wind Farms
    model.select_oss = Var(offshore_ss.keys(), within=Binary, initialize=0)  # Selection of Offshore Substations
    model.select_conn = Var(connections_costs.keys(), within=Binary, initialize=0)  # Selection of Connections
    
def create_objective_function(model, wind_farms, offshore_ss, connections_costs):
    """
    Creates the objective function for the model.
    """
    model.total_cost = Objective(
        expr=sum(wind_farms[wf]['cost'] * model.select_wf[wf] for wf in wind_farms) +
        sum(offshore_ss[oss]['cost'] * model.select_oss[oss] for oss in offshore_ss) +
        sum(connections_costs[conn] * model.select_conn[conn] for conn in connections_costs),
        sense=minimize
    )
    
def add_constraints(model, wind_farms, offshore_ss, onshore_ss, connections_costs, distances, min_total_capacity, max_wf_oss_dist, max_oss_ss_dist, universal_offshore_ss_max_capacity):
    """
    Adds constraints to the model, including constraints for maximum distances.
    """
    
    # Constraint 1: If a wind farm is selected, it must connect to at least one offshore substation
    def wf_must_connect_to_oss_rule(model, wf):
        return sum(model.select_conn[(wf, oss)] for oss in offshore_ss if (wf, oss) in connections_costs) >= 1 * model.select_wf[wf]
    model.wf_must_connect_to_oss_constraint = Constraint(wind_farms.keys(), rule=wf_must_connect_to_oss_rule)

    # Constraint 2: If an offshore substation is selected, it must connect to at least one onshore substation
    def oss_connection_rule(model, oss):
        return sum(model.select_conn[(oss, ss)] for ss in onshore_ss if (oss, ss) in connections_costs) >= model.select_oss[oss]
    model.oss_connection_constraint = Constraint(offshore_ss.keys(), rule=oss_connection_rule)

    # Constraint 3: Connectivity between a wind farm and an offshore substation implies selection of both
    def wf_oss_selection_rule(model, wf, oss):
        if (wf, oss) in connections_costs:
            return model.select_conn[(wf, oss)] <= model.select_wf[wf]
        else:
            return Constraint.Skip
    model.wf_oss_selection_constraint = Constraint(wind_farms.keys(), offshore_ss.keys(), rule=wf_oss_selection_rule)

    # Constraint 4: Connectivity between an offshore substation and an onshore substation implies selection of the offshore substation
    def oss_ss_selection_rule(model, oss, ss):
        if (oss, ss) in connections_costs:
            return model.select_conn[(oss, ss)] <= model.select_oss[oss]
        else:
            return Constraint.Skip
    model.oss_ss_selection_constraint = Constraint(offshore_ss.keys(), onshore_ss.keys(), rule=oss_ss_selection_rule)

    # Constraint 5: Minimum total wind farm capacity
    def min_capacity_rule(model):
        return sum(wind_farms[wf]['capacity'] * model.select_wf[wf] for wf in wind_farms) >= min_total_capacity
    model.min_capacity_constraint = Constraint(rule=min_capacity_rule)

    # Constraint 6: Maximum distance from wind farms to offshore substations
    def max_wf_oss_distance_rule(model, wf, oss):
        if (wf, oss) in connections_costs:
            return distances[(wf, oss)] <= max_wf_oss_dist * model.select_conn[(wf, oss)]
        else:
            return Constraint.Skip
    model.max_wf_oss_distance_constraint = Constraint(wind_farms.keys(), offshore_ss.keys(), rule=max_wf_oss_distance_rule)

    # Constraint 7: Maximum distance from offshore substations to onshore substations
    def max_oss_ss_distance_rule(model, oss, ss):
        if (oss, ss) in connections_costs:
            return distances[(oss, ss)] <= max_oss_ss_dist * model.select_conn[(oss, ss)]
        else:
            return Constraint.Skip
    model.max_oss_ss_distance_constraint = Constraint(offshore_ss.keys(), onshore_ss.keys(), rule=max_oss_ss_distance_rule)

    # Constraint 8: If an offshore substation is connected to an onshore substation, it must be connected to at least one wind farm
    def oss_must_connect_to_wf_rule(model, oss):
        connected_to_ss = sum(model.select_conn[(oss, ss)] for ss in onshore_ss if (oss, ss) in connections_costs)
        connected_to_wf = sum(model.select_conn[(wf, oss)] for wf in wind_farms if (wf, oss) in connections_costs)
        return connected_to_wf >= connected_to_ss
    model.oss_must_connect_to_wf_constraint = Constraint(offshore_ss.keys(), rule=oss_must_connect_to_wf_rule)

    # Constraint 9: for Universal Maximum Capacity of an Offshore Substation
    def oss_max_capacity_rule(model, oss):
        return sum(wind_farms[wf]['capacity'] * model.select_conn[(wf, oss)] for wf in wind_farms if (wf, oss) in connections_costs) <= universal_offshore_ss_max_capacity
    model.oss_max_capacity_constraint = Constraint(offshore_ss.keys(), rule=oss_max_capacity_rule)


universal_offshore_ss_max_capacity = 400  # Maximum capacity in MW for any offshore substation

# Define cost per kilometer per MW for connection cost calculation
cost_per_km_per_MW = 0.5  # Example value, adjust based on actual cost factors

# Generate connections and their costs using the function
distances, connections_costs = generate_connections_and_costs(wind_farms, offshore_ss, onshore_ss, cost_per_km_per_MW)

min_total_capacity = 300  # Example: minimum total capacity in MW
max_wf_oss_dist = 10  # Example: maximum distance from wind farms to offshore substations in km
max_oss_ss_dist = 20  # Example: maximum distance from offshore substations to onshore substations in km

# Initialize the model
model = ConcreteModel()

# Create decision variables
create_decision_variables(model, wind_farms, offshore_ss, connections_costs)

# Create the objective function
create_objective_function(model, wind_farms, offshore_ss, connections_costs)

# Add constraints, including the new universal maximum capacity constraint
add_constraints(model, wind_farms, offshore_ss, onshore_ss, connections_costs, distances, min_total_capacity, max_wf_oss_dist, max_oss_ss_dist, universal_offshore_ss_max_capacity)

# Solve the model
solver = SolverFactory('glpk')
solver.solve(model)

# Output the solution
print("Selected Wind Farms:")
for wf in wind_farms:
    if model.select_wf[wf].value == 1:
        print(f"  {wf}")

print("\nSelected Offshore Substations:")
for oss in offshore_ss:
    if model.select_oss[oss].value == 1:
        print(f"  {oss}")

print("\nSelected Connections:")
for conn in connections_costs:
    if model.select_conn[conn].value == 1:
        print(f"  {conn} with cost {connections_costs[conn]:.2f}")
