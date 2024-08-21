import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from scripts.present_value import present_value
from scripts.eh_cost import check_supp, equip_cost_lin, inst_deco_cost_lin

# Define font parameters
font = {'family': 'serif',
        'weight': 'normal',
        'size': 12}

# Set font
plt.rc('font', **font)


def eh_cost_lin(water_depth, ice_cover, port_distance, eh_capacity):
    """
    """
    inst_year = 2040
    
    # Determine support structure
    supp_structure = check_supp(water_depth)
    
    # Calculate equipment cost
    supp_cost, conv_cost = equip_cost_lin(water_depth, supp_structure, ice_cover, eh_capacity)

    equip_cost = supp_cost + conv_cost
    
    # Calculate installation and decommissioning cost
    inst_cost = inst_deco_cost_lin(supp_structure, port_distance, "inst")
    deco_cost = inst_deco_cost_lin(supp_structure, port_distance, "deco")

    # Calculate yearly operational cost
    ope_cost_yearly = 0.03 * conv_cost
    
    total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost = present_value(inst_year, equip_cost, inst_cost, ope_cost_yearly, deco_cost)  # Calculate present value of cost

    return total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost

def plot_total_cost_vs_water_depth():
    water_depths = np.linspace(0, 300, 500)
    ice_cover = 0
    port_distance = 50
    eh_capacity = 1000

    total_costs, equip_costs, inst_costs, total_ope_costs, deco_costs = [], [], [], [], []

    for wd in water_depths:
        total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost = eh_cost_lin(wd, ice_cover, port_distance, eh_capacity)
        total_costs.append(total_cost)
        equip_costs.append(equip_cost)
        inst_costs.append(inst_cost)
        total_ope_costs.append(total_ope_cost)
        deco_costs.append(deco_cost)

    fig, axs = plt.subplots(2, 1, figsize=(6, 6), gridspec_kw={'height_ratios': [4, 1]}, sharex=True)

    # Plotting the larger range
    axs[0].plot(water_depths, total_costs, label='Total Cost')
    axs[0].plot(water_depths, equip_costs, label='Equipment Cost')
    axs[0].plot(water_depths, inst_costs, label='Installation Cost')
    axs[0].plot(water_depths, total_ope_costs, label='Operating Cost')
    axs[0].plot(water_depths, deco_costs, label='Decommissioning Cost')

    axs[0].set_xlim(0, 300)
    axs[0].set_ylim(0, 50)
    axs[0].yaxis.set_major_locator(MultipleLocator(50 / 4))
    axs[0].yaxis.set_minor_locator(MultipleLocator(50 / 4 / 4))

    # Plotting the smaller range
    axs[1].plot(water_depths, total_costs, label='Total Cost')
    axs[1].plot(water_depths, equip_costs, label='Equipment Cost')
    axs[1].plot(water_depths, inst_costs, label='Installation Cost')
    axs[1].plot(water_depths, total_ope_costs, label='Operating Cost')
    axs[1].plot(water_depths, deco_costs, label='Decommissioning Cost')

    axs[1].set_ylim(0, 1)
    axs[1].yaxis.set_major_locator(MultipleLocator(1))
    axs[1].yaxis.set_minor_locator(MultipleLocator(0.25))

    for ax in axs:
        ax.xaxis.set_major_locator(MultipleLocator(50))
        ax.xaxis.set_minor_locator(MultipleLocator(5))
        ax.grid(which='major', linestyle='-', linewidth='0.5', color='gray')
        ax.grid(which='minor', linestyle=':', linewidth='0.5', color='gray')
        ax.minorticks_on()
        
        ax.axvline(x=120, color='grey', linewidth='1.5', linestyle='--')
        
    axs[0].text(4, 5, 'Jacket', rotation=90, verticalalignment='bottom')
    axs[0].text(124, 5, 'Floating', rotation=90, verticalalignment='bottom')

    axs[1].set_xlabel('Water Depth (m)')
    axs[0].set_ylabel('Cost (M€)')
    axs[1].set_ylabel('Cost (M€)')

    # Get legend handles and labels
    lines, labels = axs[0].get_legend_handles_labels()
    
    # Define desired order for the legend
    desired_order = ['Total Cost', 'Equipment Cost', 'Operating Cost', 'Installation Cost',  'Decommissioning Cost']
    
    # Rearrange lines and labels according to desired order
    ordered_lines = [lines[labels.index(label)] for label in desired_order]
    ordered_labels = [label for label in desired_order]

    fig.legend(ordered_lines, ordered_labels, bbox_to_anchor=(0.5, 1.02), loc='center', ncol=2, frameon=False)
    
    plt.tight_layout()
    plt.savefig(f'C:\\Users\\cflde\\Downloads\\eh_total_cost_vs_water_depth.png', dpi=400, bbox_inches='tight')
    plt.show()

def plot_inst_deco_cost_vs_port_distance(water_depths):
    port_distances = np.linspace(0, 300, 500)

    fig, axs = plt.subplots(2, 1, figsize=(6, 6), gridspec_kw={'height_ratios': [1, 1]}, sharex=True)

    for i, water_depth in enumerate(water_depths):
        inst_costs, deco_costs = [], []

        for pd in port_distances:
            support_structure = check_supp(water_depth)
            inst_cost = inst_deco_cost_lin(support_structure, pd, "inst")
            deco_cost = inst_deco_cost_lin(support_structure, pd, "deco")
            inst_costs.append(inst_cost)
            deco_costs.append(deco_cost)

        axs[i].plot(port_distances, inst_costs, label='Installation Cost')
        axs[i].plot(port_distances, deco_costs, label='Decommissioning Cost')
        
        # Set domain and range
        axs[i].set_xlim(0, 300)
        axs[i].set_ylim(0, 1.5)

        x_major_locator = MultipleLocator(50)
        x_minor_locator = MultipleLocator(10)
        y_major_locator = MultipleLocator(1.5 / 2)
        y_minor_locator = MultipleLocator(1.5 / 4 / 4)

        axs[i].xaxis.set_major_locator(x_major_locator)
        axs[i].xaxis.set_minor_locator(x_minor_locator)
        axs[i].yaxis.set_major_locator(y_major_locator)
        axs[i].yaxis.set_minor_locator(y_minor_locator)

        axs[i].grid(which='major', linestyle='-', linewidth='0.5', color='gray')
        axs[i].grid(which='minor', linestyle=':', linewidth='0.5', color='gray')
        axs[i].minorticks_on()

        supp_struct_str = 'Jacket' if water_depth < 120 else 'Floating'
        axs[i].text(2, axs[i].get_ylim()[1] * 0.05, supp_struct_str, rotation=90)
        
        # Add horizontal text annotation in the top left of the figure
        axs[i].text(2, 1.45, f'$WD ={water_depth}m$', ha='left', va='top')

        axs[i].set_ylabel('Cost (M€)')

    # Get legend handles and labels from the first subplot
    lines, labels = axs[0].get_legend_handles_labels()
    
    # Define desired order for the legend
    desired_order = ['Installation Cost', 'Decommissioning Cost']
    
    # Rearrange lines and labels according to desired order
    ordered_lines = [lines[labels.index(label)] for label in desired_order]
    ordered_labels = [label for label in desired_order]

    fig.legend(ordered_lines, ordered_labels, bbox_to_anchor=(0.3, 1.03), loc='center', ncol=1, frameon=False)
        
    axs[1].set_xlabel('Port Distance (km)')
    
    plt.tight_layout()
    plt.savefig(f'C:\\Users\\cflde\\Downloads\\eh_inst_deco_cost_vs_port_distance.png', dpi=400, bbox_inches='tight')
    plt.show()

def plot_total_cost_vs_capacity(water_depth):
    eh_capacities = np.linspace(250, 2000, 500)  # Energy hub capacities in MW
    ice_cover = 0  # Assuming no ice cover for simplicity
    port_distance = 50  # Assuming a constant port distance

    total_costs, equip_costs, inst_costs, total_ope_costs, deco_costs = [], [], [], [], []

    for eh_capacity in eh_capacities:
        total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost = eh_cost_lin(water_depth, ice_cover, port_distance, eh_capacity)
        total_costs.append(total_cost)
        equip_costs.append(equip_cost)
        inst_costs.append(inst_cost)
        total_ope_costs.append(total_ope_cost)
        deco_costs.append(deco_cost)

    fig, axs = plt.subplots(2, 1, figsize=(6, 6), gridspec_kw={'height_ratios': [4, 1]}, sharex=True)

    # Plotting the larger range
    axs[0].plot(eh_capacities, total_costs, label='Total PV')
    axs[0].plot(eh_capacities, equip_costs, label='Equipment PV')
    axs[0].plot(eh_capacities, inst_costs, label='Installation PV')
    axs[0].plot(eh_capacities, total_ope_costs, label='Total Operating PV')
    axs[0].plot(eh_capacities, deco_costs, label='Decommissioning PV')

    axs[0].set_xlim(250, 2000)
    axs[0].set_ylim(0, 175)
    axs[0].yaxis.set_major_locator(MultipleLocator(25))
    axs[0].yaxis.set_minor_locator(MultipleLocator(5))

    # Plotting the smaller range
    axs[1].plot(eh_capacities, total_costs, label='Total PV')
    axs[1].plot(eh_capacities, equip_costs, label='Equipment PV')
    axs[1].plot(eh_capacities, inst_costs, label='Installation PV')
    axs[1].plot(eh_capacities, total_ope_costs, label='Total Operating PV')
    axs[1].plot(eh_capacities, deco_costs, label='Decommissioning PV')

    axs[1].set_ylim(0, 2)
    axs[1].yaxis.set_major_locator(MultipleLocator(2))
    axs[1].yaxis.set_minor_locator(MultipleLocator(0.5))

    for ax in axs:
        ax.xaxis.set_major_locator(MultipleLocator(250))
        ax.xaxis.set_minor_locator(MultipleLocator(25))
        ax.grid(which='major', linestyle='-', linewidth='0.5', color='gray')
        ax.grid(which='minor', linestyle=':', linewidth='0.5', color='gray')
        ax.minorticks_on()
        
    supp_struct_str = 'Jacket' if water_depth < 120 else 'Floating'
    axs[0].text(275, axs[0].get_ylim()[1] * 0.05, supp_struct_str, rotation=90, verticalalignment='bottom')

    axs[1].set_xlabel('Capacity (MW)')
    axs[0].set_ylabel('Cost (M€)')
    axs[1].set_ylabel('Cost (M€)')

    lines, labels = axs[0].get_legend_handles_labels()
    fig.legend(lines, labels, bbox_to_anchor=(0.5, 1.02), loc='center', ncol=2, frameon=False)
    
    plt.tight_layout()
    plt.savefig(f'C:\\Users\\cflde\\Downloads\\eh_total_cost_vs_capacity_{supp_struct_str}.png', dpi=400, bbox_inches='tight')
    plt.show()

def plot_equip_cost_vs_water_depth():
    water_depths = np.linspace(0, 300, 500)
    ice_cover = 0  # Assuming no ice cover for simplicity
    eh_capacity = 1000  # Assuming a constant energy hub capacity of 1GW

    supp_costs, conv_costs, equip_costs = [], [], []

    for wd in water_depths:
        support_structure = check_supp(wd)
        supp_cost, conv_cost = equip_cost_lin(wd, support_structure, ice_cover, eh_capacity)
        equip_cost = supp_cost + conv_cost
        supp_costs.append(supp_cost)
        conv_costs.append(conv_cost)
        equip_costs.append(equip_cost)

    plt.figure(figsize=(6, 5))
    plt.plot(water_depths, supp_costs, label='Support Structure Cost')
    plt.plot(water_depths, conv_costs, label='Transformer Cost')
    plt.plot(water_depths, equip_costs, label='Total Equipment Cost')
    
    # Set domain and range
    plt.xlim(0, 300)
    plt.ylim(0, 100)

    # Set the number of major ticks and minor ticks
    x_major_locator = MultipleLocator(50)
    x_minor_locator = MultipleLocator(5)
    y_major_locator = MultipleLocator(25)
    y_minor_locator = MultipleLocator(5)

    # Apply the major and minor tick locators
    plt.gca().xaxis.set_major_locator(x_major_locator)
    plt.gca().xaxis.set_minor_locator(x_minor_locator)
    plt.gca().yaxis.set_major_locator(y_major_locator)
    plt.gca().yaxis.set_minor_locator(y_minor_locator)

    # Add vertical lines for support structure domains
    plt.axvline(x=120, color='grey', linewidth=1.5, linestyle='--')
    
    # Add vertical text annotations
    plt.text(4, plt.ylim()[1] * 0.05, 'Jacket', rotation=90, verticalalignment='bottom')
    plt.text(124, plt.ylim()[1] * 0.05, 'Floating', rotation=90, verticalalignment='bottom')
    
    plt.grid(which='major', linestyle='-', linewidth='0.5', color='gray')
    plt.grid(which='minor', linestyle=':', linewidth='0.5', color='gray')
    plt.minorticks_on()
    
    plt.xlabel('Water Depth (m)')
    plt.ylabel('Cost (M\u20AC)')
    
    # Position the legend above the figure
    plt.legend(bbox_to_anchor=(0, 1.25), loc='upper left', ncol=1, frameon=False)
    
    plt.grid(True)
    plt.savefig(f'C:\\Users\\cflde\\Downloads\\eh_equip_cost_vs_water_depth.png', dpi=400, bbox_inches='tight')
    plt.show()


def plot_ic_cost_vs_water_depth():
    water_depths = np.linspace(0, 300, 500)
    port_distance = 50  # Assuming a constant port distance
    eh_capacity = 1000  # Assuming a constant energy hub capacity of 1GW

    # Initialize lists to store the costs for ice cover 0 and 1
    total_costs_ice0, equip_costs_ice0, inst_costs_ice0, total_ope_costs_ice0, deco_costs_ice0 = [], [], [], [], []
    total_costs_ice1, equip_costs_ice1, inst_costs_ice1, total_ope_costs_ice1, deco_costs_ice1 = [], [], [], [], []

    for wd in water_depths:
        # Costs for ice_cover = 0
        total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost = eh_cost_lin(wd, 0, port_distance, eh_capacity)
        total_costs_ice0.append(total_cost)
        equip_costs_ice0.append(equip_cost)
        inst_costs_ice0.append(inst_cost)
        total_ope_costs_ice0.append(total_ope_cost)
        deco_costs_ice0.append(deco_cost)
        
        # Costs for ice_cover = 1
        total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost = eh_cost_lin(wd, 1, port_distance, eh_capacity)
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

    axs[0].set_xlim(0, 300)
    axs[0].set_ylim(0, 125)
    axs[0].yaxis.set_major_locator(MultipleLocator(25))
    axs[0].yaxis.set_minor_locator(MultipleLocator(5))

    # Plotting the smaller range for ice_cover = 0
    axs[1].plot(water_depths, total_costs_ice0, linestyle='-', color=line1.get_color())
    axs[1].plot(water_depths, equip_costs_ice0, linestyle='-', color=line2.get_color())
    axs[1].plot(water_depths, inst_costs_ice0, linestyle='-', color=line3.get_color())
    axs[1].plot(water_depths, total_ope_costs_ice0, linestyle='-', color=line4.get_color())
    axs[1].plot(water_depths, deco_costs_ice0, linestyle='-', color=line5.get_color())

    # Plotting the smaller range for ice_cover = 1
    axs[1].plot(water_depths, total_costs_ice1, linestyle='--', color=line1.get_color())
    axs[1].plot(water_depths, equip_costs_ice1, linestyle='--', color=line2.get_color())
    axs[1].plot(water_depths, total_ope_costs_ice1, linestyle='--', color=line4.get_color())

    axs[1].set_ylim(0, 2)
    axs[1].yaxis.set_major_locator(MultipleLocator(1))
    axs[1].yaxis.set_minor_locator(MultipleLocator(0.25))

    for ax in axs:
        ax.xaxis.set_major_locator(MultipleLocator(50))
        ax.xaxis.set_minor_locator(MultipleLocator(5))
        ax.grid(which='major', linestyle='-', linewidth='0.5', color='gray')
        ax.grid(which='minor', linestyle=':', linewidth='0.5', color='gray')
        ax.minorticks_on()
        
        ax.axvline(x=120, color='grey', linewidth='1.5', linestyle='--')
        
    axs[0].text(4, plt.ylim()[1] * 0.05, 'Jacket', rotation=90, verticalalignment='bottom')
    axs[0].text(124, plt.ylim()[1] * 0.05, 'Floating', rotation=90, verticalalignment='bottom')

    axs[1].set_xlabel('Water Depth (m)')
    axs[0].set_ylabel('Cost (M€)')
    axs[1].set_ylabel('Cost (M€)')

    lines, labels = axs[0].get_legend_handles_labels()
    fig.legend(lines, labels, bbox_to_anchor=(0.5, 1.05), loc='center', ncol=2, frameon=False)
    
    plt.tight_layout()
    plt.savefig(f'C:\\Users\\cflde\\Downloads\\ic_eh_total_cost_vs_water_depth.png', dpi=400, bbox_inches='tight')
    plt.show()

def plot_ic_equip_cost_vs_water_depth():
    water_depths = np.linspace(0, 300, 500)
    eh_capacity = 1000  # Assuming a constant energy hub capacity of 1GW

    # Initialize lists to store the costs for ice cover 0 and 1
    supp_costs_ice0, conv_costs_ice0, equip_costs_ice0 = [], [], []
    supp_costs_ice1, conv_costs_ice1, equip_costs_ice1 = [], [], []

    for wd in water_depths:
        support_structure = check_supp(wd)

        # Costs for ice_cover = 0
        supp_cost, conv_cost = equip_cost_lin(wd, support_structure, 0, eh_capacity)
        equip_cost = supp_cost + conv_cost
        supp_costs_ice0.append(supp_cost)
        conv_costs_ice0.append(conv_cost)
        equip_costs_ice0.append(equip_cost)

        # Costs for ice_cover = 1
        supp_cost, conv_cost = equip_cost_lin(wd, support_structure, 1, eh_capacity)
        equip_cost = supp_cost + conv_cost
        supp_costs_ice1.append(supp_cost)
        conv_costs_ice1.append(conv_cost)
        equip_costs_ice1.append(equip_cost)

    plt.figure(figsize=(6, 5))
    
    # Plot the solid lines for ice_cover = 0
    plt.plot(water_depths, supp_costs_ice0, label='Support Structure Cost', linestyle='-')
    line2, = plt.plot(water_depths, conv_costs_ice0, label='Transformer Cost', linestyle='-')
    line3, = plt.plot(water_depths, equip_costs_ice0, label='Total Equipment Cost', linestyle='-')

    # Plot the dashed lines for ice_cover = 1 using colors from the solid lines
    plt.plot(water_depths, conv_costs_ice1, label='Transformer Cost (IC)', color=line2.get_color(), linestyle='--')
    plt.plot(water_depths, equip_costs_ice1, label='Total Equipment Cost (IC)', color=line3.get_color(), linestyle='--')

    # Set domain and range
    plt.xlim(0, 300)
    plt.ylim(0, 100)

    # Set the number of major ticks and minor ticks
    x_major_locator = MultipleLocator(50)
    x_minor_locator = MultipleLocator(5)
    y_major_locator = MultipleLocator(25)
    y_minor_locator = MultipleLocator(5)

    # Apply the major and minor tick locators
    plt.gca().xaxis.set_major_locator(x_major_locator)
    plt.gca().xaxis.set_minor_locator(x_minor_locator)
    plt.gca().yaxis.set_major_locator(y_major_locator)
    plt.gca().yaxis.set_minor_locator(y_minor_locator)

    # Add vertical lines for support structure domains
    plt.axvline(x=120, color='grey', linewidth=1.5, linestyle='--')
    
    # Add vertical text annotations
    plt.text(4, plt.ylim()[1] * 0.05, 'Jacket', rotation=90, verticalalignment='bottom')
    plt.text(124, plt.ylim()[1] * 0.05, 'Floating', rotation=90, verticalalignment='bottom')
    
    plt.grid(which='major', linestyle='-', linewidth='0.5', color='gray')
    plt.grid(which='minor', linestyle=':', linewidth='0.5', color='gray')
    plt.minorticks_on()
    
    plt.xlabel('Water Depth (m)')
    plt.ylabel('Cost (M€)')
    
    # Position the legend above the figure
    plt.legend(bbox_to_anchor=(-0.2, 1.25), loc='upper left', ncol=2, frameon=False)
    
    plt.grid(True)
    plt.savefig(f'C:\\Users\\cflde\\Downloads\\ic_eh_equip_cost_vs_water_depth.png', dpi=400, bbox_inches='tight')
    plt.show()

if __name__ == "__main__":
    wd_jacket = 50
    wd_floating = 150

    plot_total_cost_vs_water_depth()

    # Call the function to plot the costs
    plot_inst_deco_cost_vs_port_distance([wd_jacket, wd_floating])
    
    # for wd in (wd_jacket, wd_floating):
    #     plot_total_cost_vs_capacity(wd)
        
    # plot_equip_cost_vs_water_depth()
    
    # plot_ic_cost_vs_water_depth()
    
    # plot_ic_equip_cost_vs_water_depth()