# -*- coding: utf-8 -*-
"""
Created on Tue May 30 16:29:57 2023

@author: PhilipKirk
"""

import tkinter as tk
from tkinter import filedialog
import pandas as pd

def select_directory():
    directory = filedialog.askdirectory()
    directory_entry.delete(0, tk.END)  # Clear the existing entry
    directory_entry.insert(tk.END, directory)

def show_additional_options():
    if additional_options_var.get() == 1:
        format_label.pack()
        format_96_radiobutton.pack()
        format_384_radiobutton.pack()
        plate_type_label.pack()
        plate_type_agar_radiobutton.pack()
        plate_type_multiwell_radiobutton.pack()
        start_position_label.pack()
        start_position_dropdown.pack()
    else:
        format_label.pack_forget()
        format_96_radiobutton.pack_forget()
        format_384_radiobutton.pack_forget()
        plate_type_label.pack_forget()
        plate_type_agar_radiobutton.pack_forget()
        plate_type_multiwell_radiobutton.pack_forget()
        start_position_label.pack_forget()
        start_position_dropdown.pack_forget()

def run():
    well = well_var.get()
   # selected_wellID = wellID_dropdown.get()
    additional_options = additional_options_var.get()
    format_selection = format_var.get()
    plate_type_selection = plate_type_var.get()
    start_position = start_position_dropdown.get()

"""  output_text.insert(tk.END, "Well: {}\n".format(well))
  output_text.insert(tk.END, "Selected wellID: {}\n".format(selected_wellID))
  output_text.insert(tk.END, "Additional Options: {}\n".format(additional_options))
  output_text.insert(tk.END, "Format Selection: {}\n".format(format_selection))
  output_text.insert(tk.END, "Plate Type Selection: {}\n".format(plate_type_selection))
  output_text.insert(tk.END, "Start Position: {}\n".format(start_position))
  output_text.insert(tk.END, "\n")"""

root = tk.Tk()
root.title("PIXL rearray generator for Shimadzu MALDI-TOF")

# Load the shimadzuAdapterCoords_df DataFrame
shimadzuAdapterCoords_df = pd.DataFrame({'wellID': ['A1', 'A2', 'B1', 'B2', 'C1']})  # Example data

# Rest of the code...

# Create a dropdown for well selection
well_label = tk.Label(root, text="Select well position:")
well_label.pack()

# Create a list of well positions on a 96 well plate
well_positions = []
for row in range(8):
    for col in range(12):
        well_positions.append("{}{}".format(chr(65 + row), col + 1))

# Create the dropdown using the well positions as options
well_var = tk.StringVar(root)

# Rest of the code...


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



well_dropdown = tk.OptionMenu(root, well_var, *well_positions)
well_dropdown.pack()

# Additional options
additional_options_var = tk.IntVar()
additional_options_checkbutton = tk.Checkbutton(root, text="Additional Options", variable=additional_options_var, command=show_additional_options)
additional_options_checkbutton.pack()

# Format Selection
format_var = tk.StringVar(root)
format_label = tk.Label(root, text="Select Format:")
format_96_radiobutton = tk.Radiobutton(root, text="96", variable=format_var, value="96")
format_384_radiobutton = tk.Radiobutton(root, text="384", variable=format_var, value="384")

# Plate Type Selection
plate_type_var = tk.StringVar(root)
plate_type_label = tk.Label(root, text="Select Plate Type:")
plate_type_agar_radiobutton = tk.Radiobutton(root, text="Agar", variable=plate_type_var, value="Agar")
plate_type_multiwell_radiobutton = tk.Radiobutton(root, text="Multiwell", variable=plate_type_var, value="Multiwell")

# Start Position Selection
start_position_label = tk.Label(root, text="Select Start Position:")
start_position_dropdown = tk.OptionMenu(root, "A1", *well_positions)
start_position_var = tk.StringVar(root)
start_position_var.set(well_positions[0])  # Default selection

# Run Button
run_button = tk.Button(root, text="Run", command=run)
run_button.pack()

# Rest of the code...

root.mainloop()