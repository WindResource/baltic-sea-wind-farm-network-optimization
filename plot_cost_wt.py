import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

from scripts.present_value import present_value
from scripts.wt_cost import check_supp, calc_equip_cost, calc_inst_deco_cost

# Define font parameters
font = {'family': 'serif',
        'weight': 'normal',
        'size': 12}

# Set font
plt.rc('font', **font)


def calc_total_cost(water_depth, ice_cover, port_distance, turbine_capacity):
    """
    Calculate various costs for a given set of parameters.

    Parameters:
        water_depth (float): Water depth at the turbine location.
        ice_cover (int): Indicator if the area is ice-covered (1 for Yes, 0 for No).
        port_distance (float): Distance to the port.
        turbine_capacity (float): Capacity of the turbine.

    Returns:
        tuple: Total cost, equipment cost, installation cost, total operational cost, decommissioning cost in millions of Euros.
    """
    support_structure = check_supp(water_depth)  # Determine support structure

    supp_cost, turbine_cost = calc_equip_cost(water_depth, support_structure, ice_cover, turbine_capacity)  # Calculate equipment cost

    equip_cost = supp_cost + turbine_cost
    
    inst_cost = calc_inst_deco_cost(water_depth, port_distance, turbine_capacity, "inst")  # Calculate installation cost
    deco_cost = calc_inst_deco_cost(water_depth, port_distance, turbine_capacity, "deco")  # Calculate decommissioning cost

    ope_cost_yearly = 0.025 * turbine_cost  # Calculate yearly operational cost

    total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost = present_value(equip_cost, inst_cost, ope_cost_yearly, deco_cost)  # Calculate present value of cost

    total_cost *= 1e-6  # Convert cost to millions of Euros
    equip_cost *= 1e-6
    inst_cost *= 1e-6
    total_ope_cost *= 1e-6
    deco_cost *= 1e-6

    return total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost

def plot_costs_vs_water_depth():
    water_depths = np.linspace(0, 120, 500)
    ice_cover = 0  # Assuming no ice cover for simplicity
    port_distance = 100  # Assuming a constant port distance for simplicity
    turbine_capacity = 15  # Assuming a constant turbine capacity of 15 MW

    total_costs, equip_costs, inst_costs, total_ope_costs, deco_costs = [], [], [], [], []

    for wd in water_depths:
        total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost = calc_total_cost(wd, ice_cover, port_distance, turbine_capacity)
        total_costs.append(total_cost)
        equip_costs.append(equip_cost)
        inst_costs.append(inst_cost)
        total_ope_costs.append(total_ope_cost)
        deco_costs.append(deco_cost)

    fig, axs = plt.subplots(2, 1, figsize=(6, 6), gridspec_kw={'height_ratios': [4, 1]}, sharex=True)
    
    # Plotting the larger range
    axs[0].plot(water_depths, total_costs, label='Total PV')
    axs[0].plot(water_depths, equip_costs, label='Equipment PV')
    axs[0].plot(water_depths, inst_costs, label='Installation PV')
    axs[0].plot(water_depths, total_ope_costs, label='Total Operating PV')
    axs[0].plot(water_depths, deco_costs, label='Decommissioning PV')

    axs[0].set_xlim(0, 120)
    axs[0].set_ylim(0, 50)
    axs[0].yaxis.set_major_locator(MultipleLocator(10))
    axs[0].yaxis.set_minor_locator(MultipleLocator(2.5))

    # Plotting the smaller range
    axs[1].plot(water_depths, total_costs, label='Total PV')
    axs[1].plot(water_depths, equip_costs, label='Equipment PV')
    axs[1].plot(water_depths, inst_costs, label='Installation PV')
    axs[1].plot(water_depths, total_ope_costs, label='Total Operating PV')
    axs[1].plot(water_depths, deco_costs, label='Decommissioning PV')

    axs[0].set_xlim(0, 120)
    axs[1].set_ylim(0, 2)
    axs[1].yaxis.set_major_locator(MultipleLocator(1))
    axs[1].yaxis.set_minor_locator(MultipleLocator(0.25))

    for ax in axs:
        ax.xaxis.set_major_locator(MultipleLocator(20))
        ax.xaxis.set_minor_locator(MultipleLocator(5))
        ax.grid(which='major', linestyle='-', linewidth='0.5', color='gray')
        ax.grid(which='minor', linestyle=':', linewidth='0.5', color='gray')
        ax.minorticks_on()
        
        ax.axvline(x=25, color='grey', linewidth='1.5', linestyle='--')
        ax.axvline(x=55, color='grey', linewidth='1.5', linestyle='--')
        
    axs[0].text(2, plt.ylim()[1] * 0.5, 'Monopile', rotation=90)
    axs[0].text(27, plt.ylim()[1] * 0.5, 'Jacket', rotation=90)
    axs[0].text(57, plt.ylim()[1] * 0.5, 'Floating', rotation=90)

    axs[1].set_xlabel('Water Depth (m)')
    axs[0].set_ylabel('Cost (M€)')
    axs[1].set_ylabel('Cost (M€)')

    lines, labels = axs[0].get_legend_handles_labels()
    fig.legend(lines, labels, bbox_to_anchor=(0.5, 1.02), loc='center', ncol=2, frameon=False)
    
    plt.tight_layout()
    plt.savefig(f'C:\\Users\\cflde\\Downloads\\wt_total_cost_vs_water_depth.png', dpi=400, bbox_inches='tight')
    plt.show()

def plot_equip_costs_vs_water_depth():
    water_depths = np.linspace(0, 120, 500)
    ice_cover = 0  # Assuming no ice cover for simplicity
    turbine_capacity = 15  # Assuming a constant turbine capacity of 5 MW

    supp_costs, turbine_costs, equip_costs = [], [], []

    for wd in water_depths:
        support_structure = check_supp(wd)
        supp_cost, turbine_cost = calc_equip_cost(wd, support_structure, ice_cover, turbine_capacity)
        equip_cost = supp_cost + turbine_cost
        supp_costs.append(supp_cost * 1e-6)  # Convert to millions of Euros
        turbine_costs.append(turbine_cost * 1e-6)  # Convert to millions of Euros
        equip_costs.append(equip_cost * 1e-6)  # Convert to millions of Euros

    plt.figure(figsize=(6, 4.5))
    plt.plot(water_depths, equip_costs, label='Total Equipment Cost')
    plt.plot(water_depths, supp_costs, label='Support Structure Cost')
    plt.plot(water_depths, turbine_costs, label='Turbine Equipment Cost')
    plt.xlabel('Water Depth (m)')
    plt.ylabel('Cost (M\u20AC)')

    # Set domain and range
    plt.xlim(0, 120)
    plt.ylim(0, 50)

    x_major_locator = MultipleLocator(20)
    x_minor_locator = MultipleLocator(5)
    y_major_locator = MultipleLocator(10)
    y_minor_locator = MultipleLocator(2.5)

    plt.gca().xaxis.set_major_locator(x_major_locator)
    plt.gca().xaxis.set_minor_locator(x_minor_locator)
    plt.gca().yaxis.set_major_locator(y_major_locator)
    plt.gca().yaxis.set_minor_locator(y_minor_locator)

    plt.grid(which='major', linestyle='-', linewidth='0.5', color='gray')
    plt.grid(which='minor', linestyle=':', linewidth='0.5', color='gray')
    plt.minorticks_on()
    
    # Add vertical lines for support structure domains
    plt.axvline(x=25, color='grey', linewidth='1.5', linestyle='--')
    plt.axvline(x=55, color='grey', linewidth='1.5', linestyle='--')
    
    # Add vertical text annotations
    plt.text(2, 2, 'Monopile', rotation=90)
    plt.text(27, 2, 'Jacket', rotation=90)
    plt.text(57, 2, 'Floating', rotation=90)

    plt.legend(bbox_to_anchor=(0, 1.25), loc='upper left', ncol=1, frameon=False)
    plt.grid(True)
    plt.savefig(f'C:\\Users\\cflde\\Downloads\\wt_equip_cost_vs_water_depth.png', dpi=400, bbox_inches='tight')
    plt.show()

def plot_inst_deco_cost_vs_port_distance():
    port_distances = np.linspace(0, 200, 100)
    turbine_capacity = 15
    water_depths = [40, 80]

    fig, axs = plt.subplots(2, 1, figsize=(6, 6), gridspec_kw={'height_ratios': [1, 1]}, sharex=True)
    
    for i, water_depth in enumerate(water_depths):
        inst_costs, deco_costs = [], []

        for pd in port_distances:
            inst_cost = calc_inst_deco_cost(water_depth, pd, turbine_capacity, "inst")
            deco_cost = calc_inst_deco_cost(water_depth, pd, turbine_capacity, "deco")
            inst_costs.append(inst_cost * 1e-6)  # Convert to millions of Euros
            deco_costs.append(deco_cost * 1e-6)  # Convert to millions of Euros

        axs[i].plot(port_distances, inst_costs, label='Installation Cost')
        axs[i].plot(port_distances, deco_costs, label='Decommissioning Cost')
        
        # Set domain and range
        axs[i].set_xlim(0, 200)
        axs[i].set_ylim(0, 2)

        x_major_locator = MultipleLocator(20)
        x_minor_locator = MultipleLocator(5)
        y_major_locator = MultipleLocator(0.5)
        y_minor_locator = MultipleLocator(0.125)

        axs[i].xaxis.set_major_locator(x_major_locator)
        axs[i].xaxis.set_minor_locator(x_minor_locator)
        axs[i].yaxis.set_major_locator(y_major_locator)
        axs[i].yaxis.set_minor_locator(y_minor_locator)

        axs[i].grid(which='major', linestyle='-', linewidth='0.5', color='gray')
        axs[i].grid(which='minor', linestyle=':', linewidth='0.5', color='gray')
        axs[i].minorticks_on()

        axs[i].set_ylabel('Cost (M€)')
        
        supp_struct_str = f'Monopile/Jacket' if water_depth < 55 else f'Floating'
        axs[i].text(2, 0.05, supp_struct_str, rotation=90, ha='left', va='bottom')
        
        # Add horizontal text annotation in the top left of the figure
        axs[i].text(2, 1.95, f'$WD ={water_depth}m$', ha='left', va='top')
        
    axs[1].set_xlabel('Distance to Closest Port (km)')
    
    lines, labels = axs[0].get_legend_handles_labels()
    fig.legend(lines, labels, bbox_to_anchor=(0.5, 1.02), loc='center', ncol=2, frameon=False)
    
    plt.tight_layout()
    plt.savefig(f'C:\\Users\\cflde\\Downloads\\wt_cost_vs_port_distance_{supp_struct_str.replace("/","-")}.png', dpi=400, bbox_inches='tight')
    plt.show()

def plot_ic_costs_vs_water_depth():
    water_depths = np.linspace(0, 120, 500)
    port_distance = 100  # Assuming a constant port distance for simplicity
    turbine_capacity = 15  # Assuming a constant turbine capacity of 15 MW

    # Initialize lists to store the costs
    total_costs_ice0, equip_costs_ice0, inst_costs_ice0, total_ope_costs_ice0, deco_costs_ice0 = [], [], [], [], []
    total_costs_ice1, equip_costs_ice1, inst_costs_ice1, total_ope_costs_ice1, deco_costs_ice1 = [], [], [], [], []

    for wd in water_depths:
        # Costs for ice_cover = 0
        total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost = calc_total_cost(wd, 0, port_distance, turbine_capacity)
        total_costs_ice0.append(total_cost)
        equip_costs_ice0.append(equip_cost)
        inst_costs_ice0.append(inst_cost)
        total_ope_costs_ice0.append(total_ope_cost)
        deco_costs_ice0.append(deco_cost)
        
        # Costs for ice_cover = 1
        total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost = calc_total_cost(wd, 1, port_distance, turbine_capacity)
        total_costs_ice1.append(total_cost)
        equip_costs_ice1.append(equip_cost)
        total_ope_costs_ice1.append(total_ope_cost)

    fig, axs = plt.subplots(2, 1, figsize=(6, 6), gridspec_kw={'height_ratios': [4, 1]}, sharex=True)
    
    # Plot the solid lines for ice_cover = 0
    line1, = axs[0].plot(water_depths, total_costs_ice0, label='Total PV', linestyle='-')
    line2, = axs[0].plot(water_depths, equip_costs_ice0, label='Equipment PV', linestyle='-')
    line3, = axs[0].plot(water_depths, inst_costs_ice0, label='Installation PV', linestyle='-')
    line4, = axs[0].plot(water_depths, total_ope_costs_ice0, label='Total Operating PV', linestyle='-')
    line5, = axs[0].plot(water_depths, deco_costs_ice0, label='Decommissioning PV', linestyle='-')

    # Plot the dashed lines for ice_cover = 1 using colors from the solid lines
    axs[0].plot(water_depths, total_costs_ice1, label='Total PV (IC)', color=line1.get_color(), linestyle='--')
    axs[0].plot(water_depths, equip_costs_ice1, label='Equipment PV (IC)', color=line2.get_color(), linestyle='--')
    axs[0].plot(water_depths, total_ope_costs_ice1, label='Total Operating PV (IC)', color=line4.get_color(), linestyle='--')

    axs[0].set_xlim(0, 120)
    axs[0].set_ylim(0, 60)
    axs[0].yaxis.set_major_locator(MultipleLocator(10))
    axs[0].yaxis.set_minor_locator(MultipleLocator(2.5))

    # Plot the smaller range for ice_cover = 0
    axs[1].plot(water_depths, total_costs_ice0, linestyle='-', color=line1.get_color())
    axs[1].plot(water_depths, equip_costs_ice0, linestyle='-', color=line2.get_color())
    axs[1].plot(water_depths, inst_costs_ice0, linestyle='-', color=line3.get_color())
    axs[1].plot(water_depths, total_ope_costs_ice0, linestyle='-', color=line4.get_color())
    axs[1].plot(water_depths, deco_costs_ice0, linestyle='-', color=line5.get_color())

    # Plot the smaller range for ice_cover = 1
    axs[1].plot(water_depths, total_costs_ice1, linestyle='--', color=line1.get_color())
    axs[1].plot(water_depths, equip_costs_ice1, linestyle='--', color=line2.get_color())
    axs[1].plot(water_depths, total_ope_costs_ice1, linestyle='--', color=line4.get_color())

    axs[1].set_ylim(0, 2)
    axs[1].yaxis.set_major_locator(MultipleLocator(1))
    axs[1].yaxis.set_minor_locator(MultipleLocator(0.25))

    for ax in axs:
        ax.xaxis.set_major_locator(MultipleLocator(20))
        ax.xaxis.set_minor_locator(MultipleLocator(5))
        ax.grid(which='major', linestyle='-', linewidth='0.5', color='gray')
        ax.grid(which='minor', linestyle=':', linewidth='0.5', color='gray')
        ax.minorticks_on()
        
        ax.axvline(x=25, color='grey', linewidth='1.5', linestyle='--')
        ax.axvline(x=55, color='grey', linewidth='1.5', linestyle='--')
        
    axs[0].text(2, axs[0].get_ylim()[1] * 0.05, 'Monopile', rotation=90)
    axs[0].text(27, axs[0].get_ylim()[1] * 0.05, 'Jacket', rotation=90)
    axs[0].text(57, axs[0].get_ylim()[1] * 0.05, 'Floating', rotation=90)

    axs[1].set_xlabel('Water Depth (m)')
    axs[0].set_ylabel('Cost (M€)')
    axs[1].set_ylabel('Cost (M€)')

    lines, labels = axs[0].get_legend_handles_labels()
    fig.legend(lines, labels, bbox_to_anchor=(0.5, 1.08), loc='center', ncol=2, frameon=False)
    
    plt.tight_layout()
    plt.savefig(f'C:\\Users\\cflde\\Downloads\\ic_wt_total_cost_vs_water_depth.png', dpi=400, bbox_inches='tight')
    plt.show()

if __name__ == "__main__":

    plot_costs_vs_water_depth()

    plot_equip_costs_vs_water_depth()

    plot_inst_deco_cost_vs_port_distance()

    plot_ic_costs_vs_water_depth()