import arcpy
import numpy as np
from scipy.interpolate import interp1d
from scipy.stats import weibull_min

def jensen_wake_loss_factor(distance, D, U, U_i):
    """
    Calculate the wake loss factor using the Jensen Cosine wake model.

    Args:
        distance (float): Distance between turbines (m).
        D (float): Rotor diameter of the downstream turbine (m).
        U (float): Wind speed at downstream turbine location (m/s).
        U_i (float): Wind speed at upstream turbine location (m/s).

    Returns:
        float: Wake loss factor.
    """
    k = 0.04  # Wake decay coefficient
    x = distance / D
    return (1 - np.sqrt(1 - (D / (D + 2 * k * (U_i - U)))**2 * (1 - np.cos(np.arctan(k * x / (1 - x))))))

def calculate_aep_and_capacity_factor(weibullA, weibullK, turbine_locations, wind_direction):
    """
    Calculate the Annual Energy Production (AEP) and Capacity Factor of a wind turbine.

    Args:
        weibullA (float): Weibull scale parameter (m/s).
        weibullK (float): Weibull shape parameter.
        turbine_locations (list of tuples): List of tuples containing (latitude, longitude) coordinates of turbine locations.
        wind_direction (str): Direction of the wind ("west" or "southwest").

    Returns:
        tuple: A tuple containing the AEP (in kWh) and the Capacity Factor (as a percentage).
    """
    alpha = 0.11  # Exponent of the power law for scaling wind speed
    hub_height = 112 # Hub height 8MW
    
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

    # Scale wind speed array to 112m using power law
    wind_speed_array_112m = wind_speed_array * (hub_height/100)**alpha

    # Calculate probability density function (PDF) of Weibull distribution at each wind speed
    pdf_array = weibull_dist.pdf(wind_speed_array_112m)

    # Adjusting the power output considering the cutoff wind speed
    power_output = np.array([power_curve_func(wind_speed) if wind_speed <= cutoff_wind_speed else 0 for wind_speed in wind_speed_array_112m])

    # Initialize wake loss factors for each turbine
    wake_loss_factors = np.ones(len(turbine_locations))

    # Determine downstream turbines based on wind direction
    if wind_direction == "southwest":
        # Sort turbines based on latitude (from north to south) and then longitude (from west to east)
        sorted_turbine_locations = sorted(turbine_locations, key=lambda x: (x[0], x[1]))
    else:
        # Handle other wind directions if needed
        pass

    # Apply wake losses for each turbine
    for i, (lat_i, lon_i) in enumerate(sorted_turbine_locations):
        # Calculate wake loss factors for downstream turbines
        for j in range(i + 1, len(sorted_turbine_locations)):  # Start from the next turbine in the sorted list
            lat_j, lon_j = sorted_turbine_locations[j]
            # Determine direction based on latitude and longitude differences
            lat_diff = lat_j - lat_i
            lon_diff = lon_j - lon_i
            if wind_direction == "southwest":
                if lat_diff <= 0 and lon_diff <= 0:  # Check if the turbine is downstream
                    distance = np.sqrt(lat_diff**2 + lon_diff**2) * 111000  # Distance between turbines in meters (approximation)
                    wake_loss_factor = jensen_wake_loss_factor(distance, 100, wind_speed_array_112m[i], wind_speed_array_112m[j])
                    wake_loss_factors[j] *= wake_loss_factor
            else:
                # Handle other wind directions if needed
                pass

    # Apply wake losses to power output
    power_output *= wake_loss_factors

    # Calculate AEP by summing the product of power output and interpolated PDF over wind speeds
    aep = np.sum(power_output * pdf_array) * hours_per_year * ava_factor # Convert to kWh per year

    # Calculate capacity factor
    capacity_factor = (aep / (turbine_rating * hours_per_year * len(turbine_locations))) * 100  # Convert to percentage

    return aep, capacity_factor

def update_fields():
    """
    Update the attribute table of the wind turbine layer with AEP, capacity factor, and wake loss factor.
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

    # Add 'AEP', 'Capacity_Factor', and 'WakeLoss' fields if they do not exist
    for field in ['AEP', 'Cap_Factor', 'WakeLoss']:
        if field not in existing_fields:
            arcpy.AddField_management(turbine_layer, field, "DOUBLE")

    # Retrieve WeibullA and WeibullK values for each wind turbine
    turbine_locations = []
    with arcpy.da.UpdateCursor(turbine_layer, ['SHAPE@XY', 'WeibullA', 'WeibullK', 'AEP', 'Cap_Factor', 'WakeLoss']) as cursor:
        for row in cursor:
            lat, lon = row[0][0], row[0][1]
            turbine_locations.append((lat, lon))
            weibullA, weibullK = row[1], row[2]
            aep, capacity_factor, wake_loss_factor = calculate_aep_and_capacity_factor(weibullA, weibullK, turbine_locations, "southwest")
            row[3] = round(aep / int(1e6), 4)  # AEP in GWh
            row[4] = round(capacity_factor, 2)
            row[5] = round(wake_loss_factor, 4)
            cursor.updateRow(row)

    arcpy.AddMessage("AEP, capacity factor, and wake loss factor calculations completed and added to the attribute table.")

if __name__ == "__main__":
    # Call the update_fields() function
    update_fields()
