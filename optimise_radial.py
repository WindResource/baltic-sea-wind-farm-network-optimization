from pyomo.environ import *
import numpy as np
import os
from itertools import product

def present_value(equip_cost, inst_cost, ope_cost_yearly, deco_cost):
    """
    Calculate the total present value of cable cost.

    Parameters:
        equip_cost (float): Equipment cost.
        inst_cost (float): Installation cost.
        ope_cost_yearly (float): Yearly operational cost.
        deco_cost (float): Decommissioning cost.

    Returns:
        tuple: A tuple containing the equipment cost, installation cost, and total present value of cost.
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

def onss_cost_lin(capacity, threshold):
    """
    Calculate the cost for ONSS expansion above a certain capacity.

    Parameters:
    - capacity (float): The total capacity for which the cost is to be calculated.
    - threshold (float): The capacity threshold specific to the ONSS above which cost are incurred.
    
    Returns:
    - (float) Cost of expanding the ONSS if the capacity exceeds the threshold.
    """
    
    overcap_cost = 0.050 # Million EU/ MW
    
    # Calculate the cost function: difference between capacity and threshold multiplied by the cost factor
    cost_function = (capacity - threshold) * overcap_cost
    
    return cost_function

def ec_cost_lin(distance, capacity, polarity="AC"):
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

    cable_length = 1.2 * distance
    cable_capacity = 348 # MW
    cable_equip_cost = 0.860 # Million EU/km
    cable_inst_cost = 0.540 # Million EU/km
    capacity_factor = 0.90
    
    parallel_cables = capacity / (cable_capacity * capacity_factor)
    
    equip_cost = parallel_cables * cable_length * cable_equip_cost
    inst_cost = parallel_cables * cable_length * cable_inst_cost
    
    ope_cost_yearly = 0.2 * 1e-2 * equip_cost
    
    deco_cost = 0.5 * inst_cost

    # Calculate present value
    total_cost = present_value(equip_cost, inst_cost, ope_cost_yearly, deco_cost)

    return total_cost

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great-circle distance between two points
    on the Earth (specified in decimal degrees) using NumPy for calculations.
    """
    # Convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat/2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2.0)**2
    c = 2 * np.arcsin(np.sqrt(a))
    r = 6371  # Radius of Earth in kilometers
    return c * r

def find_viable_ec(wf_lon, wf_lat, onss_lon, onss_lat, wf_iso, onss_iso):
    """
    Find all pairs of offshore and onshore substations within 300km,
    ensuring that they belong to the same country based on their ISO codes.
    
    Parameters are dictionaries indexed by substation IDs with longitude, latitude, and ISO codes.
    """
    connections = []
    for wf_id, onss_id in product(wf_lon.keys(), onss_lon.keys()):
        # Calculate the distance first to see if they are within the viable range
        distance = haversine(wf_lon[wf_id], wf_lat[wf_id], onss_lon[onss_id], onss_lat[onss_id])
        if distance <= 300:  # Check if the distance is within 300 km
            # Then check if the ISO codes match for the current offshore and onshore substation pair
            if wf_iso[wf_id] == onss_iso[onss_id]:
                connections.append((int(wf_id), int(onss_id)))
    return connections

def get_viable_entities(viable_ec):
    """
    Identifies unique wind farm, energy hub, and onshore substation IDs
    based on their involvement in viable export and export cable connections.

    Parameters:
    - viable_ec (list of tuples): List of tuples, each representing a viable connection
        between a wind farm and an energy hub (wf_id, onss_id).

    Returns:
    - viable_wf (set): Set of wind farm IDs with at least one viable connection to an energy hub.
    - viable_onss (set): Set of energy hub IDs involved in at least one viable connection
        either to a wind farm or an onshore substation.
    - viable_onss (set): Set of onshore substation IDs with at least one viable connection to an energy hub.
    """
    viable_wf = set()
    viable_onss = set()

    # Extract unique offshore and onshore substation IDs from export cable connections
    for wf_id, onss_id in viable_ec:
        viable_wf.add(int(wf_id))
        viable_onss.add(int(onss_id))

    return viable_wf, viable_onss

def opt_model(workspace_folder):
    """
    Create an optimization model for offshore wind farm layout optimization.

    Parameters:
    - workspace_folder (str): The path to the workspace folder containing datasets.

    Returns:
    - model: Pyomo ConcreteModel object representing the optimization model.
    """
    
    """
    Initialise model
    """
    print("Initialising model...")
    
    # Create a Pyomo model
    model = ConcreteModel()

    """
    Process data
    """
    print("Processing data...")
    
    # Mapping ISO country codes of Baltic Sea countries to unique integers
    iso_to_int_mp = {
        'DE': 1,  # Germany
        'DK': 2,  # Denmark
        'EE': 3,  # Estonia
        'FI': 4,  # Finland
        'LV': 5,  # Latvia
        'LT': 6,  # Lithuania
        'PL': 7,  # Poland
        'SE': 8   # Sweden
    }

    # Load datasets
    wf_dataset_file = os.path.join(workspace_folder, 'wf_data.npy')
    onss_dataset_file = os.path.join(workspace_folder, 'onss_data.npy')
    
    wf_dataset = np.load(wf_dataset_file, allow_pickle=True)
    onss_dataset = np.load(onss_dataset_file, allow_pickle=True)

    # Component identifiers
    wf_ids = [int(data[0]) for data in wf_dataset]
    onss_ids = [int(data[0]) for data in onss_dataset]

    # Wind farm data
    wf_iso, wf_lon, wf_lat, wf_cap, wf_cost = {}, {}, {}, {}, {}

    for data in wf_dataset:
        id = int(data[0])
        wf_iso[id] = iso_to_int_mp[data[1]]
        wf_lon[id] = data[2]
        wf_lat[id] = data[3]
        wf_cap[id] = data[5]
        wf_cost[id] = data[6] * 1e-3 #Meu
    
    # Onshore substation data
    onss_iso, onss_lon, onss_lat, onss_thold = {}, {}, {}, {}

    for data in onss_dataset:
        id = int(data[0])
        onss_iso[id] = iso_to_int_mp[data[1]]
        onss_lon[id] = data[2]
        onss_lat[id] = data[3]
        onss_thold[id] = data[4]

    """
    Define model parameters
    """
    print("Defining model parameters...")
    
    # Identifiers model components
    model.wf_ids = Set(initialize=wf_ids)
    model.onss_ids = Set(initialize=onss_ids)
    
    # Wind farm model parameters
    model.wf_iso = Param(model.wf_ids, initialize=wf_iso, within=NonNegativeIntegers)
    model.wf_lon = Param(model.wf_ids, initialize=wf_lon, within=NonNegativeReals)
    model.wf_lat = Param(model.wf_ids, initialize=wf_lat, within=NonNegativeReals)
    model.wf_cap = Param(model.wf_ids, initialize=wf_cap, within=NonNegativeIntegers)
    model.wf_cost = Param(model.wf_ids, initialize=wf_cost, within=NonNegativeReals)

    # Onshore substation model parameters
    model.onss_iso = Param(model.onss_ids, initialize=onss_iso, within=NonNegativeIntegers)
    model.onss_lon = Param(model.onss_ids, initialize=onss_lon, within=NonNegativeReals)
    model.onss_lat = Param(model.onss_ids, initialize=onss_lat, within=NonNegativeReals)
    model.onss_thold = Param(model.onss_ids, initialize=onss_thold, within=NonNegativeIntegers)

    """
    Define decision variables
    """
    print("Defining decision parameters...")
    
    # Calculate viable connections
    viable_ec = find_viable_ec(wf_lon, wf_lat, onss_lon, onss_lat, wf_iso, onss_iso)

    model.viable_ec_ids = Set(initialize= viable_ec, dimen=2)
    
    # Calculate viable entities based on the viable connections
    model.viable_wf_ids, model.viable_onss_ids = get_viable_entities(viable_ec)
    
    # Initialize variables
    model.wf_bool_var = Var(model.viable_wf_ids, within=Binary)
    
    model.onss_cap_var = Var(model.viable_onss_ids, within=NonNegativeReals)
    model.ec_cap_var = Var(model.viable_ec_ids, within=NonNegativeReals)
    
    model.onss_cost_var = Var(model.viable_onss_ids, within=NonNegativeReals)
    
    # Define a dictionary containing variable names and their respective lengths
    print_variables = {
        "select_wf": model.wf_bool_var,
        "select_onss": model.onss_cap_var,
        "select_ec": model.ec_cap_var
    }

    # Iterate over the dictionary and print variable ids and their lengths
    for name, var in print_variables.items():
        print(f"{name} ids:", list(var)[:20])  # Print variable ids
        print(f"Number of {name} indices:", len(var))  # Print number of indices

    """
    Define Expressions
    """
    print("Defining expressions...")

    """
    Define expressions for wind farms (WF)
    """
    def wf_cost_rule(model, wf):
        return model.wf_cost[wf] * model.wf_bool_var[wf]
    model.wf_cost_exp = Expression(model.viable_wf_ids, rule=wf_cost_rule)

    """
    Define distance and capacity expressions for Export Cables (EC)
    """
    def ec_distance_rule(model, wf, onss):
        return haversine(model.wf_lon[wf], model.wf_lat[wf], model.onss_lon[onss], model.onss_lat[onss])
    model.ec_dist_exp = Expression(model.viable_ec_ids, rule=ec_distance_rule)

    def ec_cost_rule(model, wf, onss):
        return ec_cost_lin(model.ec_dist_exp[wf, onss], model.ec_cap_var[wf, onss], polarity="AC")
    model.ec_cost_exp = Expression(model.viable_ec_ids, rule=ec_cost_rule)

    """
    Define expressions for Onshore Substation (ONSS) capacity
    """

    def onss_cost_rule(model, onss):
        return onss_cost_lin(model.onss_cap_var[onss], model.onss_thold[onss])
    model.onss_cost_exp = Expression(model.viable_onss_ids, rule=onss_cost_rule)

    """
    Define Objective function
    """
    print("Defining objective function...")

    def global_cost_rule(model):
        """
        Calculate the total cost of the energy system. This includes the cost of selecting
        and connecting wind farms, energy hubs, and onshore substations. The objective is to minimize this total cost.

        The total cost is computed by summing:
        - The cost of selected wind farms.
        - The operational cost of selected energy hubs.
        - The cost associated with export cables connecting wind farms to energy hubs.
        - The cost associated with export cables connecting energy hubs to onshore substations.

        Parameters:
        - model: The Pyomo model object containing all necessary decision variables and parameters.

        Returns:
        - The computed total cost of the network configuration, which the optimization process seeks to minimize.
        """
        wf_total_cost = sum(model.wf_cost_exp[wf] for wf in model.viable_wf_ids)
        onss_total_cost = sum(model.onss_cost_var[onss] for onss in model.viable_onss_ids)
        ec_total_cost = sum(model.ec_cost_exp[wf, onss] for (wf, onss) in model.viable_ec_ids)
        
        return wf_total_cost + ec_total_cost + onss_total_cost

    # Set the objective in the model
    model.global_cost_obj = Objective(rule=global_cost_rule, sense=minimize)

    """
    Define Constraints
    """
    print("Defining total capacity constraint...")

    def tot_wf_cap_rule(model):
        """
        Ensure the selected wind farms collectively meet a minimum required capacity.
        This capacity is specified as a fraction of the total potential capacity of all considered wind farms.
        """
        min_req_cap = 1 * sum(model.wf_cap[wf] for wf in model.viable_wf_ids)
        return sum(model.wf_bool_var[wf] * model.wf_cap[wf] for wf in model.viable_wf_ids) >= min_req_cap
    model.tot_wf_cap_con = Constraint(rule=tot_wf_cap_rule)
    
    print("Defining capacity constraints...")
    
    def ec_cap_connect_rule(model, wf):
        """
        Ensure each selected wind farm is connected to exactly one energy hub.
        The connection capacity must match the selected wind farm's capacity.
        """
        connect_to_onss = sum(model.ec_cap_var[wf, onss] for onss in model.viable_onss_ids if (wf, onss) in model.viable_ec_ids)
        return connect_to_onss >= model.wf_bool_var[wf] * model.wf_cap[wf]
    model.ec_cap_connect_con = Constraint(model.viable_wf_ids, rule=ec_cap_connect_rule)

    def onss_cap_connect_rule(model, onss):
        """
        Ensure the capacity of each energy hub matches or exceeds the total capacity of the connected wind farms.
        This ensures that the substation can handle all incoming power from the connected farms.
        """
        connect_from_wf = sum(model.ec_cap_var[wf, onss] for wf in model.viable_wf_ids if (wf, onss) in model.viable_ec_ids)
        return model.onss_cap_var[onss] >= connect_from_wf
    model.onss_cap_connect_con = Constraint(model.viable_onss_ids, rule=onss_cap_connect_rule)
    
    print("Defining the cost variables...")
    
    def onss_cost_rule(model, onss):
        """
        Ensure the cost variable for each onshore substation meets or exceeds the calculated cost.
        """
        return model.onss_cost_var[onss] >= model.onss_cost_exp[onss]
    model.onss_cost_con = Constraint(model.viable_onss_ids, rule=onss_cost_rule)
    
    """
    Solve the model
    """
    print("Solving the model...")
    
    solver_options = {
        'numerics/scaling': 1,  # Enable scaling
        'tolerances/feasibility': 1e-5,  # Tolerance for feasibility checks
        'tolerances/optimality': 1e-5,   # Tolerance for optimality conditions
        'tolerances/integrality': 1e-5,  # Tolerance for integer variable constraints
        'presolving/maxrounds': -1,      # Max presolve iterations to simplify the model
        'propagating/maxrounds': -1,     # Max constraint propagation rounds
        'parallel/threads': -1,          # Use all CPU cores for parallel processing
        'nodeselection': 'hybrid',       # Hybrid node selection in branch and bound
        'branching/varsel': 'pscost',    # Pseudocost variable selection in branching
        'separating/aggressive': 1,   # Enable aggressive separation
        'conflict/enable': 1,         # Activate conflict analysis
        'heuristics/rens/freq': 10,      # Frequency of RENS heuristic
        'heuristics/diving/freq': 10,    # Frequency of diving heuristic
        'propagating/maxroundsroot': 15, # Propagation rounds at root node
        'limits/nodes': 1e5,             # Maximum nodes in search tree
        'limits/totalnodes': 1e5,         # Total node limit across threads
        'emphasis/optimality': 1,   # Emphasize optimality
        'emphasis/memory': 1,           # Emphasize memory
        'separating/maxrounds': 10,  # Limit cut rounds at non-root nodes
        'heuristics/feaspump/freq': 10,  # Frequency of feasibility pump heuristic
        'tol': 0.01,  # Set the relative optimality gap tolerance to 1%
        'display/verblevel': 4  # Set verbosity level to display information about the solution
    }

    def save_results(model, workspace_folder):
        """
        Save the IDs of selected components of the optimization model along with all their corresponding parameters,
        including directly retrieved capacity and cost from the model expressions, into both .npy and .txt files as structured arrays.
        Headers are included in the .txt files for clarity.

        Parameters:
        - model: The optimized Pyomo model.
        - workspace_folder: The path to the directory where results will be saved.
        """
        def exp_f(e):
            return round(e.expr(), 3)
        
        def var_f(v):
            return round(v.value, 3)
        
        # Mapping ISO country codes of Baltic Sea countries to unique integers
        int_to_iso_mp = {
            1 : 'DE',  # Germany
            2 : 'DK',  # Denmark
            3 : 'EE',  # Estonia
            4 : 'FI',  # Finland
            5 : 'LV',  # Latvia
            6 : 'LT',  # Lithuania
            7 : 'PL',  # Poland
            8 : 'SE'   # Sweden
        }
        
        selected_components = {
            'wf_ids': {
                'data': np.array([(wf, int_to_iso_mp[model.wf_iso[wf]], model.wf_lon[wf], model.wf_lat[wf], model.wf_cap[wf], model.wf_cost[wf]) 
                                for wf in model.viable_wf_ids if model.wf_bool_var[wf].value > 0], 
                                dtype=[('id', int), ('iso', 'U2'), ('lon', float), ('lat', float), ('capacity', int), ('cost', int)]),
                'headers': "ID, ISO, Longitude, Latitude, Capacity, Cost"
            },
            'onss_ids': {
                'data': np.array([(onss, int_to_iso_mp[model.onss_iso[onss]], model.onss_lon[onss], model.onss_lat[onss], model.onss_thold[onss], var_f(model.onss_cap_var[onss]), var_f(model.onss_cost_var[onss])) 
                                for onss in model.viable_onss_ids if model.onss_cap_var[onss].value > 0], 
                                dtype=[('id', int), ('iso', 'U2'), ('lon', float), ('lat', float), ('threshold', int), ('capacity', float), ('cost', float)]),
                'headers': "ID, ISO, Longitude, Latitude, Threshold, Capacity, Cost"
            },
            'ec_ids': {
                'data': np.array([(wf, onss, model.wf_lon[wf], model.wf_lat[wf], model.onss_lon[onss], model.onss_lat[onss], var_f(model.ec_cap_var[wf, onss]), exp_f(model.ec_cost_exp[wf, onss])) 
                                for wf, onss in model.viable_ec_ids if model.ec_cap_var[wf, onss].value > 0], 
                                dtype=[('wf_id', int), ('onss_id', int), ('wf_lon', float), ('wf_lat', float), ('onss_lon', float), ('onss_lat', float), ('capacity', float), ('cost', float)]),
                'headers': "WF_ID, OSS_ID, WFLongitude, WFLatitude, OSSLongitude, OSSLatitude, Capacity, Cost"
            }
        }

        # Ensure the results directory exists
        results_dir = os.path.join(workspace_folder, "results", "radial")
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)

        total_capacity_cost = []

        for key, info in selected_components.items():
            npy_file_path = os.path.join(results_dir, f'{key}_r.npy')
            txt_file_path = os.path.join(results_dir, f'{key}_r.txt')

            # Save as .npy file
            np.save(npy_file_path, info['data'])

            # Save as .txt file for easier viewing
            with open(txt_file_path, 'w') as file:
                file.write(info['headers'] + '\n')  # Write the headers
                for entry in info['data']:
                    file.write(', '.join(map(str, entry)) + '\n')
            
            print(f'Saved {key} in {npy_file_path} and {txt_file_path}')

            # Calculate total capacity and cost for this component type
            total_capacity = sum(info['data']['capacity'])
            total_cost = sum(info['data']['cost'])
            total_capacity_cost.append((key, round(total_capacity), round(total_cost, 3)))

        # Calculate overall totals
        overall_capacity = sum(item[1] for item in total_capacity_cost)
        overall_cost = sum(item[2] for item in total_capacity_cost)
        total_capacity_cost.append(("overall", round(overall_capacity), round(overall_cost, 3)))

        # Create a structured array for total capacities and cost
        total_capacity_cost_array = np.array(total_capacity_cost, dtype=[('component', 'U10'), ('total_capacity', int), ('total_cost', float)])

        # Save the total capacities and cost in .npy and .txt files
        total_npy_file_path = os.path.join(results_dir, 'total_r.npy')
        total_txt_file_path = os.path.join(results_dir, 'total_r.txt')

        # Save as .npy file
        np.save(total_npy_file_path, total_capacity_cost_array)

        # Save as .txt file for easier viewing
        with open(total_txt_file_path, 'w') as file:
            file.write("Component, Total Capacity, Total Cost\n")
            for entry in total_capacity_cost_array:
                file.write(f'{entry[0]}, {entry[1]}, {entry[2]}\n')

        print(f'Saved total capacities and cost in {total_npy_file_path} and {total_txt_file_path}')

    # Set the path to the Scip solver executable
    scip_path = "C:\\Program Files\\SCIPOptSuite 9.0.0\\bin\\scip.exe"

    # Create a solver object and specify the solver executable path
    solver = SolverFactory('scip')
    solver.options['executable'] = scip_path

    # Define the path for the solver log
    solver_log_path = os.path.join(workspace_folder, "results", "radial", "solverlog_r.txt")

    # Solve the optimisation model
    results = solver.solve(model, tee=True, logfile=solver_log_path, options=solver_options)

    # Detailed checking of solver results
    if results.solver.status == SolverStatus.ok:
        if results.solver.termination_condition == TerminationCondition.optimal:
            print("Solver found an optimal solution.")
            print(f"Objective value: {round(model.global_cost_obj.expr(), 3)}")
            save_results(model, workspace_folder)
        elif results.solver.termination_condition == TerminationCondition.infeasible:
            print("Problem is infeasible. Check model constraints and data.")
        elif results.solver.termination_condition == TerminationCondition.unbounded:
            print("Problem is unbounded. Check objective function and constraints.")
        else:
            print(f"Solver terminated with condition: {results.solver.termination_condition}.")
    elif results.solver.status == SolverStatus.error:
        print("Solver error occurred. Check solver log for more details.")
    elif results.solver.status == SolverStatus.warning:
        print("Solver finished with warnings. Results may not be reliable.")
    else:
        print(f"Unexpected solver status: {results.solver.status}. Check solver log for details.")

    # Optionally, print a message about where the solver log was saved
    print(f"Solver log saved to {solver_log_path}")

    return None

# Define the main block
if __name__ == "__main__":
    # Specify the workspace folder
    workspace_folder = "C:\\Users\\cflde\\Documents\\Graduation Project\\ArcGIS Pro\\BalticSea\\Results\\datasets"

    # Call the optimization model function
    opt_model(workspace_folder)