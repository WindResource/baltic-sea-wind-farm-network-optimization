import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

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
    
    overcap_cost = 0.02287 # Million EU/ MW
    
    # Calculate the cost function: difference between capacity and threshold multiplied by the cost factor
    cost_function = np.maximum(capacity - threshold, 0) * overcap_cost
    
    return cost_function

def onss_cost_lin(capacity, threshold):
    """
    Calculate the cost for ONSS expansion above a certain capacity.

    Parameters:
    - capacity (float): The total capacity in MW for which the cost is to be calculated.
    - threshold (float): The capacity threshold in MW specific to the ONSS above which cost are incurred.
    
    Returns:
    - (float) Cost of expanding the ONSS if the capacity exceeds the threshold.
    """
    
    overcap_cost = 0.02287 # Million EU/ MW
    
    # Calculate the cost function: difference between capacity and threshold multiplied by the cost factor
    cost_function = (capacity - threshold) * overcap_cost
    
    return cost_function

def plot_onss_costs():
    """
    Plot the ONSS cost functions as a function of capacity.
    """
    
    threshold = 0
    capacities = np.linspace(-250, 500, 400)
    costs = [onss_cost(cap, threshold) for cap in capacities]
    costs_lin = [onss_cost_lin(cap, threshold) for cap in capacities]

    plt.figure(figsize=(7, 5))
    
    plt.plot(capacities, costs, label='ONSS Cost (Max Function)')
    plt.plot(capacities, costs_lin, label='ONSS Cost (Linear Function)', linestyle='--')
    
    plt.xlabel('Capacity (MW)')
    plt.ylabel('Cost (Million EU)')
    
    # Set domain and range
    plt.xlim(-250, 500)
    plt.ylim(-7.5, 15)
    
    # Set x-ticks dynamically over the range of capacities
    x_ticks = np.arange(-250, 501, 100)
    x_tick_labels = [f'$\\mathit{{TH}}-{abs(tick)}$' if tick < 0 else ('$\\mathit{TH}$' if tick == 0 else f'$\\mathit{{TH}}+{tick}$') for tick in x_ticks]
    plt.xticks(x_ticks, x_tick_labels)
    
    # Define major and minor locators
    x_major_locator = MultipleLocator(200)
    x_minor_locator = MultipleLocator(50)
    y_major_locator = MultipleLocator(5)
    y_minor_locator = MultipleLocator(1.25)
    
    ax = plt.gca()
    ax.xaxis.set_major_locator(x_major_locator)
    ax.xaxis.set_minor_locator(x_minor_locator)
    ax.yaxis.set_major_locator(y_major_locator)
    ax.yaxis.set_minor_locator(y_minor_locator)
    
    plt.grid(which='both', linestyle='--', linewidth=0.5)
    plt.minorticks_on()
    plt.legend(bbox_to_anchor=(0, 1.2), loc='upper left', ncol=2, frameon=False)
    
    plt.grid(True)
    
    plt.show()

# Example usage:
plot_onss_costs()
