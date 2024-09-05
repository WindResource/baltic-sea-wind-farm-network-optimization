import matplotlib.pyplot as plt

# Define font parameters
font = {'family': 'serif',
        'weight': 'normal',
        'size': 12}

# Set font
plt.rc('font', **font)


def plot_lifecycle_phases():
    # Define fixed parameters
    bar_height = 0.3
    year_width = 1
    spacing = 0.2
    year_segment_width = 1

    # Define the stages and durations
    stages_combined = ['Capital Investment & Project Preparation', 'Procurement & Site Preparation', 
                       'Support Structure & Infrastructure Installation', 'Turbine Installation & Commissioning', 
                       'Operation & Maintenance', 'Decommissioning & Site Restoration']

    durations_combined = [1, 1, 2, 1, 25, 2]  # Updated durations with Year 3-4 combined

    # Total years including Year 0
    years_combined = sum(durations_combined)

    # Colors for each phase
    colors_combined = ['lightgreen'] * durations_combined[0] + ['gold'] * durations_combined[1] + \
                      ['steelblue'] * durations_combined[2] + ['orange'] * durations_combined[3] + \
                      ['lightblue'] * durations_combined[4] + ['grey'] * durations_combined[5]

    # Define CAPEX, OPEX, and DECEX values
    capex_years_final = 1  # CAPEX only in Year 0
    opex_years_final = 25  # OPEX covering Years 5-29
    decex_years_final = 1  # DECEX only in Years 30-31

    # Create a list of x positions for the bars
    x_positions = list(range(years_combined))

    # Creating the figure
    fig, ax = plt.subplots(figsize=(12, 8))

    # Plotting the highlights first
    ax.barh([''], [year_width * capex_years_final], color='green', alpha=0.2, height=bar_height + 0.2, left=0, label='CAPEX')
    ax.barh([''], [year_width * opex_years_final], color='blue', alpha=0.2, height=bar_height + 0.2, left=5, label='OPEX')
    ax.barh([''], [year_width * decex_years_final], color='grey', alpha=0.2, height=bar_height + 0.2, left=30, label='DECEX')

    # Plotting the lifecycle phases (main bars) on top of the highlights
    ax.barh([''] * years_combined, [year_width] * years_combined, color=colors_combined, edgecolor='black', height=bar_height, left=x_positions)

    # Adding the year numbers starting from 0
    ax.set_xticks(x_positions)
    ax.set_xticklabels([f'{i}' for i in range(years_combined)])

    # Set the x-axis label to "Year"
    ax.set_xlabel('Year')

    # Updating the x-axis limit to end at the end of the last bar
    ax.set_xlim(0, years_combined)

    # Updating the legend to fit above the figure using figure coordinates
    legend_elements_no_title = [plt.Line2D([0], [0], color='lightgreen', lw=4, label=stages_combined[0]),
                                plt.Line2D([0], [0], color='gold', lw=4, label=stages_combined[1]),
                                plt.Line2D([0], [0], color='steelblue', lw=4, label=stages_combined[2]),
                                plt.Line2D([0], [0], color='orange', lw=4, label=stages_combined[3]),
                                plt.Line2D([0], [0], color='lightblue', lw=4, label=stages_combined[4]),
                                plt.Line2D([0], [0], color='grey', lw=4, label=stages_combined[5]),
                                plt.Line2D([0], [0], color='green', lw=4, alpha=0.5, label='CAPEX'),
                                plt.Line2D([0], [0], color='blue', lw=4, alpha=0.5, label='OPEX'),
                                plt.Line2D([0], [0], color='grey', lw=4, alpha=0.5, label='DECEX')]

    # Position the legend above the figure without resizing
    ax.legend(handles=legend_elements_no_title, loc='upper center', bbox_to_anchor=(0.5, 2), ncol=3, frameon=False)

    # Remove y-axis labels
    ax.set_yticks([])

    # Display the chart
    plt.tight_layout()
    plt.show()

# Call the function
plot_lifecycle_phases()
