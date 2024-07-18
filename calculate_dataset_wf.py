import arcpy
import numpy as np
import os
import pandas as pd

def save_structured_array_to_txt(filename, structured_array):
    """
    Saves a structured numpy array to a text file.

    Parameters:
    - filename (str): The path to the file where the array should be saved.
    - structured_array (numpy structured array): The array to save.
    """
    with open(filename, 'w') as file:
        header = ', '.join(structured_array.dtype.names)
        file.write(header + '\n')
        for row in structured_array:
            row_str = ', '.join(str(value) for value in row)
            file.write(row_str + '\n')

def process_oss_layer(layer, oss_fields, total_cost_dict, wind_farm_data_dict):
    """
    Process the OSS layer to extract relevant data.

    Parameters:
    - layer (object): The OSS layer object.
    - oss_fields (list): The list of fields to extract.
    - total_cost_dict (dict): The dictionary to store total cost data.
    - wind_farm_data_dict (dict): The dictionary to store additional data.
    """
    with arcpy.da.SearchCursor(layer, oss_fields) as cursor:
        for row in cursor:
            wind_farm_id = row[0]
            if wind_farm_id not in total_cost_dict:
                total_cost_dict[wind_farm_id] = 0
            total_cost_dict[wind_farm_id] += row[5]
            if wind_farm_id not in wind_farm_data_dict:
                wind_farm_data_dict[wind_farm_id] = row[:5]

def process_turbine_layer(layer, turbine_fields, tc_2030_dict, tc_2040_dict, tc_2050_dict, total_aep_dict, avg_cf_dict, turbine_count_dict):
    """
    Process the turbine layer to extract relevant data.

    Parameters:
    - layer (object): The turbine layer object.
    - turbine_fields (list): The list of fields to extract.
    - tc_2030_dict (dict): The dictionary to store TC_2030 data.
    - tc_2040_dict (dict): The dictionary to store TC_2040 data.
    - tc_2050_dict (dict): The dictionary to store TC_2050 data.
    - total_aep_dict (dict): The dictionary to store Total AEP data.
    - avg_cf_dict (dict): The dictionary to store Average Capacity Factor data.
    - turbine_count_dict (dict): The dictionary to store turbine count for averaging Capacity Factor.
    """
    with arcpy.da.SearchCursor(layer, turbine_fields) as cursor:
        for row in cursor:
            wind_farm_id = row[0]
            if wind_farm_id not in tc_2030_dict:
                tc_2030_dict[wind_farm_id] = 0
            if wind_farm_id not in tc_2040_dict:
                tc_2040_dict[wind_farm_id] = 0
            if wind_farm_id not in tc_2050_dict:
                tc_2050_dict[wind_farm_id] = 0
            if wind_farm_id not in total_aep_dict:
                total_aep_dict[wind_farm_id] = 0
            if wind_farm_id not in avg_cf_dict:
                avg_cf_dict[wind_farm_id] = 0
            if wind_farm_id not in turbine_count_dict:
                turbine_count_dict[wind_farm_id] = 0
                
            tc_2030_dict[wind_farm_id] += row[1]
            tc_2040_dict[wind_farm_id] += row[2]
            tc_2050_dict[wind_farm_id] += row[3]
            total_aep_dict[wind_farm_id] += row[4]
            avg_cf_dict[wind_farm_id] += row[5]
            turbine_count_dict[wind_farm_id] += 1

def process_iac_layer(layer, other_fields, iac_cost_dict):
    """
    Process the IAC layer to extract relevant data.

    Parameters:
    - layer (object): The IAC layer object.
    - other_fields (list): The list of fields to extract.
    - iac_cost_dict (dict): The dictionary to store IAC cost data.
    """
    with arcpy.da.SearchCursor(layer, other_fields) as cursor:
        for row in cursor:
            wind_farm_id = row[0]
            if wind_farm_id not in iac_cost_dict:
                iac_cost_dict[wind_farm_id] = 0
            iac_cost_dict[wind_farm_id] += row[1]

def gen_dataset(output_folder):
    """
    Generate datasets by importing necessary data from the turbine, IAC, and OSS layers,
    summing the TotalCost values for corresponding WF_IDs, and saving the required
    information in a structured .npy array and a text file.

    Parameters:
    - output_folder (str): The path to the folder where the output files will be saved.
    """
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map = aprx.activeMap

    layers = {
        'turbine': next((layer for layer in map.listLayers() if layer.name.startswith('WTC')), None),
        'iac': next((layer for layer in map.listLayers() if layer.name.startswith('IAC')), None),
        'oss': next((layer for layer in map.listLayers() if layer.name.startswith('OSSC')), None)
    }
    
    missing_layers = [name for name, layer in layers.items() if not layer]
    if missing_layers:
        arcpy.AddError(f"Missing layers: {', '.join(missing_layers)}")
        return

    for layer in layers.values():
        arcpy.SelectLayerByAttribute_management(layer, "CLEAR_SELECTION")
    
    arcpy.AddMessage(f"Processing layers: {', '.join(layer.name for layer in layers.values())}")

    oss_fields = ['WF_ID', 'ISO', 'Longitude', 'Latitude', 'TotalCap', 'TotalCost']
    turbine_fields = ['WF_ID', 'TC_2030', 'TC_2040', 'TC_2050', 'AEP', 'Cap_Factor']
    other_fields = ['WF_ID', 'TotalCost']

    total_cost_dict = {}
    wind_farm_data_dict = {}
    tc_2030_dict = {}
    tc_2040_dict = {}
    tc_2050_dict = {}
    total_aep_dict = {}
    avg_cf_dict = {}
    turbine_count_dict = {}
    iac_cost_dict = {}

    process_oss_layer(layers['oss'], oss_fields, total_cost_dict, wind_farm_data_dict)
    process_turbine_layer(layers['turbine'], turbine_fields, tc_2030_dict, tc_2040_dict, tc_2050_dict, total_aep_dict, avg_cf_dict, turbine_count_dict)
    process_iac_layer(layers['iac'], other_fields, iac_cost_dict)

    dtype = [('WF_ID', 'i8'), ('ISO', 'U50'), ('Longitude', 'f8'), ('Latitude', 'f8'), 
            ('TotalCap', 'f8'), ('TC_2030', 'f8'), ('TC_2040', 'f8'), ('TC_2050', 'f8'),
            ('TotalAEP', 'f8'), ('AverageCf', 'f8')]

    filtered_data = []
    for wind_farm_id, wind_farm_data in wind_farm_data_dict.items():
        if round(wind_farm_data[4]) > 0:
            total_aep = round(total_aep_dict[wind_farm_id], 3)
            avg_cf = round(avg_cf_dict[wind_farm_id] / turbine_count_dict[wind_farm_id], 3) if turbine_count_dict[wind_farm_id] > 0 else 0
            tc_oss = total_cost_dict.get(wind_farm_id, 0)
            tc_iac = iac_cost_dict.get(wind_farm_id, 0)
            tc_oss_iac = tc_oss + tc_iac
            tc_wf_2030 = round(tc_2030_dict.get(wind_farm_id, 0) + tc_oss_iac, 3)
            tc_wf_2040 = round(tc_2040_dict.get(wind_farm_id, 0) + tc_oss_iac, 3)
            tc_wf_2050 = round(tc_2050_dict.get(wind_farm_id, 0) + tc_oss_iac, 3)
            filtered_data.append((wind_farm_id, wind_farm_data[1], round(wind_farm_data[2], 6), round(wind_farm_data[3], 6), round(wind_farm_data[4]), 
                                    tc_wf_2030, tc_wf_2040, tc_wf_2050, total_aep, avg_cf))

    structured_array = np.array(filtered_data, dtype=dtype)

    npy_filename = os.path.join(output_folder, 'wf_data.npy')
    np.save(npy_filename, structured_array)

    txt_filename = os.path.join(output_folder, 'wf_data.txt')
    save_structured_array_to_txt(txt_filename, structured_array)

    arcpy.AddMessage(f"Data saved to {npy_filename} and {txt_filename}")
    
    # Convert structured array to pandas DataFrame
    df = pd.DataFrame(structured_array)

    # Define the Excel file path
    excel_filename = os.path.join(output_folder, 'wf_data.xlsx')

    # Aggregate data by ISO country code
    df_aggregated = df.groupby('ISO').agg({
        'WF_ID': 'count',
        'TotalCap': 'sum',
        'TC_2030': 'sum',
        'TC_2040': 'sum',
        'TC_2050': 'sum',
        'TotalAEP': 'sum',
        'AverageCf': 'mean'
    }).reset_index()

    df_aggregated.rename(columns={'WF_ID': 'WindFarmCount'}, inplace=True)

    # Aggregate global data values
    global_data = df.agg({
        'WF_ID': 'count',
        'TotalCap': 'sum',
        'TC_2030': 'sum',
        'TC_2040': 'sum',
        'TC_2050': 'sum',
        'TotalAEP': 'sum',
        'AverageCf': 'mean'
    }).to_frame().T

    global_data.insert(0, 'Global', 'Total')

    # Save the DataFrame to an Excel file with three sheets
    with pd.ExcelWriter(excel_filename) as writer:
        df.to_excel(writer, sheet_name='WindFarmData', index=False)
        df_aggregated.to_excel(writer, sheet_name='AggregatedData', index=False)
        global_data.to_excel(writer, sheet_name='GlobalData', index=False)

    arcpy.AddMessage(f"Data saved to {npy_filename}, {txt_filename}, and {excel_filename}")

if __name__ == "__main__":
    output_folder = f"C:\\Users\\cflde\\Documents\\Graduation Project\\ArcGIS Pro\\BalticSea\\Results\\datasets"
    gen_dataset(output_folder)