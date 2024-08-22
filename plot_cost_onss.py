import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from scripts.present_value import present_value
import matplotlib.lines as mlines
from matplotlib.legend_handler import HandlerBase

# Define font parameters
font = {'family': 'serif',
        'weight': 'normal',
        'size': 12}

# Set font
plt.rc('font', **font)

def onss_cost(capacity, threshold):
    """
    Calculate the cost for ONSS expansion above a certain capacity.

    Parameters:
    - capacity (float): The total capacity in MW for which the cost is to be calculated.
    - threshold (float): The capacity threshold in MW specific to the ONSS above which cost are incurred.
    
    Returns:
    - (float) Cost of expanding the ONSS if the capacity exceeds the threshold.
    """
    global inst_year
    inst_year = 2040
    
    threshold_equip_cost = 0.02287 # Million EU/ MW
    
    # Calculate the cost function: difference between capacity and threshold multiplied by the cost factor
    equip_cost = np.maximum(capacity - threshold, 0) * threshold_equip_cost
    
    ope_cost_yearly = 0.015 * equip_cost
    
    # Calculate present value
    total_cost, equip_cost, _, total_ope_cost, _ = present_value(inst_year, equip_cost, 0, ope_cost_yearly, 0)
    
    return total_cost, equip_cost, total_ope_cost

def onss_cost_lin(capacity, threshold):
    """
    Calculate the cost for ONSS expansion above a certain capacity.

    Parameters:
    - capacity (float): The total capacity in MW for which the cost is to be calculated.
    - threshold (float): The capacity threshold in MW specific to the ONSS above which cost are incurred.
    
    Returns:
    - (float) Cost of expanding the ONSS if the capacity exceeds the threshold.
    """
    
    threshold_equip_cost = 0.02287 # Million EU/ MW
    
    # Calculate the cost function: difference between capacity and threshold multiplied by the cost factor
    equip_cost = (capacity - threshold) * threshold_equip_cost
    
    ope_cost_yearly = 0.015 * equip_cost
    
    # Calculate present value
    total_cost, equip_cost, _, total_ope_cost, _ = present_value(inst_year, equip_cost, 0, ope_cost_yearly, 0)
    
    return total_cost, equip_cost, total_ope_cost

# Custom legend handler to display solid and dashed lines stacked vertically
class HandlerStackedLines(HandlerBase):
    def create_artists(self, legend, orig_handle, xdescent, ydescent, width, height, fontsize, trans):
        # Set the gap between the two lines
        vertical_gap = height * 0.5

        # Draw solid line at the top
        solid_line = mlines.Line2D([xdescent, xdescent + width], [ydescent + height / 2 + vertical_gap, ydescent + height / 2 + vertical_gap],
                                   color=orig_handle.get_color(), linestyle='-', lw=2, transform=trans)

        # Draw dashed line below the solid line
        dashed_line = mlines.Line2D([xdescent, xdescent + width], [ydescent + height / 2 - vertical_gap, ydescent + height / 2 - vertical_gap],
                                    color=orig_handle.get_color(), linestyle='--', lw=2, transform=trans)

        return [solid_line, dashed_line]

def plot_onss_costs():
    threshold = 0
    capacities = np.linspace(-200, 501, 400)

    total_costs = []
    equip_costs = []
    total_ope_costs = []

    total_costs_lin = []
    equip_costs_lin = []
    total_ope_costs_lin = []

    for cap in capacities:
        total_cost, equip_cost, total_ope_cost = onss_cost(cap, threshold)
        total_costs.append(total_cost)
        equip_costs.append(equip_cost)
        total_ope_costs.append(total_ope_cost)

        total_cost_lin, equip_cost_lin, total_ope_cost_lin = onss_cost_lin(cap, threshold)
        total_costs_lin.append(total_cost_lin)
        equip_costs_lin.append(equip_cost_lin)
        total_ope_costs_lin.append(total_ope_cost_lin)

    plt.figure(figsize=(6, 5))

    # Plot solid lines
    line1, = plt.plot(capacities, total_costs, label='Total PV', color='C0')
    line2, = plt.plot(capacities, equip_costs, label='Equipment PV', color='C1')
    line3, = plt.plot(capacities, total_ope_costs, label='Total Operating PV', color='C2')

    # Plot dashed lines
    plt.plot(capacities, total_costs_lin, color=line1.get_color(), linestyle='--')
    plt.plot(capacities, equip_costs_lin, color=line2.get_color(), linestyle='--')
    plt.plot(capacities, total_ope_costs_lin, color=line3.get_color(), linestyle='--')

    plt.xlabel('Capacity (MW)')
    plt.ylabel('Cost (M\u20AC)')
    
    # Set domain and range
    plt.xlim(-200, 500)
    plt.ylim(-5, 10)
    
    # Define major and minor locators
    x_major_locator = MultipleLocator(200)
    x_minor_locator = MultipleLocator(50)
    y_major_locator = MultipleLocator(5)
    y_minor_locator = MultipleLocator(5 / 4)
    
    ax = plt.gca()
    ax.xaxis.set_major_locator(x_major_locator)
    ax.xaxis.set_minor_locator(x_minor_locator)
    ax.yaxis.set_major_locator(y_major_locator)
    ax.yaxis.set_minor_locator(y_minor_locator)
    
    plt.grid(which='both', linestyle='--', linewidth=0.5)
    
    # Set x-ticks dynamically over the range of capacities
    x_ticks = np.arange(-200, 501, 100)
    # Define the LaTeX string for P_th without embedding $
    P_th = r'P_{th}'

    # Create the tick labels using the defined P_th and correct LaTeX minus sign
    x_tick_labels = [
        f'${{{P_th}}} - {abs(tick)}$' if tick < 0 else
        (f'${{{P_th}}}$' if tick == 0 else f'${{{P_th}}} + {tick}$')
        for tick in x_ticks
    ]
    
    plt.xticks(x_ticks, x_tick_labels, fontsize=11, rotation=45, rotation_mode='anchor', ha='right')
    
    plt.minorticks_on()
    plt.grid(which='major', linestyle='-', linewidth='0.5', color='gray')
    plt.grid(which='minor', linestyle=':', linewidth='0.5', color='gray')

    # Custom legend lines
    custom_lines = [
        mlines.Line2D([], [], color='C0', lw=2),
        mlines.Line2D([], [], color='C1', lw=2),
        mlines.Line2D([], [], color='C2', lw=2)
    ]

    labels = ['Total Cost', 'Equipment Cost', 'Operating Cost']

    # Use custom handler for stacked lines
    plt.legend(
        custom_lines,
        labels,
        handler_map={mlines.Line2D: HandlerStackedLines()},
        bbox_to_anchor=(0, 1.20), loc='upper left', ncol=2, frameon=False
    )

    plt.savefig(f'C:\\Users\\cflde\\Downloads\\onss_cost_vs_capacity.png', dpi=400, bbox_inches='tight')
    plt.show()

if __name__ == "__main__":
    # Example usage:
    plot_onss_costs()
