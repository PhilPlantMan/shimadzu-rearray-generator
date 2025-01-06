# -*- coding: utf-8 -*-
"""
Created on Fri May 26 10:02:25 2023

@author: PhilipKirk
"""

import pandas as pd
import os
import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk
import re
import shutil
import sys
from tkinter.filedialog import askdirectory



####### GUI methods #######
# Function to handle the selection of the Colony Detection directory
def select_CD_directory():
    pixlAppdataPath = os.path.join(os.getenv('APPDATA'),
                                   "Singer Instrument Company Limited\PIXL\Tracking")
    directory = filedialog.askdirectory(initialdir = pixlAppdataPath)
    directory_entry.delete(0, tk.END)  # Clear the existing entry
    directory_entry.insert(tk.END, directory)

# Function to handle the selection of the export directory
def select_export_directory():
    export_directory = get_export_directory()
    directory = filedialog.askdirectory(initialdir = export_directory)
    export_directory_entry.delete(0, tk.END)  # Clear the existing entry
    export_directory_entry.insert(tk.END, directory)

# Function to show/hide additional options based on the checkbox state
# def show_additional_options():
#     if additional_options_var.get() == 1:
#         export_directory_label.pack_forget()
#         export_directory_entry.pack_forget()
#         export_directory_button.pack_forget()
#         run_button.pack_forget()
#         output_label.pack_forget()
#         output_text.pack_forget()
#         format_label.pack()
#         format_96_radiobutton.pack()
#         format_384_radiobutton.pack()
#         start_position_label.pack()
#         start_position_dropdown.pack()
#         adapter_label.pack()
#         adapter_dropdown.pack()
#         export_directory_label.pack()
#         export_directory_entry.pack()
#         export_directory_button.pack()
#         run_button.pack()
#         output_label.pack()
#         output_text.pack()
#         format_var.trace('w', update_start_position_options)
#     else:
#         # Hide additional options
#         format_label.pack_forget()
#         format_96_radiobutton.pack_forget()
#         format_384_radiobutton.pack_forget()
#         start_position_label.pack_forget()
#         start_position_dropdown.pack_forget()

def toggle_additional_options():
    state = "normal" if additional_options_var.get() else "disabled"
    for child in additional_frame.winfo_children():
        # Only configure widgets other than the Checkbutton
        if child != additional_options_checkbutton and isinstance(child, (ttk.Entry, ttk.Button, ttk.OptionMenu, ttk.Radiobutton)):
            child.configure(state=state)



# Function to update the start position options based on the selected format
def update_start_position_options(*args):
    format_selection = format_var.get()
    valid_positions = array_lister(format_selection)
    # Clear the current options and update with the valid positions
    start_position_dropdown['menu'].delete(0, 'end')
    for position in valid_positions:
        start_position_dropdown['menu'].add_command(label=position, command=tk._setit(start_position_var, position))


####### File system methods #######
# Function to read the stub tsv file and return a DataFrame
def read_stub_tsv(path):
    files = [f for f in os.listdir(path) if re.match('.*_RearrayTemplate.tsv', f)]
    arrayPath = os.path.join(path, files[0])
    df = pd.read_csv(arrayPath, sep = '\t', header = None, names = ["source", "sourceRow", "sourceCol", "target"])
    return df

# Function to validate if the selected path is a valid Colony Detection project
def validate_stub_path():
    path = os.path.normpath(directory_entry.get())
    split_path = path.split(os.sep)
    validCDPath = split_path[-2] == "Colony Detection"
    if validCDPath: output_text.insert(tk.END, "Valid Colony Detection project found"+ "\n")
    else: output_text.insert(tk.END, "Colony Detection project not found. Please ensure the parent folder of the project selected is 'Colony Detection'"+ "\n")
    return validCDPath

# Function to create a generic config.txt to store user choices
def createConfig():
    dirPath = os.path.join(os.getenv('APPDATA'),
                               "Singer Instrument Company Limited\PIXL_MALDI_Rearray")
    if not os.path.isdir(dirPath):
        os.makedirs(dirPath)

    config_file = os.path.join(dirPath,"config.txt")


    try:
        with open(config_file, "w") as file:
            for variable, default_value in template_variables.items():
                file.write(f"{variable} = {default_value}\n")

    except Exception as e:
        print(f"Error: Failed to create config template. {str(e)}")

# Function to add any missing varibales in config.txt file stored in Appdata
# This is required as any updates to the software need to account for new
# missing variables in the original config
def add_missing_config_variable(variable_name):
    config_file = os.path.join(os.getenv('APPDATA'),
                                   "Singer Instrument Company Limited\PIXL_MALDI_Rearray","config.txt")
    try:
        with open(config_file, 'a') as file:
            file.write(f"{variable_name} = {template_variables[variable_name]}\n")

    except Exception as e:
        print(f"Error: Failed to append to config. {str(e)}")

# Function to read a variable from the config.txt file stored in Appdata
def read_config_variable(variable_name):
    config_file = os.path.join(os.getenv('APPDATA'),
                                   "Singer Instrument Company Limited\PIXL_MALDI_Rearray","config.txt")
    try:
        with open(config_file, "r") as file:
            for line in file:
                if line.startswith(variable_name):
                    value = line.split("=")[1].strip()
                    return value
        add_missing_config_variable(variable_name)
        return(template_variables[variable_name])

    except FileNotFoundError:
        createConfig()
        return None

# Function to update a variable from config.txt
def update_config_variable(variable_name, new_value):
    config_file = os.path.join(os.getenv('APPDATA'),
                                   "Singer Instrument Company Limited\PIXL_MALDI_Rearray","config.txt")
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

# Function to update all variabled in config.txt
def update_config_all():
    update_config_variable("matrix_position", well_var.get())
    update_config_variable("first_target_position", wellID_dropdown.get())
    update_config_variable("matrix_application_mode", matrix_var.get())
    update_config_variable("rearry_export_directory", export_directory_entry.get())
    update_config_variable("adapter_option", adapter_var.get())

# Function to get the export directory from the config.txt file
def get_export_directory():
    export_directory = read_config_variable("rearry_export_directory")
    if export_directory == "desktop": export_directory = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
    return export_directory


####### Generating Rearry methods #######

# Prepare a dataframe containing the plate definitions
def prepare_pixl_array():
    pixlArray_df = pd.DataFrame(columns=["source", "sourceRow", "sourceCol", "target", "targetRow", "targetCol"])
    s1 = pd.Series({"source" : 'matrixMWP', 'sourceRow' : "SBS", 'sourceCol' : "NONE", 'target': "Source"})
    s2 = pd.Series({"source" : 'SlideAdapter', 'sourceRow' : "SBS", 'sourceCol' : "NONE", 'target': "Target"})
    firstStubRow = stub_df.iloc[0,:]
    s3 = pd.Series({"source" : firstStubRow.source, 'sourceRow' : "-45.6", 'sourceCol' : "-67.5", 'target': ""})
    s4 = pd.Series({"source" : 'matrixMWP', 'sourceRow' : "-45.6", 'sourceCol' : "-67.5", 'target': ""})
    pixlArray_df = pd.concat([pixlArray_df, s1.to_frame().T], ignore_index=True)
    pixlArray_df = pd.concat([pixlArray_df, s2.to_frame().T], ignore_index=True)
    pixlArray_df = pd.concat([pixlArray_df, firstStubRow.to_frame().T], ignore_index=True)
    pixlArray_df = pd.concat([pixlArray_df, s3.to_frame().T], ignore_index=True)
    pixlArray_df = pd.concat([pixlArray_df, s4.to_frame().T], ignore_index=True)
    return pixlArray_df

# Append PIXL  colony and matrix commands to the array
def append_pixl_commands_to_array(prepared_array):
    shimadzuAdapterIndex = int(adapterCoords_df[adapterCoords_df["wellID"]== wellID_dropdown.get()].index.values)
    availableAdapterPositions = adapterCoords_df.shape[0] - shimadzuAdapterIndex
    global stub_df
    if availableAdapterPositions < stub_df.shape[0]-1:
        output_text.insert(tk.END, "There are more colonies than available target positions on the MALDI-TOF adapter. Excess colonies will be ignored. \n")
        stub_df_subset = stub_df.iloc[0:availableAdapterPositions+1,:]
        stub_df = stub_df_subset
    for index, row in stub_df.iterrows():
        if index == 0: continue
        shimadzuAdapterRow = adapterCoords_df.iloc[shimadzuAdapterIndex,:]
        prepared_array = append_colony_transfer(prepared_array,row, shimadzuAdapterRow)
        prepared_array = append_matrix_transfer(prepared_array, shimadzuAdapterRow)
        if (matrix_var.get() == "Double Dip"):
            prepared_array = append_matrix_transfer(prepared_array, shimadzuAdapterRow)
        shimadzuAdapterIndex += 1
    return prepared_array

# Append a colony transfer command to the array
def append_colony_transfer(prepared_array, stubRow, shimadzuAdapterRow):
    if type(shimadzuAdapterRow) == pd.core.frame.DataFrame:
        shimadzuAdapterRow = shimadzuAdapterRow.squeeze(axis = 0)
    targetSeries = pd.Series({"source": stubRow['source'],"sourceRow": stubRow['sourceRow'],"sourceCol": stubRow['sourceCol'], "target": "SlideAdapter","targetRow": shimadzuAdapterRow.loc['y'] ,"targetCol":shimadzuAdapterRow.loc['x']})
    prepared_array = pd.concat([prepared_array, targetSeries.to_frame().T], ignore_index=True)
    return prepared_array

# Append a matrix transfer command to the array
def append_matrix_transfer(prepared_array, shimadzuAdapterRow):

    matrix_cartesian_x = matrix_multiwell_df.loc[matrix_multiwell_df.Cardinal==well_var.get(),"CartesianX"].item()
    matrix_cartesian_y = matrix_multiwell_df.loc[matrix_multiwell_df.Cardinal==well_var.get(),"CartesianY"].item()

    if type(shimadzuAdapterRow) == pd.core.frame.DataFrame:
        shimadzuAdapterRow = shimadzuAdapterRow.squeeze(axis = 0)

    targetSeries = pd.Series({"source": "matrixMWP","sourceRow": matrix_cartesian_y,"sourceCol": matrix_cartesian_x, "target": "SlideAdapter","targetRow": shimadzuAdapterRow.loc['y'] ,"targetCol":shimadzuAdapterRow.loc['x']})
    prepared_array = pd.concat([prepared_array, targetSeries.to_frame().T], ignore_index=True)
    return prepared_array

# Trigger all methods required to make array and export to user defined directory
def export_pixl_array():
    pixl_array = prepare_pixl_array()
    pixl_array = append_pixl_commands_to_array(pixl_array)

    if additional_options_var.get() == 1:
        pixl_array = append_additional_target_to_array(pixl_array)

    project_name = os.path.basename(directory_entry.get())
    array_path = os.path.join(export_directory_entry.get(), project_name + "_MALDI_Rearray.csv")
    pixl_array.to_csv(array_path, header = False, index = False)

# Function for addition target plate: prepend plate deinition and append PIXL commands
def append_additional_target_to_array(pixl_array):

    def addAdditionalTargetDefinition(plate_number, pixl_array):
        targetPlateID = "AdditionalMWPTarget{}".format(plate_number)
        target_definition = pd.Series({"source" : targetPlateID, 'sourceRow' : "MWP", 'sourceCol' : format_var.get(), 'target': "Target"})
        pixl_array = pd.concat([target_definition.to_frame().T, pixl_array], ignore_index=True)
        return(pixl_array)

    numAdditionalTargetPlates = 1
    target_positions = array_lister(format_var.get())
    targetPositionIndex = target_positions.index(start_position_var.get())
    target_positions = target_positions[targetPositionIndex:]
    target_plates_list = [numAdditionalTargetPlates] * len(target_positions)

    pixl_array = addAdditionalTargetDefinition(numAdditionalTargetPlates, pixl_array)

    while len(target_positions) < stub_df.shape[0]:
       numAdditionalTargetPlates += 1
       new_positions = array_lister(format_var.get())
       target_positions.extend(new_positions)
       target_plates_list.extend([numAdditionalTargetPlates] * len(new_positions))
       pixl_array = addAdditionalTargetDefinition(numAdditionalTargetPlates, pixl_array)

    #plateTypeConversion = {'Agar': 'SBS', 'Multiwell': 'MWP'}[plate_type_var.get()]
    for index, row in stub_df.iterrows():
        if index == 0: continue
        targetPlateID = "AdditionalMWPTarget{}".format(target_plates_list[index - 1])
        target_position = target_positions[index - 1]
        target_row = target_position[0]  # Extract the first character
        target_col = int(target_position[1:])
        targetSeries = pd.Series({"source": row['source'],"sourceRow": row['sourceRow'],"sourceCol": row['sourceCol'], "target": targetPlateID,"targetRow": target_row ,"targetCol": target_col})
        pixl_array = pd.concat([pixl_array, targetSeries.to_frame().T], ignore_index=True)
    return pixl_array


####### Other methods #######
# Function to create a list of cardinal coordinates for a "96" or "384" array
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

def upload_pinning_profile():
    profile_dest_path = os.path.join(os.getenv('APPDATA'),
                                     "Singer Instrument Company Limited",
                                     "PIXL", "Pinning Profiles", "User",
                                     "MALDITOF-PINNING-PROFILE.xml")
    if os.path.exists(profile_dest_path) == False:
        output_text.insert(tk.END, "\nNo Pinning profile detected. One has been created.\nPlease restart PIXL (You should only see this prompt on the first time running this app)\n")
    profile_src_path = resource_path("MALDITOF-PINNING-PROFILE.xml")
    shutil.copy(profile_src_path, profile_dest_path)

def adapter_coordinates(user_adapter_choice):
    global adapterCoords_df
    if user_adapter_choice == 'Shimadzu Precision adapter':
        adapterCoords_df = pd.read_csv(resource_path("shimadzu_adapter_coordinates_Precision_adapter.csv"))
    if user_adapter_choice == 'SI adapter':
        adapterCoords_df = pd.read_csv(resource_path("shimadzu_adapter_coordinates_SI_adapter.csv"))
    adapterCoords_df["wellID"] = "Target " + adapterCoords_df["Plate"].map(str) + ", " + adapterCoords_df["Row"]+ adapterCoords_df["Column"].map(str)

# Function called when 'Run' button pressed
def run():
    validCDPath = validate_stub_path()
    if validCDPath:
        adapter_coordinates(adapter_var.get())
        global stub_df
        stub_df = read_stub_tsv(directory_entry.get())
        export_pixl_array()
        output_text.insert(tk.END, "Success! PIXL rearry file exported\n")
        update_config_all()
        output_text.insert(tk.END, "\n")
        upload_pinning_profile()


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

####### Main #######

# Regardless of which adapter is in use, this df is used to pull the wellIDs
# for the GUI.
shimadzuAdapterCoords_df = pd.read_csv(resource_path("shimadzu_adapter_coordinates_Precision_adapter.csv"))
shimadzuAdapterCoords_df["wellID"] = "Target " + shimadzuAdapterCoords_df["Plate"].map(str) + ", " + shimadzuAdapterCoords_df["Row"]+ shimadzuAdapterCoords_df["Column"].map(str)

matrix_multiwell_df = pd.read_csv(resource_path("thermo_nunc_96_coordinates.csv"))


# Dictionary of variables that are cached in config.txt with default values
template_variables = {
"rearry_export_directory": "desktop",
"first_target_position": "Target 1, A1",
"matrix_application_mode": "Double Dip",
"matrix_position": "A1",
"adapter_option": "Shimadzu Precision adapter"
}

#################  GUI code  #############################

# root = tk.Tk()
# root.title("PIXL rearray generator for Shimadzu MALDI-TOF")  # Set the title of the GUI window
# root.iconbitmap(resource_path("icon.ico"))

# # Style setup
# style = ttk.Style(root)
# style.theme_use("clam")  # 'clam', 'alt', 'default', 'classic' are built-in themes
# style.configure("TButton", padding=6)
# style.configure("TLabel", padding=5)

# # Create main frame
# main_frame = ttk.Frame(root, padding="10")
# main_frame.grid(row=0, column=0, sticky="NSEW")

# # Create a label and entry for directory selection
# directory_label = tk.Label(root, text="Select Colony Detection project folder:")
# directory_label.pack()
# directory_entry = tk.Entry(root, width=50)
# directory_entry.pack()

# # Create a button to trigger directory selection
# directory_button = tk.Button(root, text="Browse", command=select_CD_directory)
# directory_button.pack()

# # Adapter Selection
# adapter_label = tk.Label(root, text="Select adapter (default is Shimadzu Precision adapter)")
# adapter_label.pack()
# adapter_var = tk.StringVar(root)
# adapter_options = ['Shimadzu Precision adapter', 'SI adapter']
# adapter_var.set(read_config_variable("adapter_option"))  # Default selection
# adapter_dropdown = tk.OptionMenu(root, adapter_var, *adapter_options)
# adapter_dropdown.pack()

# # Create a dropdown for wellID selection
# wellID_label = tk.Label(root, text="Select MALDI target postion to start picking to:")
# wellID_label.pack()

# # Create the dropdown using the unique wellIDs as options
# wellIDs = shimadzuAdapterCoords_df['wellID'].unique()
# wellID_dropdown = tk.StringVar(root)
# wellID_dropdown.set(read_config_variable("first_target_position"))  # Default selection
# wellID_optionmenu = tk.OptionMenu(root, wellID_dropdown, *wellIDs)
# wellID_optionmenu.pack()

# # Create a label and entry for well input
# well_label = tk.Label(root, text="Enter matrix reservoir position in 96 well plate  e.g. A1:")
# well_label.pack()

# # Create the dropdown using the well positions as options
# well_positions = array_lister("96")
# well_var = tk.StringVar(root)
# well_var.set(read_config_variable("matrix_position"))  # Default selection
# well_dropdown = tk.OptionMenu(root, well_var, *well_positions)
# well_dropdown.pack()

# # Create radio buttons for matrix type
# matrix_label = tk.Label(root, text="Matrix application mode:")
# matrix_label.pack()
# matrix_var = tk.StringVar()
# matrix_var.set(read_config_variable("matrix_application_mode"))  # Default selection
# single_dip_radio = tk.Radiobutton(root, text="Single Dip", variable=matrix_var, value="Single Dip")
# single_dip_radio.pack()
# double_dip_radio = tk.Radiobutton(root, text="Double Dip (recommended)", variable=matrix_var, value="Double Dip")
# double_dip_radio.pack()

# # Create option to pick to seperate array
# # Additional options
# additional_options_var = tk.IntVar()
# additional_options_checkbutton = tk.Checkbutton(root, text="Pick colony to additional target plate", variable=additional_options_var, command=show_additional_options)
# additional_options_checkbutton.pack()

# # Format Selection
# format_var = tk.StringVar(root)
# format_label = tk.Label(root, text="Select Format:")
# format_var.set("96")
# format_96_radiobutton = tk.Radiobutton(root, text="96", variable=format_var, value="96")
# format_384_radiobutton = tk.Radiobutton(root, text="384", variable=format_var, value="384")

# # Start Position Selection
# start_position_label = tk.Label(root, text="Select Start Position:")
# start_position_var = tk.StringVar(root)
# target_positions = array_lister(format_var.get())
# start_position_var.set(target_positions[0])  # Default selection
# start_position_dropdown = tk.OptionMenu(root, start_position_var, *target_positions)

# # Create a label and entry for directory selection for export
# export_directory_label = tk.Label(root, text="Select a PIXL rearray export directory:")
# export_directory_label.pack()
# export_directory_entry = tk.Entry(root, width=50)
# export_directory_entry.pack()
# export_directory_entry.insert(tk.END, get_export_directory())

# # Create a button to trigger directory selection
# export_directory_button = tk.Button(root, text="Browse", command=select_export_directory)
# export_directory_button.pack()

# # Create a button to run the operation
# run_button = tk.Button(root, text="Run", command=run)
# run_button.pack()

# # Create an output box
# output_label = tk.Label(root, text="Output:")
# output_label.pack()
# output_text = tk.scrolledtext.ScrolledText(root, width=50, height=10)
# output_text.pack()

# root.mainloop()

# Create the root window
root = tk.Tk()
root.title("PIXL Rearray Generator for Shimadzu MALDI-TOF")
root.geometry("600x700")
root.iconbitmap(resource_path("icon.ico"))

# Style setup
style = ttk.Style(root)
style.theme_use("alt")
style.configure("TButton", padding=6)
style.configure("TLabel", padding=5)

# Create a Notebook (tabbed interface)
notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True, padx=10, pady=10)

# Tab 1: Basic Settings
basic_frame = ttk.Frame(notebook, padding=10)
notebook.add(basic_frame, text="Basic Settings")

# Directory selection
ttk.Label(basic_frame, text="Select Colony Detection Project Folder:").pack(anchor="w", pady=2)
directory_entry = ttk.Entry(basic_frame, width=50)
directory_entry.pack(fill="x", pady=5)
ttk.Button(basic_frame, text="Browse", command=select_CD_directory).pack(anchor="e", pady=5)

# Adapter Selection
adapter_frame = ttk.LabelFrame(basic_frame, text="Adapter Selection", padding=10)
adapter_frame.pack(fill="x", pady=5)
adapter_var = tk.StringVar(root)
adapter_options = ['Shimadzu Precision adapter', 'SI adapter']
adapter_var.set(read_config_variable("adapter_option"))  # Default selection
ttk.Label(adapter_frame, text="Select adapter:").pack(anchor="w")
adapter_dropdown = ttk.OptionMenu(adapter_frame, adapter_var, *adapter_options)
adapter_dropdown.pack(fill="x", pady=5)


# # Create the dropdown using the unique wellIDs as options
adapter_start_frame = ttk.LabelFrame(basic_frame, text="Adapter Start position Selection", padding=10)
adapter_start_frame.pack(fill="x", pady=5)
wellIDs = shimadzuAdapterCoords_df['wellID'].unique()
wellID_dropdown = tk.StringVar(root)
wellID_dropdown.set(read_config_variable("first_target_position"))  # Default selection
wellID_optionmenu = ttk.OptionMenu(adapter_start_frame, wellID_dropdown, *wellIDs)
wellID_optionmenu.pack(fill="x", pady=5)


# Well Input
well_frame = ttk.LabelFrame(basic_frame, text="Well Selection", padding=10)
well_frame.pack(fill="x", pady=5)
ttk.Label(well_frame, text="Enter matrix reservoir position (e.g., A1):").pack(anchor="w")
well_positions = array_lister("96")
well_var = tk.StringVar(root)
well_var.set(read_config_variable("matrix_position"))
well_dropdown = ttk.OptionMenu(well_frame, well_var, *well_positions)
well_dropdown.pack(fill="x", pady=5)

# Matrix Application Mode
matrix_frame = ttk.LabelFrame(basic_frame, text="Matrix Application Mode", padding=10)
matrix_frame.pack(fill="x", pady=5)
matrix_var = tk.StringVar()
matrix_var.set(read_config_variable("matrix_application_mode"))
ttk.Radiobutton(matrix_frame, text="Single Dip", variable=matrix_var, value="Single Dip").pack(anchor="w")
ttk.Radiobutton(matrix_frame, text="Double Dip (recommended)", variable=matrix_var, value="Double Dip").pack(anchor="w")

# PIXL Rearray Export Directory
export_directory_frame = ttk.LabelFrame(basic_frame, text="Export Directory", padding=10)
export_directory_frame.pack(fill="x", pady=5)
ttk.Label(export_directory_frame, text="Select PIXL Rearray Export Directory:").pack(anchor="w")
export_directory_entry = ttk.Entry(export_directory_frame, width=50)
export_directory_entry.pack(fill="x", pady=5)
export_directory_entry.insert(tk.END, get_export_directory())
ttk.Button(export_directory_frame, text="Browse", command=select_export_directory).pack(anchor="e", pady=5)

# Tab 2: Additional Options
additional_frame = ttk.Frame(notebook, padding=10)
notebook.add(additional_frame, text="Additional target(s)")


# Checkbox to enable/disable additional options
additional_options_var = tk.IntVar()
additional_options_checkbutton = ttk.Checkbutton(additional_frame, text="Enable Additional Plates", variable=additional_options_var, command=toggle_additional_options)
additional_options_checkbutton.pack(anchor="w", pady=5)


# Format Selection
format_var = tk.StringVar(root)
format_var.set("96")
format_frame = ttk.LabelFrame(additional_frame, text="Plate Format", padding=10)
format_frame.pack(fill="x", pady=10)
ttk.Label(format_frame, text="Select Format:").pack(anchor="w")
ttk.Radiobutton(format_frame, text="96", variable=format_var, value="96").pack(anchor="w")
ttk.Radiobutton(format_frame, text="384", variable=format_var, value="384").pack(anchor="w")
format_var.trace('w', update_start_position_options)

# Start Position Selection
start_position_frame = ttk.LabelFrame(additional_frame, text="Start Position", padding=10)
start_position_frame.pack(fill="x", pady=10)
start_position_var = tk.StringVar(root)
target_positions = array_lister(format_var.get())
start_position_var.set(target_positions[0])  # Default selection
ttk.Label(start_position_frame, text="Select Start Position:").pack(anchor="w")
start_position_dropdown = ttk.OptionMenu(start_position_frame, start_position_var, *target_positions)
start_position_dropdown.pack(fill="x", pady=5)

# Initially disable additional options
additional_options_var.set(0)
toggle_additional_options()

# Tab 3: Run and Output
run_frame = ttk.Frame(notebook, padding=10)
notebook.add(run_frame, text="Run: Generate re-array")

ttk.Button(run_frame, text="Generate re-array", command=run).pack(pady=10)
ttk.Label(run_frame, text="Output:").pack(anchor="w", pady=5)
output_text = scrolledtext.ScrolledText(run_frame, width=50, height=15)
output_text.pack(fill="both", expand=True, pady=5)

# Start the GUI
root.mainloop()