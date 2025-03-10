# -*- coding: utf-8 -*-

"""
Created on Fri May 26 10:02:25 2023
@author: PhilipKirk

This script provides a GUI application to generate re-array files for the PIXL instrument,
specifically for preparing Shimadzu MALDI-ToF targets. It handles colony detection data,
user preferences, and generates the necessary commands for the PIXL to transfer colonies,
matrix and formic acid (optional) to the target slide or additional plates.
"""

import pandas as pd
import os
import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk
import re
import shutil
import sys
from tkinter.filedialog import askdirectory
import math

####### GUI methods #######
# Function to handle the selection of the Colony Detection directory
def select_CD_directory():
    pixlAppdataPath = os.path.join(os.getenv('APPDATA'),
                                   "Singer Instrument Company Limited\PIXL\Tracking")
    directory = filedialog.askdirectory(initialdir = pixlAppdataPath)
    directory_entry.delete(0, tk.END)  # Clear the existing entry
    directory_entry.insert(tk.END, directory)
    directory_entry.xview_moveto(1)

# Function to handle the selection of the export directory
def select_export_directory():
    export_directory = get_export_directory()
    directory = filedialog.askdirectory(initialdir = export_directory)
    export_directory_entry.delete(0, tk.END)  # Clear the existing entry
    export_directory_entry.insert(tk.END, directory)

# Function to update the start position options based on the selected format
def update_start_position_options(*args):
    format_selection = format_var.get()
    valid_positions = array_lister(format_selection)
    # Clear the current options and update with the valid positions
    additional_well_row_dropdown['menu'].delete(0, 'end')
    well_rows, well_cols = well_positions = array_lister(format_var.get(), full = True)
    for row in well_rows:
        additional_well_row_dropdown['menu'].add_command(label=row, command=tk._setit(additional_well_row_selection, row))
    additional_well_col_dropdown['menu'].delete(0, 'end')
    for col in well_cols:
        additional_well_col_dropdown['menu'].add_command(label=col, command=tk._setit(additional_well_col_selection, col))

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

    # validCDPath = split_path[-2] == "Colony Detection"
    try:
        colony_detection_dir_index = split_path.index('Colony Detection')
        project_path = os.path.join("C:\\", *split_path[1:colony_detection_dir_index + 2])
        directory_entry.delete(0, tk.END)  # Clear the existing entry
        directory_entry.insert(tk.END, project_path)
        validCDPath = True
        output_text.insert(tk.END, "Valid Colony Detection project found"+ "\n")
    except: 
        output_text.insert(tk.END, "Colony Detection project not found. Please ensure the parent folder of the project selected is 'Colony Detection'"+ "\n")
        validCDPath = False
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
    update_config_variable("adapter_option", adapter_var.get())
    update_config_variable("first_target_position", wellID_dropdown.get())

    update_config_variable("formic_acid_enable", formic_enabled_var.get())
    update_config_variable("formic_acid_position", formic_well_var.get())
    update_config_variable("formic_application_mode", formic_mode_var.get())

    update_config_variable("matrix_enable", matrix_enabled_var.get())
    update_config_variable("matrix_position", matrix_well_var.get())
    update_config_variable("matrix_application_mode", matrix_var.get())

    update_config_variable("additional_plate_enable", additional_plate_enabled_var.get())

    update_config_variable("rearry_export_directory", export_directory_entry.get())
    

# Function to get the export directory from the config.txt file
def get_export_directory():
    export_directory = read_config_variable("rearry_export_directory")
    if export_directory == "desktop": export_directory = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
    return export_directory


####### Generating Rearry methods #######

# Prepare a dataframe containing the plate definitions
def prepare_pixl_array():
    pixlArray_df = pd.DataFrame(columns=["source", "sourceRow", "sourceCol", "target", "targetRow", "targetCol"])
    s1 = pd.Series({"source" : 'reagentMWP', 'sourceRow' : "SBS", 'sourceCol' : "NONE", 'target': "Source"})
    s2 = pd.Series({"source" : 'SlideAdapter', 'sourceRow' : "SBS", 'sourceCol' : "NONE", 'target': "Target"})
    firstStubRow = stub_df.iloc[0,:]
    s3 = pd.Series({"source" : firstStubRow.source, 'sourceRow' : "-45.6", 'sourceCol' : "-67.5", 'target': ""})
    s4 = pd.Series({"source" : 'reagentMWP', 'sourceRow' : "-45.6", 'sourceCol' : "-67.5", 'target': ""})
    pixlArray_df = pd.concat([pixlArray_df, s2.to_frame().T], ignore_index=True)
    pixlArray_df = pd.concat([pixlArray_df, firstStubRow.to_frame().T], ignore_index=True)
    pixlArray_df = pd.concat([pixlArray_df, s1.to_frame().T], ignore_index=True)
    pixlArray_df = pd.concat([pixlArray_df, s3.to_frame().T], ignore_index=True)
    pixlArray_df = pd.concat([pixlArray_df, s4.to_frame().T], ignore_index=True)
    return pixlArray_df

# def append_plate_order_commands(pixlArray_df):


# Append PIXL  colony and matrix commands to the array
def append_pixl_commands_to_array(prepared_array):
    shimadzuAdapterIndex_start = int(adapterCoords_df[adapterCoords_df["wellID"]== wellID_dropdown.get()].index.values)
    availableAdapterPositions = adapterCoords_df.shape[0] - shimadzuAdapterIndex_start
    global stub_df
    if availableAdapterPositions < stub_df.shape[0]-1:
        output_text.insert(tk.END, "There are more colonies than available target positions on the MALDI-TOF adapter. Excess colonies will be ignored. \n")
        stub_df_subset = stub_df.iloc[0:availableAdapterPositions+1,:]
        stub_df = stub_df_subset
    shimadzuAdapterIndex = shimadzuAdapterIndex_start
    if formic_enabled_var.get()  == 0:
        for index, row in stub_df.iterrows():
            if index == 0: continue
            shimadzuAdapterRow = adapterCoords_df.iloc[shimadzuAdapterIndex,:]
            prepared_array = append_colony_transfer(prepared_array,row, shimadzuAdapterRow)
            if matrix_enabled_var.get() == 1:
                prepared_array = append_matrix_transfer(prepared_array, shimadzuAdapterRow)
                if (matrix_var.get() == "Double Dip"):
                    prepared_array = append_matrix_transfer(prepared_array, shimadzuAdapterRow)
            shimadzuAdapterIndex += 1
    if formic_enabled_var.get()  == 1:
        for index, row in stub_df.iterrows():
            if index == 0: continue
            shimadzuAdapterRow = adapterCoords_df.iloc[shimadzuAdapterIndex,:]
            prepared_array = append_colony_transfer(prepared_array,row, shimadzuAdapterRow)
            prepared_array = append_formic_acid_transfer(prepared_array, shimadzuAdapterRow)
            if (formic_mode_var.get() == "Double Dip"):
                prepared_array = append_formic_acid_transfer(prepared_array, shimadzuAdapterRow)
            shimadzuAdapterIndex += 1
        if matrix_enabled_var.get() == 1:
            shimadzuAdapterIndex = shimadzuAdapterIndex_start
            for index, row in stub_df.iterrows():
                if index == 0: continue
                shimadzuAdapterRow = adapterCoords_df.iloc[shimadzuAdapterIndex,:]
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

    matrix_cartesian_x = reagent_multiwell_df.loc[reagent_multiwell_df.Cardinal==matrix_well_var.get(),"CartesianX"].item()
    matrix_cartesian_y = reagent_multiwell_df.loc[reagent_multiwell_df.Cardinal==matrix_well_var.get(),"CartesianY"].item()

    if type(shimadzuAdapterRow) == pd.core.frame.DataFrame:
        shimadzuAdapterRow = shimadzuAdapterRow.squeeze(axis = 0)

    targetSeries = pd.Series({"source": "reagentMWP","sourceRow": matrix_cartesian_y,"sourceCol": matrix_cartesian_x, "target": "SlideAdapter","targetRow": shimadzuAdapterRow.loc['y'] ,"targetCol":shimadzuAdapterRow.loc['x']})
    prepared_array = pd.concat([prepared_array, targetSeries.to_frame().T], ignore_index=True)
    return prepared_array

# Append a matrix transfer command to the array
def append_formic_acid_transfer(prepared_array, shimadzuAdapterRow):

    formic_cartesian_x = reagent_multiwell_df.loc[reagent_multiwell_df.Cardinal==formic_well_var.get(),"CartesianX"].item()
    formic_cartesian_y = reagent_multiwell_df.loc[reagent_multiwell_df.Cardinal==formic_well_var.get(),"CartesianY"].item()

    if type(shimadzuAdapterRow) == pd.core.frame.DataFrame:
        shimadzuAdapterRow = shimadzuAdapterRow.squeeze(axis = 0)

    targetSeries = pd.Series({"source": "reagentMWP","sourceRow": formic_cartesian_y,"sourceCol": formic_cartesian_x, "target": "SlideAdapter","targetRow": shimadzuAdapterRow.loc['y'] ,"targetCol":shimadzuAdapterRow.loc['x']})
    prepared_array = pd.concat([prepared_array, targetSeries.to_frame().T], ignore_index=True)
    return prepared_array

# Trigger all methods required to make array and export to user defined directory
def export_pixl_array():
    pixl_array = prepare_pixl_array()
    pixl_array = append_pixl_commands_to_array(pixl_array)

    if additional_plate_enabled_var.get() == 1:
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
    targetPositionIndex = target_positions.index(additional_well_var.get())
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


def array_lister(array_format, full = False):
    if array_format == "96":
        rows = 8
        cols = 12
    elif array_format == "384":
        rows = 16
        cols = 24
    else: raise Exception("format not compatible")
    well_positions = []
    if full == False:
        for row in range(rows):
            for col in range(cols):
                well_positions.append("{}{}".format(chr(65 + row), col + 1))
        return well_positions
    if full:
            rows_list = []
            cols_list = []
            for row in range(rows):
                    rows_list.append(chr(65 + row))
            for col in range(cols):
                cols_list.append(col +1)
            return [rows_list, cols_list]

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
    if user_adapter_choice == 'Singer Instruments target adapter':
        adapterCoords_df = pd.read_csv(resource_path("shimadzu_adapter_coordinates_SI_adapter.csv"))
    adapterCoords_df["wellID"] = "Target " + adapterCoords_df["Plate"].map(str) + ", " + adapterCoords_df["Row"]+ adapterCoords_df["Column"].map(str)

# Function called when 'Run' button pressed
def run():
    validCDPath = validate_stub_path()
    if validCDPath:
        target_string_new = f"{plate_selection.get()}, {row_selection.get()}{col_selection.get()}"
        wellID_dropdown.set(target_string_new)
        formic_well_var.set(formic_well_row_selection.get()+str(formic_well_col_selection.get()))
        matrix_well_var.set(well_row_selection.get()+str(well_col_selection.get()))
        additional_well_var.set(additional_well_row_selection.get()+str(additional_well_col_selection.get()))
        adapter_coordinates(adapter_var.get())
        global stub_df
        stub_df = read_stub_tsv(directory_entry.get())
        export_pixl_array()
        if matrix_enabled_var.get() ==  0 | formic_enabled_var.get()  == 0:
            output_text.insert(tk.END, "Please note, PIXL will  request that you load a MWP (named reagentMWP) even though you do not require formic acid or matrix. Please load an empty MWP when prompted.\n")
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

def split_target_row_col_string(string):
    pattern = r"Target (\d+), ([A-Z])(\d+)"
    match = re.match(pattern, string)
    if match:
        target_number = int(match.group(1))  # The number after "Target"
        letter = match.group(2)             # The letter
        final_number = int(match.group(3))  # The final number
    else:
        print("String does not match the expected pattern.")
    return(target_number, letter, final_number)

def split_row_col_string(string):
    pattern = r"([A-Z])(\d+)"
    # Perform the matching
    match = re.match(pattern, string)

    if match:
        well_row = match.group(1)  # The number after "Target"
        well_col = int(match.group(2))             # The letter
    else:
        print(f"String {default_well} does not match the expected pattern.")
    return (well_row, well_col)
####### Main #######

# Regardless of which adapter is in use, this df is used to pull the wellIDs
# for the GUI.
shimadzuAdapterCoords_df = pd.read_csv(resource_path("shimadzu_adapter_coordinates_Precision_adapter.csv"))
shimadzuAdapterCoords_df["wellID"] = "Target " + shimadzuAdapterCoords_df["Plate"].map(str) + ", " + shimadzuAdapterCoords_df["Row"]+ shimadzuAdapterCoords_df["Column"].map(str)
reagent_multiwell_df = pd.read_csv(resource_path("thermo_nunc_96_coordinates.csv"))


# Dictionary of variables that are cached in config.txt with default values
template_variables = {
"rearry_export_directory": "desktop",
"first_target_position": "Target 1, A1",
"formic_acid_enable" : "0",
"formic_acid_position": "A2",
"formic_application_mode": "Single Dip",
"matrix_enable" : "0",
"matrix_position": "A1",
"matrix_application_mode": "Double Dip",
"additional_plate_enable" : "0",
"adapter_option": "Shimadzu Precision adapter",

}

#################  GUI code  #############################

# Create the root window
root = tk.Tk()
root.title("PIXL re-array Generator for Shimadzu MALDI-TOF")
root.iconbitmap(resource_path("icon.ico"))

# Style setup
style = ttk.Style(root)
style.theme_use("alt")
style.configure("TButton", padding=1)
style.configure("TLabel", padding=1)

# Create a Notebook (tabbed interface)
notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True, padx=10, pady=10)

# Tab 1: Basic Settings---------------------------------------------------------------------------------------
basic_frame = ttk.Frame(notebook, padding=10)
notebook.add(basic_frame, text="Basic Settings")

# Directory selection
cdp_frame = ttk.LabelFrame(basic_frame, text="Colony Detection Project Selection", padding=10)
cdp_frame.pack(fill="x", pady=5)
cdp_label = ttk.Label(cdp_frame, text="Select Colony Detection Project Folder:")
cdp_label.grid(row=0, column=0, columnspan= 3, padx=0, pady=2, sticky="w")
directory_entry = ttk.Entry(cdp_frame, width=60)
directory_entry.grid(row=1, column=0, columnspan= 3, padx=5, pady=2)
cdp_button = ttk.Button(cdp_frame, text="Browse", command=select_CD_directory)
cdp_button.grid(row=1, column=4, padx=5, pady=2)
pattern_label = ttk.Label(cdp_frame, text="The path should match this pattern: ...Tracking\\[date]\\Colony Detection\\[project name]")
pattern_label.grid(row=2, column=0, columnspan= 5, padx=0, pady=0, sticky="w")

# Adapter Selection
adapter_frame = ttk.LabelFrame(basic_frame, text="Target Adapter Selection", padding=10)
adapter_frame.pack(fill="x", pady=5)
adapter_var = tk.StringVar(root)
adapter_options = ['Shimadzu Precision adapter', 'Singer Instruments target adapter']
adapter_var.set(read_config_variable("adapter_option"))  # Default selection
ttk.Label(adapter_frame, text="Select target adapter used to house Shimadzu targets in PIXL:").pack(anchor="w")
adapter_dropdown = ttk.OptionMenu(adapter_frame, adapter_var, read_config_variable("adapter_option"), *adapter_options)
adapter_dropdown.pack(fill="x", pady=5)


# Create the dropdown using the unique wellIDs as options
adapter_start_frame = ttk.LabelFrame(basic_frame, text="Target Adapter Start Position Selection", padding=10)
adapter_start_frame.pack(fill="x", pady=5)

target_descr_label = ttk.Label(adapter_start_frame, text="The adapter can hold up to 4 Shimadzu targets (Target 1 to 4, left to right).\nSelect the first Shimadzu target and the position to start pinning to.\nSubsequent targets will be filled from A1.")
target_descr_label.grid(row=0, column=0,columnspan=3, padx=5, pady=2,sticky="w")

target_label = ttk.Label(adapter_start_frame, text="First target")
target_label.grid(row=1, column=0, padx=5, pady=2, sticky= "w")
target_plates = shimadzuAdapterCoords_df['Plate'].unique()
formatted_plates = ["Target " + str(plate) for plate in target_plates]
plate_selection = tk.StringVar(root)

target_number, letter, final_number = split_target_row_col_string(read_config_variable("first_target_position"))
plate_selection.set("Target "+str(target_number))  # Default selection
plate_dropdown = ttk.OptionMenu(adapter_start_frame, plate_selection, "Target "+str(target_number), *formatted_plates)
plate_dropdown.grid(row=2, column=0, padx=5, pady=2)

row_label = ttk.Label(adapter_start_frame, text="Target row")
row_label.grid(row=1, column=1, padx=5, pady=2, sticky= "w")
target_rows = shimadzuAdapterCoords_df['Row'].unique()
row_selection = tk.StringVar(root)
row_selection.set(letter)  # Default selection
row_dropdown = ttk.OptionMenu(adapter_start_frame, row_selection, letter, *target_rows)
row_dropdown.grid(row=2, column=1, padx=5, pady=2)

col_label = ttk.Label(adapter_start_frame, text="Target column")
col_label.grid(row=1, column=2, padx=5, pady=2, sticky= "w")
target_cols = shimadzuAdapterCoords_df['Column'].unique()
col_selection = tk.StringVar(root)
col_selection.set(final_number)  # Default selection
col_dropdown = ttk.OptionMenu(adapter_start_frame, col_selection, final_number, *target_cols)
col_dropdown.grid(row=2, column=2, padx=5, pady=2)

target_string_new = f"{plate_selection.get()}, {row_selection.get()}{col_selection.get()}"
wellID_dropdown = tk.StringVar(root)
wellIDs = shimadzuAdapterCoords_df['wellID'].unique()

# Tab 2: Formic acid Settings---------------------------------------------------------------------------------------
formic_tab = ttk.Frame(notebook, padding=10)
notebook.add(formic_tab, text="Optional: CH₂O₂ addition")

formic_enabled_var = tk.IntVar()
formic_enabled_var.set(int(read_config_variable("formic_acid_enable")))
formic_enabled_checkbutton = ttk.Checkbutton(formic_tab, text="Enable formic acid addition", variable=formic_enabled_var)
formic_enabled_checkbutton.pack(anchor="w", pady=5)

formic_well_frame = ttk.LabelFrame(formic_tab, text="Formic Acid Reservoir Postion", padding=10)
formic_well_frame.pack(fill="x", pady=5)
formic_well_label = ttk.Label(formic_well_frame, text="Enter the well position of a 96 multwell plate that contains formic acid.\nThis will be the same multwell plate that contains matrix [if matrix addition is enabled].")
formic_well_label.grid(row=0, column=0,columnspan=7, padx=5, pady=2, sticky="w")
well_row, well_col =split_row_col_string(read_config_variable("formic_acid_position"))

well_rows, well_cols = well_positions = array_lister("96", full = True)
formic_well_row_selection = tk.StringVar(root)
formic_well_row_selection.set(well_row)
formic_well_row_dropdown = ttk.OptionMenu(formic_well_frame, formic_well_row_selection, well_row,*well_rows)
formic_well_row_dropdown.grid(row=1, column=0, padx=5, pady=2)

formic_well_col_selection = tk.StringVar(root)
formic_well_col_selection.set(well_row)
formic_well_col_dropdown = ttk.OptionMenu(formic_well_frame, formic_well_col_selection, well_col,*well_cols)
formic_well_col_dropdown.grid(row=1, column=1, padx=5, pady=2)

# well_positions = array_lister("96")
formic_well_var = tk.StringVar(root)

# Formic Application Mode
formic_mode_frame = ttk.LabelFrame(formic_tab, text="Formic Acid Application Mode", padding=10)
formic_mode_frame.pack(fill="x", pady=5)
formic_additional_col_label = ttk.Label(formic_mode_frame, text="Please select whether PIXL should pin formic acid once (Single Dip) or twice (Double Dip)\nonto the microbial material.")
formic_additional_col_label.grid(row=0, column=0, columnspan= 5, padx=5, pady=0, sticky= "w")

formic_mode_var = tk.StringVar()
formic_mode_var.set(read_config_variable("formic_application_mode"))
single_radio = ttk.Radiobutton(formic_mode_frame, text="Single Dip", variable=formic_mode_var, value="Single Dip")
single_radio.grid(row=1, column=0, padx=5, pady=2)
double_radio = ttk.Radiobutton(formic_mode_frame, text="Double Dip", variable=formic_mode_var, value="Double Dip")
double_radio.grid(row=1, column=2, padx=5, pady=2)

# Tab 3: Matrix Settings---------------------------------------------------------------------------------------
# Well Input
matrix_tab = ttk.Frame(notebook, padding=10)
notebook.add(matrix_tab, text="Optional: Matrix addition")

matrix_enabled_var = tk.IntVar()
matrix_enabled_var.set(int(read_config_variable("matrix_enable")))
matrix_enabled_checkbutton = ttk.Checkbutton(matrix_tab, text="Enable matrix addition", variable=matrix_enabled_var)
matrix_enabled_checkbutton.pack(anchor="w", pady=5)

well_frame = ttk.LabelFrame(matrix_tab, text="Matrix Reservoir Postion", padding=10)
well_frame.pack(fill="x", pady=5)
well_label = ttk.Label(well_frame, text="Enter the well position of a 96 multwell plate that contains matrix.\nThis will be the same multwell plate that contains formic acid [if formic acid addition is enabled].")
well_label.grid(row=0, column=0,columnspan=7, padx=5, pady=2, sticky="w")

well_row, well_col =split_row_col_string(read_config_variable("matrix_position"))
well_rows, well_cols = well_positions = array_lister("96", full = True)
well_row_selection = tk.StringVar(root)
well_row_selection.set(well_row)
well_row_dropdown = ttk.OptionMenu(well_frame, well_row_selection, well_row,*well_rows)
well_row_dropdown.grid(row=1, column=0, padx=5, pady=2)

well_col_selection = tk.StringVar(root)
well_col_selection.set(well_row)
well_col_dropdown = ttk.OptionMenu(well_frame, well_col_selection, well_col,*well_cols)
well_col_dropdown.grid(row=1, column=1, padx=5, pady=2)

matrix_well_var = tk.StringVar(root)

# Matrix Application Mode
matrix_frame = ttk.LabelFrame(matrix_tab, text="Matrix Application Mode", padding=10)
matrix_frame.pack(fill="x", pady=5)
additional_col_label = ttk.Label(matrix_frame, text="Please select whether PIXL should pin matrix once (Single Dip) or twice (Double Dip)\nonto the microbial material.")
additional_col_label.grid(row=0, column=0, columnspan= 5, padx=5, pady=0, sticky= "w")

matrix_var = tk.StringVar()
matrix_var.set(read_config_variable("matrix_application_mode"))
single_radio = ttk.Radiobutton(matrix_frame, text="Single Dip", variable=matrix_var, value="Single Dip")
single_radio.grid(row=1, column=0, padx=5, pady=2)
double_radio = ttk.Radiobutton(matrix_frame, text="Double Dip (recommended)", variable=matrix_var, value="Double Dip")
double_radio.grid(row=1, column=2, padx=5, pady=2)


# Tab 4: Additional plate Settings---------------------------------------------------------------------------------------
additional_frame = ttk.Frame(notebook, padding=10)
notebook.add(additional_frame, text="Optional: Additional target(s)")

# Checkbox to enable/disable additional options
additional_plate_enabled_var = tk.IntVar()
additional_plate_enabled_var.set(int(read_config_variable("additional_plate_enable")))
additional_options_checkbutton = ttk.Checkbutton(additional_frame, text="Enable Additional Plates", variable=additional_plate_enabled_var)
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
additional_start_label = ttk.Label(start_position_frame, text="Select Start Position for first target plate.\nOnce the first target plate has been filled, addtional target plates will fill from A1:")
additional_start_label.grid(row=0, column=0, columnspan= 5, padx=5, pady=2, sticky= "w")

additional_row_label = ttk.Label(start_position_frame, text="Row")
additional_row_label.grid(row=1, column=0, padx=5, pady=0, sticky= "w")
well_rows, well_cols = well_positions = array_lister(format_var.get(), full = True)
additional_well_row_selection = tk.StringVar(root)
additional_well_row_selection.set(well_rows[0])
additional_well_row_dropdown = ttk.OptionMenu(start_position_frame, additional_well_row_selection, well_rows[0],*well_rows)
additional_well_row_dropdown.grid(row=2, column=0, padx=1, pady=2, sticky= "w")

additional_col_label = ttk.Label(start_position_frame, text="Column")
additional_col_label.grid(row=1, column=1, padx=5, pady=0, sticky= "w")
additional_well_col_selection = tk.StringVar(root)
additional_well_col_selection.set(well_cols[0])
additional_well_col_dropdown = ttk.OptionMenu(start_position_frame, additional_well_col_selection, well_cols[0],*well_cols)
additional_well_col_dropdown.grid(row=2, column=1, padx=1, pady=2, sticky= "w")

additional_well_var = tk.StringVar(root)

# Tab 5: Run ---------------------------------------------------------------------------------------
run_frame = ttk.Frame(notebook, padding=10)
notebook.add(run_frame, text="Run: Generate re-array")

# PIXL Rearray Export Directory
export_directory_frame = ttk.LabelFrame(run_frame, text="Export Directory", padding=10)
export_directory_frame.pack(fill="x", pady=5)
export_desc = ttk.Label(export_directory_frame, text="Select PIXL Rearray Export Directory:")
export_desc.grid(row=0, column=0,columnspan=4, padx=5, pady=2, sticky="w")
export_directory_entry = ttk.Entry(export_directory_frame, width=50)
export_directory_entry.grid(row=1, column=0,columnspan=3, padx=5, pady=2, sticky="w")
export_directory_entry.insert(tk.END, get_export_directory())
export_button = ttk.Button(export_directory_frame, text="Browse", command=select_export_directory)
export_button.grid(row=1, column=4, padx=5, pady=2, sticky="w")

ttk.Button(run_frame, text="Generate re-array", command=run).pack(pady=10)
ttk.Label(run_frame, text="Output:").pack(anchor="w", pady=5)
output_text = scrolledtext.ScrolledText(run_frame, width=50, height=15)
output_text.pack(fill="both", expand=True, pady=5)

# Start the GUI
root.mainloop()