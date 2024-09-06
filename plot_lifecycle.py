import matplotlib.pyplot as plt

# Define font parameters
font = {'family': 'serif',
        'weight': 'normal',
        'size': 12}

# Set font
plt.rc('font', **font)


def plot_lifecycle_phases():
    # Define parameters inside the function
    start_capex = 0
    start_opex = 5
    start_decex = 30

    # Define fixed parameters
    bar_height = 0.2
    year_width = 1

    # Define the stages and durations
    stages_combined = ['Procurement & Site Preparation', 
                       'Support Structure & Infrastructure Installation', 
                       'Turbine Installation & Commissioning', 
                       'Operation & Maintenance', 
                       'Decommissioning & Site Restoration']

    durations_combined = [1, 2, 2, 25, 2]  # Updated durations

    # Total years including Year 0
    years_combined = sum(durations_combined)

    # Colors for each phase
    colors_combined = ['limegreen'] * durations_combined[0] + \
                      ['green'] * durations_combined[1] + \
                      ['darkgreen'] * durations_combined[2] + \
                      ['cornflowerblue'] * durations_combined[3] + \
                      ['salmon'] * durations_combined[4]

    # Define CAPEX, OPEX, and DECEX values
    capex_years_final = 1  # CAPEX only in Year 0
    opex_years_final = 25  # OPEX covering Years 5-29
    decex_years_final = 1  # DECEX covering Years 30-31

    # Create a list of x positions for the bars
    x_positions = list(range(years_combined))

    # Creating the figure
    fig, ax = plt.subplots(figsize=(12, 1.2))

    # Add vertical major gridlines
    #ax.grid(True, which='major', axis='x', linestyle='--', linewidth=0.75, color='grey')

    # Plotting the highlights first
    ax.barh([''], [year_width * capex_years_final], color='green', alpha=0.2, height=bar_height + 0.2, left=start_capex, label='CAPEX')
    ax.barh([''], [year_width * opex_years_final], color='blue', alpha=0.2, height=bar_height + 0.2, left=start_opex, label='OPEX')
    ax.barh([''], [year_width * decex_years_final], color='red', alpha=0.2, height=bar_height + 0.2, left=start_decex, label='DECEX')

    # Plotting the lifecycle phases (main bars) on top of the highlights
    ax.barh([''] * years_combined, [year_width] * years_combined, color=colors_combined, edgecolor='black', height=bar_height, left=x_positions)

    # Adding the year numbers
    ax.set_xticks(range(0, years_combined + 2))  # Ensure Year 32 is included
    ax.set_xticklabels([f'{i}' for i in range(0, years_combined + 2)])

    # Set the x-axis label to "Year"
    ax.set_xlabel('Year')

    # Updating the x-axis limit to end at the end of Year 32
    ax.set_xlim(0, years_combined + 0.01)  # Adding 1 to include Year 32
    
    # # Define the y-axis limits to control height (number of bars shown)
    ax.set_ylim(-0.25, 0.25)  # Adjust these values as needed

    # Define legend elements with borders around symbols
    legend_elements_no_title = [
        plt.Line2D([0], [0], color='limegreen', marker='o', markersize=10, markeredgecolor='black', markeredgewidth=1, lw=0, label=stages_combined[0]),
        plt.Line2D([0], [0], color='green', marker='o', markersize=10, markeredgecolor='black', markeredgewidth=1, lw=0, label=stages_combined[1]),
        plt.Line2D([0], [0], color='darkgreen', marker='o', markersize=10, markeredgecolor='black', markeredgewidth=1, lw=0, label=stages_combined[2]),
        plt.Line2D([0], [0], color='cornflowerblue', marker='o', markersize=10, markeredgecolor='black', markeredgewidth=1, lw=0, label=stages_combined[3]),
        plt.Line2D([0], [0], color='salmon', marker='o', markersize=10, markeredgecolor='black', markeredgewidth=1, lw=0, label=stages_combined[4]),
        plt.Line2D([0], [0], color='green', marker='o', markersize=10, alpha=0.5, markeredgecolor='black', markeredgewidth=1, lw=0, label='Capital Expenses'),
        plt.Line2D([0], [0], color='blue', marker='o', markersize=10, alpha=0.5, markeredgecolor='black', markeredgewidth=1, lw=0, label='Operating Expenses'),
        plt.Line2D([0], [0], color='red', marker='o', markersize=10, alpha=0.5, markeredgecolor='black', markeredgewidth=1, lw=0, label='Decommissioning Expenses')
    ]
    
    # Position the legend above the figure without resizing
    ax.legend(handles=legend_elements_no_title, loc='upper center', bbox_to_anchor=(0.5, 2.5), ncol=2, frameon=False)

    # Remove y-axis labels
    ax.set_yticks([])

    # Display the chart
    plt.savefig(f'C:\\Users\\cflde\\Downloads\\lifecycle.png', dpi=400, bbox_inches='tight')
    plt.show()

# Call the function
plot_lifecycle_phases()
