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

    # Power curve of the NREL Reference 15MW wind turbine
    power_curve_data = {
        3: 0, 4: 720, 5: 1239, 6: 2271, 7: 3817, 8: 5661, 9: 7758, 10: 10000, 11: 12503,
        12: 15000, 13: 15000, 14: 15000, 15: 15000, 16: 15000, 17: 15000, 18: 15000,
        19: 15000, 20: 15000, 21: 15000, 22: 15000, 23: 15000, 24: 15000, 25: 15000
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