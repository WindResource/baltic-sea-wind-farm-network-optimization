import arcpy
import numpy as np
from scipy.interpolate import interp1d
from scipy.stats import weibull_min

def calculate_aep_and_capacity_factor_precomputed(weibullA, weibullK, power_output, wind_speed_array):
    """
    Calculate the Annual Energy Production (AEP) and Capacity Factor of a wind turbine.

    Args:
        weibullA (float): Weibull scale parameter (m/s).
        weibullK (float): Weibull shape parameter.
        power_output (ndarray): Precomputed power output array.
        wind_speed_array (ndarray): Precomputed wind speed array.

    Returns:
        tuple: A tuple containing the AEP (in kWh) and the Capacity Factor (as a percentage).
    """
    alpha = 0.11  # Exponent of the power law for scaling wind speed
    hub_height = 150  # Wind turbine hub height

    # Average number of hours in a year
    hours_per_year = 365.25 * 24

    # Wind turbine availability factor
    avail_factor = 0.94
    wake_factor = 0.85

    turbine_rating = 15 * 1e3  # Turbine rating (kW)

    # Scale the Weibull parameters to hub height using the power law
    weibullA_hh = weibullA * (hub_height / 100) ** alpha

    # Define the Weibull distribution with the scaled parameters
    weibull_dist = weibull_min(weibullK, scale=weibullA_hh)

    # Calculate probability density function (PDF) of Weibull distribution at each wind speed
    pdf_array = weibull_dist.pdf(wind_speed_array)

    # Calculate AEP by integrating the product of power output and PDF over wind speeds
    aep = np.trapz(power_output * pdf_array, wind_speed_array) * hours_per_year * avail_factor * wake_factor # kWh per year

    # Calculate capacity factor
    capacity_factor = aep / (turbine_rating * hours_per_year)

    return aep, capacity_factor

def update_fields():
    """
    Update the attribute table of the wind turbine layer with AEP and capacity factor.
    """
    # Access the current ArcGIS project
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map = aprx.activeMap

    # Find the wind turbine layer in the map
    turbine_layer = next((layer for layer in map.listLayers() if layer.name.startswith('WTC')), None)

    # Check if the turbine layer exists
    if not turbine_layer:
        arcpy.AddError("No layer starting with 'WTC' found in the current map.")
        return

    # Deselect all currently selected features
    arcpy.SelectLayerByAttribute_management(turbine_layer, "CLEAR_SELECTION")

    arcpy.AddMessage(f"Processing layer: {turbine_layer.name}")

    # Check if required fields exist in the attribute table
    required_fields = ['WeibullA', 'WeibullK']
    existing_fields = [field.name for field in arcpy.ListFields(turbine_layer)]
    for field in required_fields:
        if field not in existing_fields:
            arcpy.AddError(f"Required field '{field}' is missing in the attribute table.")
            return

    # Add 'AEP' and 'Capacity_Factor' fields if they do not exist
    for field in ['AEP', 'Cap_Factor']:
        if field not in existing_fields:
            arcpy.AddField_management(turbine_layer, field, "DOUBLE")

    # Define wind speed range
    speed_min = 0
    speed_max = 50
    cutoff_wind_speed = 25  # Cut-off wind speed (m/s)

    # Create wind speed array for integration
    wind_speed_array = np.linspace(speed_min, speed_max, num=1000)

    # Power curve of the IEA Wind 15-Megawatt Offshore Reference Wind Turbine
    power_curve_data = {
        3.00: 0.070, 3.50: 0.302, 4.00: 0.595, 4.50: 0.965, 4.75: 1.185, 5.00: 1.429,
        5.25: 1.695, 6.00: 2.656, 6.20: 2.957, 6.40: 3.276, 6.50: 3.443, 6.55: 3.529,
        6.60: 3.615, 6.70: 3.791, 6.80: 3.972, 6.90: 4.156, 6.92: 4.192, 6.93: 4.211,
        6.94: 4.229, 6.95: 4.247, 6.96: 4.265, 6.97: 4.284, 6.98: 4.302, 6.99: 4.320,
        7.00: 4.339, 7.50: 5.339, 8.00: 6.481, 8.50: 7.775, 9.00: 9.229, 9.50: 10.855,
        10.00: 12.661, 10.25: 13.638, 10.50: 14.661, 10.60: 14.995, 10.70: 14.995,
        10.72: 14.995, 10.74: 14.995, 10.76: 14.995, 10.78: 14.995, 10.79: 14.995,
        10.80: 14.995, 10.90: 14.994, 11.00: 14.994, 11.25: 14.994, 11.50: 14.994,
        11.75: 14.994, 12.00: 14.994, 13.00: 14.995, 14.00: 14.995, 15.00: 14.995,
        17.50: 14.995, 20.00: 14.995, 22.50: 14.996, 25.00: 14.998
    }

    # Create interpolation function for power curve
    wind_speeds = np.array(list(power_curve_data.keys()))
    power_values = np.array(list(power_curve_data.values()))  # Power values are already in kW
    power_curve_func = interp1d(wind_speeds, power_values, kind='linear', fill_value='extrapolate')

    # Calculate the power output at each wind speed considering the cut-off wind speed
    power_output = np.array([power_curve_func(wind_speed) if wind_speed <= cutoff_wind_speed else 0 for wind_speed in wind_speed_array])

    # Read WeibullA and WeibullK values and calculate AEP and Capacity Factor
    aep_cf_values = []
    with arcpy.da.SearchCursor(turbine_layer, ['WeibullA', 'WeibullK']) as cursor:
        for row in cursor:
            weibullA, weibullK = row
            aep, capacity_factor = calculate_aep_and_capacity_factor_precomputed(weibullA, weibullK, power_output, wind_speed_array)
            aep_cf_values.append((round(aep / int(1e6), 3), round(capacity_factor, 2)))  # AEP in GWh

    # Update the attribute table with the calculated values
    with arcpy.da.UpdateCursor(turbine_layer, ['AEP', 'Cap_Factor']) as cursor:
        for idx, row in enumerate(cursor):
            row[0], row[1] = aep_cf_values[idx]
            cursor.updateRow(row)

    arcpy.AddMessage("AEP and capacity factor calculations completed and added to the attribute table.")

if __name__ == "__main__":
    # Call the update_fields() function
    update_fields()