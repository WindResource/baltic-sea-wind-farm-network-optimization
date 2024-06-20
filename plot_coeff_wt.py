import numpy as np
import matplotlib.pyplot as plt

# Data from the table
years = np.array([2020, 2030, 2050])

# Monopile data
monopile_c1 = np.array([201, 181, 171])
monopile_c2 = np.array([613, 552, 521])
monopile_c3 = np.array([812, 370, 170])

# Jacket data
jacket_c1 = np.array([114, 103, 97])
jacket_c2 = np.array([-2270, -2043, -1930])
jacket_c3 = np.array([932, 478, 272])

# Floating data
floating_c1 = np.array([0, 0, 0])
floating_c2 = np.array([774, 697, 658])
floating_c3 = np.array([1481, 1223, 844])

# Function to perform linear fit and plot data
def fit_and_plot_combined_linear(years, c1, c2, c3, foundation_type):
    # Fit linear polynomials to the data
    p1 = np.polyfit(years, c1, 1)
    p2 = np.polyfit(years, c2, 1)
    p3 = np.polyfit(years, c3, 1)
    
    # Generate years for smooth plotting
    fit_years = np.linspace(2020, 2050, 100)
    fit_c1 = np.polyval(p1, fit_years)
    fit_c2 = np.polyval(p2, fit_years)
    fit_c3 = np.polyval(p3, fit_years)
    
    # Estimate the values for 2040
    c1_2040 = np.polyval(p1, 2040)
    c2_2040 = np.polyval(p2, 2040)
    c3_2040 = np.polyval(p3, 2040)
    
    # Plot original data and the fits
    plt.figure(figsize=(10, 6))
    plt.plot(years, c1, 'o', label='Original c1', markersize=8)
    plt.plot(fit_years, fit_c1, '-', label='Linear fit for c1')
    plt.plot(2040, c1_2040, 'rx', label='Estimated c1 in 2040', markersize=12)
    
    plt.plot(years, c2, 'o', label='Original c2', markersize=8)
    plt.plot(fit_years, fit_c2, '-', label='Linear fit for c2')
    plt.plot(2040, c2_2040, 'rx', label='Estimated c2 in 2040', markersize=12)
    
    plt.plot(years, c3, 'o', label='Original c3', markersize=8)
    plt.plot(fit_years, fit_c3, '-', label='Linear fit for c3')
    plt.plot(2040, c3_2040, 'rx', label='Estimated c3 in 2040', markersize=12)
    
    plt.xlabel('Year')
    plt.ylabel('Coefficient value')
    plt.title(f'Evolution of coefficients for {foundation_type} foundation')
    plt.legend()
    plt.grid(True)
    plt.show()
    
    return c1_2040, c2_2040, c3_2040

# Monopile combined plot and estimates for 2040
monopile_c1_2040, monopile_c2_2040, monopile_c3_2040 = fit_and_plot_combined_linear(years, monopile_c1, monopile_c2, monopile_c3, 'Monopile')

# Jacket combined plot and estimates for 2040
jacket_c1_2040, jacket_c2_2040, jacket_c3_2040 = fit_and_plot_combined_linear(years, jacket_c1, jacket_c2, jacket_c3, 'Jacket')

# Floating combined plot and estimates for 2040
floating_c1_2040, floating_c2_2040, floating_c3_2040 = fit_and_plot_combined_linear(years, floating_c1, floating_c2, floating_c3, 'Floating')

# Print estimated values for 2040
print("Estimated coefficients for 2040:")
print(f"Monopile c1: {monopile_c1_2040:.2f}, c2: {monopile_c2_2040:.2f}, c3: {monopile_c3_2040:.2f}")
print(f"Jacket c1: {jacket_c1_2040:.2f}, c2: {jacket_c2_2040:.2f}, c3: {jacket_c3_2040:.2f}")
print(f"Floating c1: {floating_c1_2040:.2f}, c2: {floating_c2_2040:.2f}, c3: {floating_c3_2040:.2f}")