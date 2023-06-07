![](images/logo.png)

# PIXL Rearray Generator for the Shimadzu MALDI-TOF microbial ID workflow

This program generates a PIXL rearray file for a Shimadzu MALDI-TOF microbial ID workflow.\n

Users are presented with a GUI which allows them to select a Colony Detection folder
produced by PIXL and select workflow options such as starting position on the target, matrix locaition on a multiwell plate and whether they would also wish to pin to a seperate multiwell plate for downtram culturing or other uses.

## For Developers

### Prerequisites to run in developer environment

- Python 3.6 or higher
- pandas
- tkinter

### Distribution

This application is indended to be shared with users in a 'frozen' executable.
This avoids users having to install python and enables them to interact with the
application in a familiar way. The script `shimadzu-rearray-generator.py` can still
be ran within a development enviroment if required.

The distribution is constructed using `pyinstaller'. It is worth familiarsing
yourself with this module.

To create a distribution:
1. Install pyinstaller: `pip install pyinstaller'
2. In the terminal, run `pyinstaller shimadzu-rearray-generator.spec shimadzu-rearray-generator.py`
3. The `.spec` file defines, amost other things, what other files are bundled with the distribution.
4. A `dist` directory will be produced that can be deployed to customers.


## For Users
### Usage

1. Run the file `shimadzu-rearray-generator.exe`
2. Select the Colony Detection project folder by clicking the "Browse" button.
3. Enter the matrix reservoir position in the 96-well plate.
4. Select the MALDI target position to start picking to.
5. Select the matrix application mode (Single Dip or Double Dip).
6. (Optional) Check the additional options checkbox to enable additional settings.
7. Click the "Run" button to generate the PIXL rearray file.
