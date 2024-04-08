from pyomo.environ import *

def calculate_costs(model):
    """
    Calculate costs for wind farms, substations, and cables.
    """
    # Define the cost variables
    wind_farm_cost = 10000  # Example wind farm cost
    substation_cost = 5000  # Example substation cost
    cable_cost_per_unit_distance = 2  # Example cable cost per unit distance

    # Cable cost from wind farm to substation
    cable_cost_wf_to_ss = sum(model.capacity[w] * model.distance[w, s] * cable_cost_per_unit_distance
                                for w in model.wind_farms for s in model.substations)

    # Cable cost from substation to onshore
    cable_cost_ss_to_onshore = sum(model.substation_capacity[s] * model.distance[s, 'onshore'] *
                                    cable_cost_per_unit_distance for s in model.substations)

    # Wind farm costs
    total_wind_farm_cost = wind_farm_cost * sum(model.capacity[w] for w in model.wind_farms)

    # Substation costs
    total_substation_cost = substation_cost * len(model.substations)

    return total_wind_farm_cost, total_substation_cost, cable_cost_wf_to_ss, cable_cost_ss_to_onshore

def objective_function(model):
    """
    Objective function to minimize costs.
    """
    # Calculate costs
    total_wind_farm_cost, total_substation_cost, cable_cost_wf_to_ss, cable_cost_ss_to_onshore = calculate_costs(model)

    # Total cost
    total_cost = total_wind_farm_cost + total_substation_cost + cable_cost_wf_to_ss + cable_cost_ss_to_onshore

    return total_cost

def constraints(model):
    """
    Constraints for the optimization problem.
    """
    # One wind farm connects to one substation
    def one_wind_farm_to_one_substation_rule(model, s):
        return sum(model.connection[w, s] for w in model.wind_farms) == 1
    model.one_wind_farm_to_one_substation_constraint = Constraint(model.substations, rule=one_wind_farm_to_one_substation_rule)

    # Substation capacity constraint
    def substation_capacity_rule(model, s):
        return model.substation_capacity[s] == sum(model.capacity[w] * model.connection[w, s] for w in model.wind_farms)
    model.substation_capacity_constraint = Constraint(model.substations, rule=substation_capacity_rule)

    # Substation connects to onshore only if it's connected to a wind farm
    def substation_connects_to_onshore_rule(model, s):
        if sum(model.connection[w, s] for w in model.wind_farms) > 0:
            return sum(model.connection[s, 'onshore'] for s in model.substations) == 1
        else:
            return Constraint.Skip
    model.substation_connects_to_onshore_constraint = Constraint(model.substations, rule=substation_connects_to_onshore_rule)

    return model

def solve_optimization(wind_farms, substations, distances):
    """
    Solve the LP optimization problem.
    """
    model = ConcreteModel()

    # Sets
    model.wind_farms = Set(initialize=wind_farms)
    model.substations = Set(initialize=substations)

    # Parameters
    model.capacity = Param(model.wind_farms, initialize=100)  # Example capacity for wind farms
    model.distance = Param(model.wind_farms | model.substations | {'onshore'}, model.wind_farms | model.substations | {'onshore'}, initialize=distances)  # Example distances
    model.substation_capacity = Var(model.substations, within=NonNegativeReals)
    model.connection = Var(model.wind_farms | model.substations, model.substations | {'onshore'}, within=Binary)

    # Objective function
    model.objective = Objective(rule=objective_function, sense=minimize)

    # Constraints
    model = constraints(model)

    # Solve the model
    solver = SolverFactory('glpk')
    results = solver.solve(model)

    # Return the results
    return model, results

# Example wind farms, substations, and distances (coordinates)
wind_farms = ['WF1', 'WF2']
substations = ['SS1', 'SS2']
distances = {('WF1', 'SS1'): 50, ('WF1', 'SS2'): 60, ('WF2', 'SS1'): 70, ('WF2', 'SS2'): 80,
             ('SS1', 'onshore'): 100, ('SS2', 'onshore'): 110}

# Solve the optimization problem
model, results = solve_optimization(wind_farms, substations, distances)

# Print the results
print(results)
print("Total Cost:", model.objective())
