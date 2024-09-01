import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

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
plot_heatmap()

def plot_grouped_bar_chart():
    # Data for each component in the specified order
    components = ["Onshore substations", "Energy Hubs", "Onshore cables", "Export cables", "Wind farms", "Overall System"]

    # Costs for each configuration (reordered accordingly)
    onshore_substations = [111, 114, 111, 114, 113, 118]
    energy_hubs = [0, 0, 0, 431, 0, 0]
    onshore_cables = [1868, 1228, 1398, 1289, 1017, 982]
    export_cables = [5496, 6200, 6427, 5976, 6190, 5245]
    wind_farms = [21454, 20957, 21049, 21016, 13486, 20898]
    overall_system = [28928, 28499, 28986, 28827, 20806, 27243]

    # Combine data into a single array for easier plotting
    data_reordered = np.array([
        onshore_substations,
        energy_hubs,
        onshore_cables,
        export_cables,
        wind_farms,
        overall_system
    ]).T

    # Labels for the configurations
    labels = [
        "National Combined", "Int. Combined", "Int. Combined, Multi-stage",
        "Int. Hub & Spoke", "Int. Combined, 80% WF Cost", "Int. Combined, 80% Cable Cost"
    ]

    # Number of configurations
    n_configurations = len(labels)

    # Create the bar positions
    bar_width = 0.15
    index = np.arange(n_configurations)

    # Create the plot
    fig, ax = plt.subplots(figsize=(14, 8))

    # Plot bars for each component in the specified order
    for i in range(len(components)):
        ax.bar(index + i * bar_width, data_reordered[:, i], bar_width, label=components[i])

    # Adding labels and title
    ax.set_xlabel('Network Configuration')
    ax.set_ylabel('Cost (M EUR)')
    ax.set_title('Component Costs by Network Configuration (Grouped Bar Chart)')
    ax.set_xticks(index + bar_width * 2.5)
    ax.set_xticklabels(labels)
    ax.legend(title="Components")

    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()




#plot_grouped_bar_chart()