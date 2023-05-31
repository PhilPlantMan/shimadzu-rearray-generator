# -*- coding: utf-8 -*-
"""
Created on Fri May 26 10:02:25 2023

@author: PhilipKirk
"""

import pandas as pd
import os
import tkinter as tk
from tkinter import filedialog
import re


def read_stub_tsv(path):
    basename = os.path.basename(path)
    arrayPath = os.path.join(path, basename+"_RearrayTemplate.tsv")
    df = pd.read_csv(arrayPath, sep = '\t', header = None, names = ["source", "sourceRow", "sourceCol", "target"])
    return df

def select_CD_directory():
    pixlAppdataPath = os.path.join(os.getenv('APPDATA'),
                                   "Singer Instrument Company Limited\PIXL\Tracking")
    directory = filedialog.askdirectory(initialdir = pixlAppdataPath)
    directory_entry.delete(0, tk.END)  # Clear the existing entry
    directory_entry.insert(tk.END, directory)

def select_export_directory():
    export_directory = get_export_directory()
    directory = filedialog.askdirectory(initialdir = export_directory)
    export_directory_entry.delete(0, tk.END)  # Clear the existing entry
    export_directory_entry.insert(tk.END, directory)

def run():
    validCDPath = validate_stub_path()
    if validCDPath:
        well = well_var.get()
        starting_target = wellID_dropdown.get()
        matrix_type = matrix_var.get()


        output_text.insert(tk.END, "Matrix reservoir well: {}\n".format(well))
        output_text.insert(tk.END, "Target starting position: {}\n".format(starting_target))
        output_text.insert(tk.END, "Matrix addition mode: {}\n".format(matrix_type))
        #
        if additional_options_var.get() == 1:
            output_text.insert(tk.END, "Additional {} {} target plate enabled\n".format(format_var.get(), plate_type_var.get()))
        stub_df = read_stub_tsv(directory_entry.get())
        export_pixl_array(stub_df)
        output_text.insert(tk.END, "Success! PIXL rearry file exported")

        update_config_all()
        output_text.insert(tk.END, "\n")

def validate_stub_path():
    path = os.path.normpath(directory_entry.get())
    split_path = path.split(os.sep)
    validCDPath = split_path[-2] == "Colony Detection"
    if validCDPath: output_text.insert(tk.END, "Valid Colony Detection project found"+ "\n")
    else: output_text.insert(tk.END, "Colony Detection project not found. Please ensure the parent folder of the project selected is 'Colony Detection'"+ "\n")
    return validCDPath

def prepare_pixl_array(stub_df):
    pixlArray_df = pd.DataFrame(columns=["source", "sourceRow", "sourceCol", "target", "targetRow", "targetCol"])
    s1 = pd.Series({"source" : 'matrixMWP', 'sourceRow' : "SBS", 'sourceCol' : 96, 'target': "Source"})
    s2 = pd.Series({"source" : 'SlideAdapter', 'sourceRow' : "SBS", 'sourceCol' : "NONE", 'target': "Target"})
    firstStubRow = stub_df.iloc[0,:]
    pixlArray_df = pd.concat([pixlArray_df, s1.to_frame().T], ignore_index=True)
    pixlArray_df = pd.concat([pixlArray_df, s2.to_frame().T], ignore_index=True)
    pixlArray_df = pd.concat([pixlArray_df, firstStubRow.to_frame().T], ignore_index=True)
    return pixlArray_df

def append_pixl_commands_to_array(prepared_array, stub_df):

    shimadzuAdapterIndex = shimadzuAdapterCoords_df[shimadzuAdapterCoords_df["wellID"]== wellID_dropdown.get()].index.values

    for index, row in stub_df.iterrows():
        if index == 0: continue
        shimadzuAdapterRow = shimadzuAdapterCoords_df.iloc[shimadzuAdapterIndex,:]
        prepared_array = append_colony_transfer(prepared_array,row, shimadzuAdapterRow)
        prepared_array = append_matrix_transfer(prepared_array, shimadzuAdapterRow)
        if (matrix_var.get() == "Double Dip"):
            prepared_array = append_matrix_transfer(prepared_array, shimadzuAdapterRow)

        shimadzuAdapterIndex += 1
    return prepared_array

def append_colony_transfer(prepared_array, stubRow, shimadzuAdapterRow):
    if type(shimadzuAdapterRow) == pd.core.frame.DataFrame:
        shimadzuAdapterRow = shimadzuAdapterRow.squeeze(axis = 0)
    targetSeries = pd.Series({"source": stubRow['source'],"sourceRow": stubRow['sourceRow'],"sourceCol": stubRow['sourceCol'], "target": "SlideAdapter","targetRow": shimadzuAdapterRow.loc['y'] ,"targetCol":shimadzuAdapterRow.loc['x']})
    prepared_array = pd.concat([prepared_array, targetSeries.to_frame().T], ignore_index=True)
    return prepared_array

def append_matrix_transfer(prepared_array, shimadzuAdapterRow):

    match = re.match(r"([a-z]+)([0-9]+)", well_var.get(), re.I)
    if match:
        items = match.groups()
        matrixRow = items[0]
        matrixCol = items[1]

    if type(shimadzuAdapterRow) == pd.core.frame.DataFrame:
        shimadzuAdapterRow = shimadzuAdapterRow.squeeze(axis = 0)

    targetSeries = pd.Series({"source": "matrixMWP","sourceRow": matrixRow,"sourceCol": matrixCol, "target": "SlideAdapter","targetRow": shimadzuAdapterRow.loc['y'] ,"targetCol":shimadzuAdapterRow.loc['x']})
    prepared_array = pd.concat([prepared_array, targetSeries.to_frame().T], ignore_index=True)
    return prepared_array

def read_config_variable(variable_name):
    config_file = "config.txt"
    try:
        with open(config_file, "r") as file:
            for line in file:
                if line.startswith(variable_name):
                    export_directory = line.split("=")[1].strip()
                    return export_directory

    except FileNotFoundError:
        print(f"Error: {config_file} not found.")
        return None


def update_config_variable(variable_name, new_value):
    config_file = "config.txt"
    updated_lines = []

    try:
        with open(config_file, "r") as file:
            for line in file:
                if line.startswith(variable_name):
                    line = f"{variable_name} = {new_value}\n"
                updated_lines.append(line)

        with open(config_file, "w") as file:
            file.writelines(updated_lines)

    except FileNotFoundError:
        print(f"Error: {config_file} not found.")

def update_config_all():
    update_config_variable("matrix_position", well_var.get())
    update_config_variable("first_target_position", wellID_dropdown.get())
    update_config_variable("matrix_application_mode", matrix_var.get())
    update_config_variable("rearry_export_directory", export_directory_entry.get())

def get_export_directory():
    export_directory = read_config_variable("rearry_export_directory")
    if export_directory == "desktop": export_directory = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
    return export_directory

def export_pixl_array(stub_df):
    global pixl_array
    pixl_array = prepare_pixl_array(stub_df)
    pixl_array = append_pixl_commands_to_array(pixl_array, stub_df)

    if additional_options_var.get() == 1:
        pixl_array = append_additional_target_to_array(pixl_array, stub_df)

    project_name = os.path.basename(directory_entry.get())
    array_path = os.path.join(export_directory_entry.get(), project_name + "_MALDI_Rearray.csv")
    pixl_array.to_csv(array_path, header = False, index = False)

def show_additional_options():
    if additional_options_var.get() == 1:
        export_directory_label.pack_forget()
        export_directory_entry.pack_forget()
        export_directory_button.pack_forget()
        run_button.pack_forget()
        output_label.pack_forget()
        output_text.pack_forget()
        format_label.pack()
        format_96_radiobutton.pack()
        format_384_radiobutton.pack()
        plate_type_label.pack()
        plate_type_agar_radiobutton.pack()
        plate_type_multiwell_radiobutton.pack()
        start_position_label.pack()
        start_position_dropdown.pack()
        export_directory_label.pack()
        export_directory_entry.pack()
        export_directory_button.pack()
        run_button.pack()
        output_label.pack()
        output_text.pack()
        format_var.trace('w', update_start_position_options)
    else:
        format_label.pack_forget()
        format_96_radiobutton.pack_forget()
        format_384_radiobutton.pack_forget()
        plate_type_label.pack_forget()
        plate_type_agar_radiobutton.pack_forget()
        plate_type_multiwell_radiobutton.pack_forget()
        start_position_label.pack_forget()
        start_position_dropdown.pack_forget()

def array_lister(array_format):
    if array_format == "96":
        rows = 8
        cols = 12
    elif array_format == "384":
        rows = 16
        cols = 24
    else: raise Exception("format not compatible")
    well_positions = []
    for row in range(rows):
        for col in range(cols):
            well_positions.append("{}{}".format(chr(65 + row), col + 1))
    return well_positions

def update_start_position_options(*args):
    format_selection = format_var.get()
    valid_positions = array_lister(format_selection)
    # Clear the current options and update with the valid positions
    start_position_dropdown['menu'].delete(0, 'end')
    for position in valid_positions:
        start_position_dropdown['menu'].add_command(label=position, command=tk._setit(start_position_var, position))

def append_additional_target_to_array(pixl_array, stub_df):
    targetPlateID = "Additional"+plate_type_var.get()+"Plate"
    plateTypeConversion = {'Agar': 'SBS', 'Multiwell': 'MWP'}[plate_type_var.get()]
    target_definition = pd.Series({"source" : targetPlateID, 'sourceRow' : plateTypeConversion, 'sourceCol' : format_var.get(), 'target': "Target"})

    pixl_array = pd.concat([target_definition.to_frame().T, pixl_array], ignore_index=True)
    target_positions = array_lister(format_var.get())

    targetPositionIndex = target_positions.index(start_position_var.get())

    for index, row in stub_df.iterrows():
        if index == 0: continue
        target_position = target_positions[targetPositionIndex]
        target_row = target_position[0]  # Extract the first character
        target_col = int(target_position[1:])
        targetSeries = pd.Series({"source": row['source'],"sourceRow": row['sourceRow'],"sourceCol": row['sourceCol'], "target": targetPlateID,"targetRow": target_row ,"targetCol": target_col})
        pixl_array = pd.concat([pixl_array, targetSeries.to_frame().T], ignore_index=True)
        targetPositionIndex += 1
    return pixl_array

shimadzuAdapterCoords_df = pd.read_csv("shimadzu_adapter_coordinates.csv")
shimadzuAdapterCoords_df["wellID"] = "Target " + shimadzuAdapterCoords_df["Plate"].map(str) + ", " + shimadzuAdapterCoords_df["Row"]+ shimadzuAdapterCoords_df["Column"].map(str)
#################  GUI code  #############################

root = tk.Tk()
root.title("PIXL rearray generator for Shimadzu MALDI-TOF")  # Set the title of the GUI window

# Create a label and entry for directory selection
directory_label = tk.Label(root, text="Select Colony Detection project folder:")
directory_label.pack()

directory_entry = tk.Entry(root, width=50)
directory_entry.pack()


# Create a button to trigger directory selection
directory_button = tk.Button(root, text="Browse", command=select_CD_directory)
directory_button.pack()


# Create a label and entry for well input
well_label = tk.Label(root, text="Enter matrix reservoir position in 96 well plate  e.g. A1:")
well_label.pack()




# Create the dropdown using the well positions as options
well_positions = array_lister("96")
well_var = tk.StringVar(root)
well_var.set(read_config_variable("matrix_position"))  # Default selection

well_dropdown = tk.OptionMenu(root, well_var, *well_positions)
well_dropdown.pack()


# Create a dropdown for wellID selection
wellID_label = tk.Label(root, text="Select MALDI target postion to start picking to:")
wellID_label.pack()


# Create the dropdown using the unique wellIDs as options
wellIDs = shimadzuAdapterCoords_df['wellID'].unique()
wellID_dropdown = tk.StringVar(root)
wellID_dropdown.set(read_config_variable("first_target_position"))  # Default selection

wellID_optionmenu = tk.OptionMenu(root, wellID_dropdown, *wellIDs)
wellID_optionmenu.pack()


# Create radio buttons for matrix type
matrix_label = tk.Label(root, text="Matrix application mode:")
matrix_label.pack()

matrix_var = tk.StringVar()
matrix_var.set(read_config_variable("matrix_application_mode"))  # Default selection

single_dip_radio = tk.Radiobutton(root, text="Single Dip", variable=matrix_var, value="Single Dip")
single_dip_radio.pack()

double_dip_radio = tk.Radiobutton(root, text="Double Dip (recommended)", variable=matrix_var, value="Double Dip")
double_dip_radio.pack()


# Create option to pick to seperate array
# Additional options
additional_options_var = tk.IntVar()
additional_options_checkbutton = tk.Checkbutton(root, text="Pick colony to additional target plate", variable=additional_options_var, command=show_additional_options)
additional_options_checkbutton.pack()

# Format Selection
format_var = tk.StringVar(root)
format_label = tk.Label(root, text="Select Format:")
format_var.set("96")
format_96_radiobutton = tk.Radiobutton(root, text="96", variable=format_var, value="96")
format_384_radiobutton = tk.Radiobutton(root, text="384", variable=format_var, value="384")

# Plate Type Selection
plate_type_var = tk.StringVar(root)
plate_type_label = tk.Label(root, text="Select Plate Type:")
plate_type_var.set("Agar")
plate_type_agar_radiobutton = tk.Radiobutton(root, text="Agar", variable=plate_type_var, value="Agar")
plate_type_multiwell_radiobutton = tk.Radiobutton(root, text="Multiwell", variable=plate_type_var, value="Multiwell")

# Start Position Selection
start_position_label = tk.Label(root, text="Select Start Position:")
start_position_var = tk.StringVar(root)
target_positions = array_lister(format_var.get())
start_position_var.set(target_positions[0])  # Default selection
#start_position_var.set(well_positions[0])
start_position_dropdown = tk.OptionMenu(root, start_position_var, *target_positions)




# Create a label and entry for directory selection for export

export_directory_label = tk.Label(root, text="Select a PIXL rearray export directory:")
export_directory_label.pack()

export_directory_entry = tk.Entry(root, width=50)
export_directory_entry.pack()
export_directory_entry.insert(tk.END, get_export_directory())

# Create a button to trigger directory selection
export_directory_button = tk.Button(root, text="Browse", command=select_export_directory)
export_directory_button.pack()






# Create a button to run the operation
run_button = tk.Button(root, text="Run", command=run)
run_button.pack()


# Create an output box
output_label = tk.Label(root, text="Output:")
output_label.pack()

output_text = tk.Text(root, width=50, height=10)
output_text.pack()

root.mainloop()
