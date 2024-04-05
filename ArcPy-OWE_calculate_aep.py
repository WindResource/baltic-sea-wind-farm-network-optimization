import arcpy
import numpy as np
from scipy.interpolate import interp1d
from scipy.stats import weibull_min

def calculate_aep_and_capacity_factor(weibullA, weibullK):
    """
    Calculate the Annual Energy Production (AEP) and Capacity Factor of a wind turbine.

    Args:
        weibullA (float): Weibull scale parameter (m/s).
        weibullK (float): Weibull shape parameter.

    Returns:
        tuple: A tuple containing the AEP (in kWh) and the Capacity Factor (as a percentage).
    """
    # Average number of hours in a year
    hours_per_year = 365.25 * 24
    
    # Wind turbine availability factor
    ava_factor = 0.94
    
    turbine_rating = 8 * 1e3  # Turbine rating (kW)
    cutoff_wind_speed = 25  # Cut-off wind speed (m/s)

    # Power curve of the NREL Reference 8MW wind turbine
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

    # Define the Weibull distribution with the provided parameters
    weibull_dist = weibull_min(weibullK, scale=weibullA)

    # Define wind speed range
    speed_min = 0
    speed_max = 50

    # Create wind speed array for integration
    wind_speed_array = np.linspace(speed_min, speed_max, num=1000)

    # Calculate probability density function (PDF) of Weibull distribution at each wind speed
    pdf_array = weibull_dist.pdf(wind_speed_array)

    # Adjusting the power output considering the cutoff wind speed
    power_output = np.array([power_curve_func(wind_speed) if wind_speed <= cutoff_wind_speed else 0 for wind_speed in wind_speed_array])

    # Calculate AEP by summing the product of power output and interpolated PDF over wind speeds
    aep = np.sum(power_output * pdf_array) * hours_per_year * ava_factor # Convert to kWh per year

    # Calculate capacity factor
    capacity_factor = (aep / (turbine_rating * hours_per_year)) * 100  # Convert to percentage

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

    # Retrieve WeibullA and WeibullK values for each wind turbine
    with arcpy.da.UpdateCursor(turbine_layer, ['WeibullA', 'WeibullK', 'AEP', 'Cap_Factor']) as cursor:
        for row in cursor:
            weibullA, weibullK = row[:2]
            aep, capacity_factor = calculate_aep_and_capacity_factor(weibullA, weibullK)
            row[2] = round(aep / int(1e6), 4) # AEP in GWh
            row[3] = round(capacity_factor, 2)
            cursor.updateRow(row)

    arcpy.AddMessage("AEP and capacity factor calculations completed and added to the attribute table.")

if __name__ == "__main__":
    # Call the update_fields() function
    update_fields()
