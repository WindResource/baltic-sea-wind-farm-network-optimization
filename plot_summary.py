import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import AutoMinorLocator
from matplotlib.ticker import MultipleLocator

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

    data = np.array([
        [2.37, 0, -2.91, -11.36, 52.15, 1.51],
        [0.44, 0, -2.33, 3.67, 13.82, 1.71],
        [0.28, 0, -0.19, -3.61, 5.01, 1.15],
        [-19.56, 0, -1.06, -0.16, -17.14, -15.16],
        [-0.28, 0, 3.24, -15.40, -20.00, -4.41]
    ])

    components = ["Wind farms", "Energy Hubs", "Onshore substations", "Export cables", "Onshore cables", "Overall System"]
    labels = [
        "National Combined", "Int. Combined, Multi-stage", "Int. Hub&Spoke",
        "Int. Combined, 80% WF Cost", "Int. Combined, 80% TC Cost"
    ]
    
    # Exclude the "Energy Hubs" component
    exclude_index = components.index("Energy Hubs") if "Energy Hubs" in components else None
    if exclude_index is not None:
        data_filtered = np.delete(data, exclude_index, axis=1)
        components_filtered = [comp for i, comp in enumerate(components) if i != exclude_index]
    else:
        data_filtered = data
        components_filtered = components

    # Calculate the standard deviation of the data
    std_dev = np.std(data_filtered)
    
    # Set the normalization range for the color map based on standard deviation
    norm = plt.Normalize(vmin=-num_std_dev*std_dev, vmax=num_std_dev*std_dev)
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(7, 5))  # Adjusted figure size for better colorbar width
    
    # Create a diverging color map with red for positive and blue for negative values
    cmap = sns.diverging_palette(240, 10, as_cmap=True, center="light")
    
    # Plot the heatmap with annotation font size set via annot_kws
    heatmap = sns.heatmap(data_filtered.T, annot=True, cmap=cmap, fmt=".2f", xticklabels=labels, yticklabels=components_filtered, 
                        ax=ax, norm=norm, cbar_kws={"shrink": 1, "aspect": 10},
                        annot_kws={"size": 14})  # Adjust the font size for heatmap values here

    # Adjust the position of the x-axis labels
    ax.xaxis.set_label_position('top')
    ax.xaxis.tick_top()
    plt.xticks(rotation=45, ha='left')

    # Format the annotations in math format
    for text in ax.texts:
        text.set_text(f"${text.get_text()}$")  # Wrap the text in math format

    # Add the unit (%) to the color bar
    cbar = heatmap.collections[0].colorbar
    cbar.set_label('(%)', rotation=0, ha='left', va='center', labelpad=10)
    
    # Customize the font properties of the color bar label
    cbar.ax.yaxis.label.set_size(14)  # Adjust label size
    cbar.ax.yaxis.label.set_fontweight('normal')  # Make the label not bold (or adjust as needed)

    # Set the font size for color bar tick labels
    cbar.ax.tick_params(labelsize=14)  # Set the font size for the color bar tick labels

    # Make "Overall System" bold
    if "Overall System" in components_filtered:
        overall_system_index = components_filtered.index("Overall System")
        ax.yaxis.get_ticklabels()[overall_system_index].set_fontweight('bold')

    plt.savefig(f'C:\\Users\\cflde\\Downloads\\heatmap.png', dpi=400, bbox_inches='tight')
    plt.show()

# Call the function
# plot_heatmap()

def plot_grouped_bar_chart():
    # New order for the legend and data arrays directly ordered
    components = ["Overall System", "Wind farms", "Energy Hubs", "Onshore substations", "Export cables", "Onshore cables"]
    overall_system = [28928, 28499, 28986, 28827, 20806, 27243]
    wind_farms = [21454, 20957, 21049, 21016, 13486, 20898]
    energy_hubs = [0, 0, 0, 431, 0, 0]
    onshore_substations = [111, 114, 111, 114, 113, 118]
    export_cables = [5496, 6200, 6427, 5976, 6190, 5245]
    onshore_cables = [1868, 1228, 1398, 1289, 1017, 982]

    # Data directly ordered as per the new legend order
    data_ordered = np.array([
        overall_system,
        wind_farms,
        energy_hubs,
        onshore_substations,
        export_cables,
        onshore_cables
    ]).T
    data_ordered_billion = data_ordered / 1000

    # Labels for the configurations
    labels = [
        "National Combined", "Int. Combined", "Int. Combined, Multi-stage",
        "Int. Hub&Spoke", "Int. Combined, 80% WF Cost", "Int. Combined, 80% TC Cost"
    ]

    # Number of configurations
    n_configurations = len(labels)

    # Create the bar positions
    bar_width = 0.15
    group_width = len(components) * bar_width + 0.2  # Width of one group plus spacing
    index = np.arange(n_configurations) * group_width * 1.2  # Increase gap between groups

    # Specify colors using 'C0', 'C1', 'C2', etc.
    colors = ['C0', 'C1', 'C2', 'C3', 'C4', 'C6']

    # Create the plot
    fig, ax = plt.subplots(figsize=(8, 5))

    # Plot bars for each component in the specified order with colors
    handles = []
    for i, component in enumerate(components):
        bars = ax.bar(index + i * bar_width, data_ordered_billion[:, i], bar_width, label=component, color=colors[i])
        handles.append(bars[0])  # Store the handle for the legend

    # Adding labels and title
    ax.set_ylabel('Cost (B\u20AC)', fontsize=12)
    ax.set_xticks(index + bar_width * (len(components) / 2))
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=10)
    
    # Set x and y limits with additional space on the left
    ax.set_xlim(-0.5, index[-1] + len(components) * bar_width + 0.5)  # Adjust space on the x-axis
    ax.set_ylim(0, np.max(data_ordered_billion) + 2)  # Add a bit of padding

    # Set major and minor gridlines
    ax.yaxis.set_major_locator(MultipleLocator(5))  # Adjust as needed
    ax.yaxis.set_minor_locator(MultipleLocator(1))  # Adjust as needed

    # Add grid lines for better readability
    ax.grid(which='major', axis='y', linestyle='--', linewidth='0.5', color='gray')
    ax.grid(which='minor', axis='y', linestyle=':', linewidth='0.5', color='gray')
    ax.set_axisbelow(True)

    # Add legend using the specified format and order
    fig.legend(handles, components, bbox_to_anchor=(0.4, 1.05), loc='center', ncol=2, frameon=False, fontsize=10)

    plt.tight_layout()
    plt.show()

plot_grouped_bar_chart()

