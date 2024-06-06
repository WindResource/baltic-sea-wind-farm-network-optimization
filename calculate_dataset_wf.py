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
    # Open the file in write mode
    with open(filename, 'w') as file:
        # Write header
        header = ', '.join(structured_array.dtype.names)
        file.write(header + '\n')

        # Write data rows
        for row in structured_array:
            row_str = ', '.join(str(value) for value in row)
            file.write(row_str + '\n')

def update_fields(output_folder):
    """
    Update fields by importing necessary data from the turbine, IAC, and OSS layers,
    summing the TotalCost values for corresponding WF_IDs, and saving the required
    information in a structured .npy array and a text file.
    """
    # Access the current ArcGIS project
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map = aprx.activeMap

    # Locate the necessary layers
    turbine_layer = next((layer for layer in map.listLayers() if layer.name.startswith('WTC')), None)
    iac_layer = next((layer for layer in map.listLayers() if layer.name.startswith('IAC')), None)
    oss_layer = next((layer for layer in map.listLayers() if layer.name.startswith('OSSC')), None)
    
    # Check if the layers exist
    if not turbine_layer:
        arcpy.AddError("No layer starting with 'WTC' found in the current map.")
        return
    if not iac_layer:
        arcpy.AddError("No layer starting with 'IAC' found in the current map.")
        return
    if not oss_layer:
        arcpy.AddError("No layer starting with 'OSSC' found in the current map.")
        return

    # Deselect all currently selected features
    arcpy.SelectLayerByAttribute_management(turbine_layer, "CLEAR_SELECTION")
    arcpy.SelectLayerByAttribute_management(iac_layer, "CLEAR_SELECTION")
    arcpy.SelectLayerByAttribute_management(oss_layer, "CLEAR_SELECTION")
    
    arcpy.AddMessage(f"Processing layers: {turbine_layer.name}, {iac_layer.name}, {oss_layer.name}")

    # Define the fields to extract
    oss_fields = ['WF_ID', 'ISO', 'Longitude', 'Latitude', 'TotalCap', 'TotalCost']
    other_fields = ['WF_ID', 'TotalCost']

    # Create a dictionary to hold the summed TotalCost for each WF_ID
    cost_dict = {}
    data_dict = {}

    # Helper function to process the OSS layer
    def process_oss_layer(layer):
        with arcpy.da.SearchCursor(layer, oss_fields) as cursor:
            for row in cursor:
                wf_id = row[0]
                if wf_id not in cost_dict:
                    cost_dict[wf_id] = 0
                cost_dict[wf_id] += row[5]
                if wf_id not in data_dict:
                    data_dict[wf_id] = row[:5]

    # Helper function to process the other layers (turbine and IAC)
    def process_other_layer(layer):
        with arcpy.da.SearchCursor(layer, other_fields) as cursor:
            for row in cursor:
                wf_id = row[0]
                if wf_id in cost_dict:  # Only sum if WF_ID exists in OSS layer
                    cost_dict[wf_id] += row[1]

    # Process the OSS layer to get the full set of data
    process_oss_layer(oss_layer)
    # Process the other layers to accumulate TotalCost
    process_other_layer(turbine_layer)
    process_other_layer(iac_layer)

    # Prepare the structured array
    dtype = [('WF_ID', 'i8'), ('ISO', 'U50'), ('Longitude', 'f8'), ('Latitude', 'f8'), ('TotalCap', 'f8'), ('TotalCost', 'f8')]
    structured_array = np.zeros(len(cost_dict), dtype=dtype)

    # Populate the structured array
    for idx, wf_id in enumerate(cost_dict.keys()):
        iso, lon, lat, total_cap = data_dict[wf_id][1:5]
        total_cost = cost_dict[wf_id]
        structured_array[idx] = (wf_id, iso, round(lon, 6), round(lat, 6), round(total_cap), round(total_cost))

    # Save the structured array to a .npy file
    npy_filename = os.path.join(output_folder, 'wf_data.npy')
    np.save(npy_filename, structured_array)

    # Save the structured array to a text file
    txt_filename = os.path.join(output_folder, 'wf_data.txt')
    save_structured_array_to_txt(txt_filename, structured_array)

    arcpy.AddMessage(f"Data saved to {npy_filename} and {txt_filename}")

if __name__ == "__main__":
    output_folder = f"C:\\Users\\cflde\\Documents\\Graduation Project\\ArcGIS Pro\\BalticSea\\Results\\datasets"
    update_fields(output_folder)
