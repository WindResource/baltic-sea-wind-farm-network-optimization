import numpy as np
from scipy.interpolate import interp1d
from scipy.stats import weibull_min

def calculate_aep_and_capacity_factor():
    """
    Calculate the Annual Energy Production (AEP) and Capacity Factor of a wind turbine.

    Returns:
        tuple: A tuple containing the AEP (in kWh) and the Capacity Factor (as a percentage).
    """
    # Weibull parameters and turbine rating
    weibullA = 10.65  # Weibull scale parameter (m/s)
    weibullK = 2.32  # Weibull shape parameter
    turbine_rating = 8 * 1e3  # Turbine rating (kW)

    # Power curve of the wind turbine
    power_curve_data = {
        1: 0, 2: 0, 3: 0, 4: 359, 4.5: 561, 5: 812, 5.5: 1118, 6: 1483, 6.5: 1911, 7: 2407,
        7.5: 2974, 8: 3616, 8.5: 4336, 9: 5135, 9.5: 6015, 10: 6976, 10.5: 7518, 11: 7813,
        12: 8000, 13: 8000, 14: 8000, 15: 8000, 16: 8000, 17: 8000, 18: 8000, 19: 8000,
        20: 8000, 21: 8000, 22: 8000, 23: 8000, 24: 8000, 25: 8000
    }

    # Create interpolation function for power curve
    wind_speeds = np.array(list(power_curve_data.keys()))
    power_values = np.array(list(power_curve_data.values()))  # Power values are already in kW
    power_curve_func = interp1d(wind_speeds, power_values, kind='linear', fill_value='extrapolate')

    # Define the Weibull distribution
    weibull_dist = weibull_min(weibullK, scale=weibullA)

    # Define wind speed range
    speed_min = wind_speeds.min()
    speed_max = wind_speeds.max()

    # Create wind speed array for integration
    wind_speed_array = np.linspace(speed_min, speed_max, num=1000)

    # Calculate probability density function (PDF) of Weibull distribution at each wind speed
    pdf_array = weibull_dist.pdf(wind_speed_array)

    # Calculate power output at each wind speed using the power curve function
    power_output_array = power_curve_func(wind_speed_array)

    # Calculate AEP by integrating the product of power output and Weibull PDF over the wind speed range
    aep = np.trapz(power_output_array * pdf_array, wind_speed_array)

    # Number of hours in a year (assuming non-leap year)
    hours_per_year = 365 * 24

    # Calculate capacity factor
    capacity_factor = (aep / (turbine_rating * hours_per_year)) * 100  # Convert to percentage

    return aep, capacity_factor

# Calculate AEP and capacity factor
aep, capacity_factor = calculate_aep_and_capacity_factor()

print("Annual Energy Production (AEP): {:.2f} kWh".format(aep))
print("Capacity Factor: {:.2f}%".format(capacity_factor))
