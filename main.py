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

def select_directory():
    pixlAppdataPath = os.path.join(os.getenv('APPDATA'),
                                   "Singer Instrument Company Limited\PIXL\Tracking")
    directory = filedialog.askdirectory(initialdir = pixlAppdataPath)
    directory_entry.delete(0, tk.END)  # Clear the existing entry
    directory_entry.insert(tk.END, directory)

def run():
    validCDPath = validate_stub_path()
    if validCDPath:
        well = well_var.get()
        starting_target = wellID_dropdown.get()
        matrix_type = matrix_var.get()
        global stub_df
        stub_df = read_stub_tsv(directory_entry.get())

        output_text.insert(tk.END, "Matrix reservoir well: {}\n".format(well))
        output_text.insert(tk.END, "Target starting position: {}\n".format(starting_target))
        output_text.insert(tk.END, "Matrix addition mode: {}\n".format(matrix_type))
        output_text.insert(tk.END, "\n")

        global pixl_array
        pixl_array = prepare_pixl_array(stub_df)
        pixl_array = append_pixl_commands_to_array(pixl_array, stub_df)

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
directory_button = tk.Button(root, text="Browse", command=select_directory)
directory_button.pack()


# Create a label and entry for well input
well_label = tk.Label(root, text="Enter matrix reservoir position in 96 well plate  e.g. A1:")
well_label.pack()

well_positions = []
for row in range(8):
    for col in range(12):
        well_positions.append("{}{}".format(chr(65 + row), col + 1))

# Create the dropdown using the well positions as options
well_var = tk.StringVar(root)
well_var.set(well_positions[0])  # Default selection

well_dropdown = tk.OptionMenu(root, well_var, *well_positions)
well_dropdown.pack()


# Create a dropdown for wellID selection
wellID_label = tk.Label(root, text="Select target postion to start picking to:")
wellID_label.pack()


# Create the dropdown using the unique wellIDs as options
wellIDs = shimadzuAdapterCoords_df['wellID'].unique()
wellID_dropdown = tk.StringVar(root)
wellID_dropdown.set(wellIDs[0])  # Default selection

wellID_optionmenu = tk.OptionMenu(root, wellID_dropdown, *wellIDs)
wellID_optionmenu.pack()


# Create radio buttons for matrix type
matrix_label = tk.Label(root, text="Matrix application mode:")
matrix_label.pack()

matrix_var = tk.StringVar()
matrix_var.set("Double Dip")  # Default selection

single_dip_radio = tk.Radiobutton(root, text="Single Dip", variable=matrix_var, value="Single Dip")
single_dip_radio.pack()

double_dip_radio = tk.Radiobutton(root, text="Double Dip (recommended)", variable=matrix_var, value="Double Dip")
double_dip_radio.pack()


# Create a button to run the operation
run_button = tk.Button(root, text="Run", command=run)
run_button.pack()


# Create an output box
output_label = tk.Label(root, text="Output:")
output_label.pack()

output_text = tk.Text(root, width=50, height=10)
output_text.pack()

root.mainloop()
