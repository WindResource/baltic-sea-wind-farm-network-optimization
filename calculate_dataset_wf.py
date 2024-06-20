import arcpy
import numpy as np
import os

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

def process_oss_layer(layer, oss_fields, cost_dict, data_dict):
    with arcpy.da.SearchCursor(layer, oss_fields) as cursor:
        for row in cursor:
            wf_id = row[0]
            if wf_id not in cost_dict:
                cost_dict[wf_id] = [0, 0, 0, 0]
            cost_dict[wf_id][0] += row[5]
            if wf_id not in data_dict:
                data_dict[wf_id] = row[:5]

def process_turbine_layer(layer, turbine_fields, cost_dict):
    with arcpy.da.SearchCursor(layer, turbine_fields) as cursor:
        for row in cursor:
            wf_id = row[0]
            if wf_id in cost_dict:
                cost_dict[wf_id][1] += row[1]
                cost_dict[wf_id][2] += row[2]
                cost_dict[wf_id][3] += row[3]

def process_iac_layer(layer, other_fields, cost_dict):
    with arcpy.da.SearchCursor(layer, other_fields) as cursor:
        for row in cursor:
            wf_id = row[0]
            if wf_id in cost_dict:
                cost_dict[wf_id][1] += row[1]
                cost_dict[wf_id][2] += row[1]
                cost_dict[wf_id][3] += row[1]

def gen_dataset(output_folder):
    """
    Generate datasets by importing necessary data from the turbine, IAC, and OSS layers,
    summing the TotalCost values for corresponding WF_IDs, and saving the required
    information in a structured .npy array and a text file.
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
    turbine_fields = ['WF_ID', 'TC_2030', 'TC_2040', 'TC_2050']
    other_fields = ['WF_ID', 'TotalCost']

    cost_dict = {}
    data_dict = {}

    process_oss_layer(layers['oss'], oss_fields, cost_dict, data_dict)
    process_turbine_layer(layers['turbine'], turbine_fields, cost_dict)
    process_iac_layer(layers['iac'], other_fields, cost_dict)

    dtype = [('WF_ID', 'i8'), ('ISO', 'U50'), ('Longitude', 'f8'), ('Latitude', 'f8'), ('TotalCap', 'f8'), 
            ('TC_2030', 'f8'), ('TC_2040', 'f8'), ('TC_2050', 'f8')]
    filtered_data = [(wf_id, data[1], round(data[2], 6), round(data[3], 6), round(data[4]), 
                    round(cost_dict[wf_id][0] + cost_dict[wf_id][1], 3), 
                    round(cost_dict[wf_id][0] + cost_dict[wf_id][2], 3), 
                    round(cost_dict[wf_id][0] + cost_dict[wf_id][3], 3))
                    for wf_id, data in data_dict.items() if round(data[4]) > 0]

    structured_array = np.array(filtered_data, dtype=dtype)

    npy_filename = os.path.join(output_folder, 'wf_data.npy')
    np.save(npy_filename, structured_array)

    txt_filename = os.path.join(output_folder, 'wf_data.txt')
    save_structured_array_to_txt(txt_filename, structured_array)

    arcpy.AddMessage(f"Data saved to {npy_filename} and {txt_filename}")

if __name__ == "__main__":
    output_folder = f"C:\\Users\\cflde\\Documents\\Graduation Project\\ArcGIS Pro\\BalticSea\\Results\\datasets"
    gen_dataset(output_folder)