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

    # Define components and their respective data in a dictionary
    data_dict = {
        "Wind farms": [2.37, 0.44, 0.28, -19.56, -0.28],
        "Energy Hubs": [0, 0, 0, 0, 0],
        "Onshore substations": [-2.91, -2.33, -0.19, -1.06, 3.24],
        "Export cables": [-11.36, 3.67, -3.61, -0.16, -15.40],
        "Onshore cables": [52.15, 13.82, 5.01, -17.14, -20.00],
        "Overall System": [1.51, 1.71, 1.15, -15.16, -4.41]
    }
    
    labels = [
        "National Combined", "Int. Combined, Multi-stage", "Int. Hub&Spoke",
        "Int. Combined, 80% WF Cost", "Int. Combined, 80% TC Cost"
    ]

    # Exclude the "Energy Hubs" component
    if "Energy Hubs" in data_dict:
        data_dict.pop("Energy Hubs")
    
    # Convert the dictionary values into a numpy array and get the list of components
    components_filtered = list(data_dict.keys())
    data_filtered = np.array(list(data_dict.values())).T

    # Calculate standard deviation and set normalization range
    std_dev = np.std(data_filtered)
    norm = plt.Normalize(vmin=-num_std_dev * std_dev, vmax=num_std_dev * std_dev)
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(7, 5))
    cmap = sns.diverging_palette(240, 10, as_cmap=True, center="light")
    
    # Plot heatmap
    heatmap = sns.heatmap(data_filtered.T, annot=True, cmap=cmap, fmt=".2f", xticklabels=labels, yticklabels=components_filtered, 
                        ax=ax, norm=norm, cbar_kws={"shrink": 1, "aspect": 10}, annot_kws={"size": 14})
    
    # Adjust axis labels and tick labels
    ax.xaxis.set_label_position('top')
    ax.xaxis.tick_top()
    plt.xticks(rotation=45, ha='left')
    
    # Format annotations
    for text in ax.texts:
        text.set_text(f"${text.get_text()}$")
    
    # Customize color bar
    cbar = heatmap.collections[0].colorbar
    cbar.set_label('(%)', rotation=0, ha='left', va='center', labelpad=10)
    cbar.ax.yaxis.label.set_size(14)
    cbar.ax.yaxis.label.set_fontweight('normal')
    cbar.ax.tick_params(labelsize=14)
    
    # Highlight "Overall System" if present
    if "Overall System" in components_filtered:
        overall_system_index = components_filtered.index("Overall System")
        ax.yaxis.get_ticklabels()[overall_system_index].set_fontweight('bold')

    plt.savefig('C:\\Users\\cflde\\Downloads\\heatmap.png', dpi=400, bbox_inches='tight')
    plt.show()
    

# Call the function
plot_heatmap()

def plot_grouped_bar_chart():
    # Define components and data in a dictionary for better management
    data_dict = {
        "Overall System": [28928, 28499, 28986, 28827, 20806, 27243],
        "Wind farms": [21454, 20957, 21049, 21016, 13486, 20898],
        "Energy Hubs": [0, 0, 0, 431, 0, 0],
        "Onshore substations": [111, 114, 111, 114, 113, 118],
        "Export cables": [5496, 6200, 6427, 5976, 6190, 5245],
        "Onshore cables": [1868, 1228, 1398, 1289, 1017, 982]
    }
    
    components = list(data_dict.keys())
    data = np.array(list(data_dict.values())).T  # Transpose to match the configurations
    data_billion = data / 1000  # Convert to billions
    
    # Labels for the configurations
    labels = [
        "National Combined", "Int. Combined", "Int. Combined, Multi-stage",
        "Int. Hub&Spoke", "Int. Combined, 80% WF Cost", "Int. Combined, 80% TC Cost"
    ]
    
    n_configurations = len(labels)
    bar_width = 0.15
    group_width = len(components) * bar_width + 0.2
    index = np.arange(n_configurations) * group_width * 1.2
    
    # Select a Seaborn color palette
    sns_palette = sns.color_palette("muted", len(components))
    
    fig, ax = plt.subplots(figsize=(8, 5))
    
    # Plot bars for each component with colors from Seaborn palette
    handles = []
    for i, (component, color) in enumerate(zip(components, sns_palette)):
        bars = ax.bar(index + i * bar_width, data_billion[:, i], bar_width, label=component, color=color)
        handles.append(bars[0])
    
    # Set labels, title, and limits
    ax.set_ylabel('Cost (B\u20AC)')
    ax.set_xticks(index + bar_width * (len(components) / 2))
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.set_xlim(-0.5, index[-1] + len(components) * bar_width + 0.5)
    ax.set_ylim(0, np.max(data_billion) + 2)
    
    # Set grid lines
    ax.yaxis.set_major_locator(MultipleLocator(5))
    ax.yaxis.set_minor_locator(MultipleLocator(1))
    ax.grid(which='major', axis='y', linestyle='--', linewidth='0.5', color='gray')
    ax.grid(which='minor', axis='y', linestyle=':', linewidth='0.5', color='gray')
    ax.set_axisbelow(True)
    
    # Add legend
    fig.legend(handles, components, bbox_to_anchor=(0.38, 1.05), loc='center', ncol=2, frameon=False)
    
    plt.tight_layout()
    plt.savefig('C:\\Users\\cflde\\Downloads\\grouped_bars.png', dpi=400, bbox_inches='tight')
    plt.show()

plot_grouped_bar_chart()

