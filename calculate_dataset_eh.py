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

def gen_dataset(output_folder: str):
    """
    Generates a dataset from the energy hub layer in the current ArcGIS project 
    and saves it as both a NumPy binary file (.npy) and a text file (.txt) in the specified folder.

    Parameters:
    - output_folder (str): The path to the folder where the output files will be saved.
    """
    # Access the current ArcGIS project
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map = aprx.activeMap

    # Find the energy hub layer
    eh_layers = [layer for layer in map.listLayers() if layer.name.startswith('EHC')]

    # Check if any OSSC layer exists
    if not eh_layers:
        arcpy.AddError("No layer starting with 'OSSC' found in the current map.")
        return

    # Select the first OSSC layer
    eh_layer = eh_layers[0]

    # Deselect all currently selected features
    arcpy.SelectLayerByAttribute_management(eh_layer, "CLEAR_SELECTION")

    arcpy.AddMessage(f"Processing layer: {eh_layer.name}")

    # Check if required fields exist
    required_fields = ['EH_ID', 'ISO', 'Longitude', 'Latitude', 'WaterDepth', 'IceCover', 'Distance']
    for field in required_fields:
        if field not in [f.name for f in arcpy.ListFields(eh_layer)]:
            arcpy.AddError(f"Required field '{field}' is missing in the attribute table.")
            return

    # Convert attribute table to NumPy array
    array = arcpy.da.FeatureClassToNumPyArray(eh_layer, required_fields)

    # Update IceCover to binary format
    array['IceCover'] = np.where(array['IceCover'] == "Yes", 1, 0)

    # Define the dtype for the structured array
    dtype = [('EH_ID', 'U10'), 
            ('ISO', 'U3'), 
            ('Longitude', 'f8'), 
            ('Latitude', 'f8'), 
            ('WaterDepth', 'i4'), 
            ('IceCover', 'i4'), 
            ('PortDistance', 'f8')]

    # Create the structured array directly from the existing array, ensuring it fits the defined dtype
    data_array = np.array(list(zip(array['EH_ID'], array['ISO'], array['Longitude'], array['Latitude'], array['WaterDepth'], array['IceCover'], array['Distance'])), dtype=dtype)

    # Save the structured array to a .npy file in the specified folder
    np.save(os.path.join(output_folder, 'eh_data.npy'), data_array)
    arcpy.AddMessage("NumPy data saved successfully.")

    # Save the structured array to a text file
    save_structured_array_to_txt(os.path.join(output_folder, 'eh_data.txt'), data_array)
    arcpy.AddMessage("Text data saved successfully.")

if __name__ == "__main__":
    # Prompt the user to input the folder path where they want to save the output files
    output_folder = arcpy.GetParameterAsText(0)
    gen_dataset(output_folder)
