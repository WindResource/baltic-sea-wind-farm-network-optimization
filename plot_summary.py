import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import AutoMinorLocator
from matplotlib.ticker import MultipleLocator
from matplotlib import gridspec
from mpl_toolkits.axes_grid1 import make_axes_locatable

# Define font parameters
font = {'family': 'serif',
        'weight': 'normal',
        'size': 12}

# Set font
plt.rc('font', **font)

def plot_heatmap():
    """
    Plots an adjusted heatmap where positive values are in red and negative values are in blue.
    The "Energy Hubs" component is excluded from the heatmap.
    """
    num_std_dev = 2

    # Define components and their respective data in a dictionary (excluding Energy Hubs)
    data_dict = {
        "Wind farms": [2.37, 0.44, 0.28, -19.56, -0.28, 0.74],
        "Onshore substations": [-2.91, -2.33, -0.19, -1.06, 3.24, -3.08],
        "Export cables": [-11.36, 3.67, -3.61, -0.16, -15.40, -7.21],
        "Onshore cables": [52.15, 13.82, 5.01, -17.14, -20.00, 0.00],
        "Overall System": [1.51, 1.71, 1.15, -15.16, -4.41, -1.04]
    }
    
    labels = [
        "National Combined", "Int. Combined, Multi-stage", "Int. Hub&Spoke",
        "Int. Combined, 20% Red. WF Cost", "Int. Combined, 20% Red. TC Cost",
        "Int. Combined, 60% Red. IC Cost"
    ]

    # Convert the dictionary values into a numpy array and get the list of components
    components_filtered = list(data_dict.keys())
    data_filtered = np.array(list(data_dict.values())).T

    # Calculate standard deviation and set normalization range
    std_dev = np.std(data_filtered)
    norm = plt.Normalize(vmin=-num_std_dev * std_dev, vmax=num_std_dev * std_dev)
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(8, 6))
    cmap = sns.diverging_palette(240, 10, as_cmap=True, center="light")
    
    # Plot heatmap
    heatmap = sns.heatmap(data_filtered.T, annot=True, cmap=cmap, fmt=".2f", xticklabels=labels, yticklabels=components_filtered, 
                        ax=ax, norm=norm, cbar=False, annot_kws={"size": 14})
    
    # Adjust axis labels and tick labels
    ax.xaxis.set_label_position('top')
    ax.xaxis.tick_top()
    plt.xticks(rotation=45, ha='left')
    
    # Format annotations
    for text in ax.texts:
        text.set_text(f"${text.get_text()}$")
    
    # Calculate cell width based on the figure and heatmap dimensions
    num_cols = len(labels)
    heatmap_width = ax.get_position().width * fig.get_size_inches()[0]  # Width in inches
    cell_width = heatmap_width / num_cols  # Width of one cell
    
    # Set the size and padding based on the calculated cell width
    colorbar_size = cell_width / 3  # Color bar size as 1/3 of cell width
    colorbar_pad = cell_width / 3  # Padding as 1/3 of cell width
    
    # Create a color bar with a height matching the heatmap y-axis height
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size=colorbar_size, pad=colorbar_pad)  # Use float values

    cbar = fig.colorbar(heatmap.collections[0], cax=cax)
    cbar.set_label('(%)', rotation=0, ha='left', va='center', labelpad=10)
    cbar.ax.yaxis.label.set_size(14)
    cbar.ax.yaxis.label.set_fontweight('normal')
    cbar.ax.tick_params(labelsize=14)
    
    # Remove the black border around the color bar
    cbar.outline.set_visible(False)
    
    # Highlight "Overall System" if present
    if "Overall System" in components_filtered:
        overall_system_index = components_filtered.index("Overall System")
        ax.yaxis.get_ticklabels()[overall_system_index].set_fontweight('bold')

    # Set aspect ratio to ensure cells are square
    ax.set_aspect('equal', 'box')

    plt.savefig('C:\\Users\\cflde\\Downloads\\heatmap.png', dpi=400, bbox_inches='tight')
    plt.show()

# Call the updated function
plot_heatmap()

def plot_grouped_bar_chart():
    include_configs = ["National Combined", "Int. Combined", "Int. Combined,\nMulti-stage", "Int. Hub&Spoke"]

    # Define components and data in a dictionary for better management
    data_dict = {
        "Overall System": [28928, 28499, 28986, 28827, 20806, 27243],
        "Wind farms": [21454, 20957, 21049, 21016, 13486, 20898],
        "Energy Hubs": [0, 0, 0, 431, 0, 0],
        "Onshore substations": [110.7, 114.0, 111.4, 113.8, 112.8, 117.7],
        "Export cables": [5496, 6200, 6427, 5976, 6190, 5245],
        "Onshore cables": [1868, 1228, 1398, 1289, 1017, 982]
    }
    
    # Labels for the configurations
    labels = [
        "National Combined", "Int. Combined", "Int. Combined,\nMulti-stage",
        "Int. Hub&Spoke", "Int. Combined, 20% Red. WF Cost", "Int. Combined, 20% Red. TC Cost"
    ]
    
    # Filter configurations if needed
    if include_configs is not None:
        include_indices = [labels.index(config) for config in include_configs if config in labels]
        labels = [labels[i] for i in include_indices]
        for key in data_dict:
            data_dict[key] = [data_dict[key][i] for i in include_indices]
    
    components = list(data_dict.keys())
    data = np.array(list(data_dict.values())).T  # Transpose to match the configurations
    data_billion = data / 1000  # Convert to billions
    
    n_configurations = len(labels)
    bar_width = 1.0  # Increase bar width
    group_width = len(components) * bar_width + 0.5  # Increase the group width for spacing
    index = np.arange(n_configurations) * group_width
    
    # Define specific colors for each component with saturated colors
    color_mapping = {
        "Wind farms": "forestgreen",       # Deep and rich green
        "Energy Hubs": "deepskyblue",      # Bright and vibrant blue
        "Onshore substations": "goldenrod",     # Bold and saturated yellow
        "Export cables": "limegreen",      # Bright and vibrant green
        "Onshore cables": "mediumseagreen", # Balanced and rich green
        "Overall System": "royalblue"      # Deep and saturated blue
    }

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 4.5), gridspec_kw={'height_ratios': [3, 1]})
    
    # Plot bars for each component with specific colors
    handles = []
    for i, component in enumerate(components):
        bars = ax1.bar(index + i * bar_width, data_billion[:, i], bar_width, label=component, color=color_mapping[component])
        
        # Highlight min and max values with cross markers
        min_val = np.min(data_billion[:, i])
        max_val = np.max(data_billion[:, i])
        
        for bar in bars:
            height = bar.get_height()
            # Add text within the bar just below the top (excluding specific components)
            if component not in ["Energy Hubs", "Onshore substations"]:
                ax1.text(bar.get_x() + bar.get_width() / 2, height - 0.25, f'{height:.1f}', ha='center', va='top', fontsize=8, fontweight='bold', color='white')
            if height == min_val and component != "Energy Hubs":
                ax1.plot(bar.get_x() + bar.get_width() / 2, height, 'gx', markersize=10, markeredgewidth=2)
            if height == max_val:
                ax1.plot(bar.get_x() + bar.get_width() / 2, height, 'rx', markersize=10, markeredgewidth=2)
        
        handles.append(bars[0])
    
    # Plot zoomed in panel for Energy Hubs and Onshore Substations
    zoom_components = ["Energy Hubs", "Onshore substations"]
    zoom_indices = [components.index(comp) for comp in zoom_components]
    
    for i in zoom_indices:
        bars = ax2.bar(index + i * bar_width, data_billion[:, i], bar_width, label=components[i], color=color_mapping[components[i]])
        
        # Highlight min and max values with cross markers
        min_val = np.min(data_billion[:, i])
        max_val = np.max(data_billion[:, i])
        
        for bar in bars:
            height = bar.get_height()
            if height > 0:  # Display value only if positive
                ax2.text(bar.get_x() + bar.get_width() / 2, height - 0.025, f'{height:.2f}', ha='center', va='top', fontsize=8, fontweight='bold', color='white')
            if height == min_val and components[i] != "Energy Hubs":
                ax2.plot(bar.get_x() + bar.get_width() / 2, height, 'gx', markersize=10, markeredgewidth=2)
            if height == max_val:
                ax2.plot(bar.get_x() + bar.get_width() / 2, height, 'rx', markersize=10, markeredgewidth=2)

    # Set labels, title, and limits for the main plot
    ax1.set_ylabel('Cost (B\u20AC)')
    ax1.set_xticks(index + bar_width * (len(components) / 2))
    ax1.set_xticklabels(labels, rotation=45, ha='right')
    ax1.set_xlim(-0.5, index[-1] + bar_width * len(components) - 0.5)
    ax1.set_ylim(0, np.max(data_billion) + 2)
    # Set grid lines for the main plot
    ax1.yaxis.set_major_locator(MultipleLocator(5))
    ax1.yaxis.set_minor_locator(MultipleLocator(1))
    ax1.grid(which='major', axis='y', linestyle='--', linewidth='0.5', color='gray')
    ax1.grid(which='minor', axis='y', linestyle=':', linewidth='0.5', color='gray')
    ax1.set_axisbelow(True)

    # Set labels, title, and limits for the zoomed plot
    ax2.set_ylabel('Cost (B\u20AC)')
    ax2.set_xticks(index + bar_width * (len(components) / 2))
    ax2.set_xticklabels(labels, rotation=0, ha='center')
    ax2.set_xlim(-0.5, index[-1] + bar_width * len(components) - 0.5)
    ax2.set_ylim(0, np.max(data_billion[:, zoom_indices]) + 0.1)
    # Set grid lines for the zoomed plot
    ax2.yaxis.set_major_locator(MultipleLocator(0.5/2))
    ax2.yaxis.set_minor_locator(MultipleLocator(0.5/2/4))
    ax2.grid(which='major', axis='y', linestyle='--', linewidth='0.5', color='gray')
    ax2.grid(which='minor', axis='y', linestyle=':', linewidth='0.5', color='gray')
    ax2.set_axisbelow(True)
    
    # Remove the x-axis labels from the top panel
    ax1.set_xticklabels([])

    # Create custom legends for the crosses
    min_cross = plt.Line2D([0], [0], color='g', marker='x', linestyle='None', markersize=10, markeredgewidth=2, label='Min Value')
    max_cross = plt.Line2D([0], [0], color='r', marker='x', linestyle='None', markersize=10, markeredgewidth=2, label='Max Value')
    
    # Add legend to the main plot
    handles.extend([min_cross, max_cross])
    fig.legend(handles, components + ['Minimum Value', 'Maximum Value'], bbox_to_anchor=(0.45, 1.06), loc='center', ncol=3, frameon=False)
    
    plt.tight_layout()
    plt.savefig('C:\\Users\\cflde\\Downloads\\grouped_bar_chart.png', dpi=400, bbox_inches='tight')
    plt.show()

# Example usage:
# plot_grouped_bar_chart()




