# Material for VIMS-IR uncertainties estimations

## About
The material available here is a supplementary material related to the paper 
``Photometric Uncertainties of Cassini VIMS-IR Instrument'' by Cordier, D., Seignovert, B., Le Mouélic, S. and 
Sotin, C.

## Requirements
Basically, the programs, we make publicly available, require a recent `Python` version (3.x) and the very commonly used packages:
 - `Numpy`
 - `Matplotlib`
 - `Pandas`

together with the VIMS data management tool:
 - `PyVIMS` 
 
all these packages may be installed using the `pip` with command lines similar to `pip install pyvims`

## Data
 - `VIMSuncert_cubes_list.csv`: `CSV` file containing the full list of the 149 high spatial resolution VIMS cubes analyzed.
    These cubes have a spatial resolution better than 35km/pixel.
 - `VIMS_CALCUBES/`: the directory containing all the 149 calibrated cube involved in the study. Using the list in the 
   mentioned `CSV` file, all these cubes (total size: 313MB) may be automatically downloaded from Nantes University
   repository (https://vims.univ-nantes.fr/) with the `PyVIMS` tool.
 - since the analysis relies basically on a Monte-Carlo algorithm, we provide precisely used in our study under the
   form of 2 HDF5 files:
   - `stoDFrame_CubeData_NEW.hdf5` (48 KB) containing global features of employed cubes.
   - `stoDFrame_PavData_NEW.hdf5` (79 MB) containing the data of 3x3 pixels blocks picked-up in cubes.
   this way, any colleague, can potentially reproduce exactly the work we have done.
   
## Tools
    
 - `VIMS-IR_uncertainties_analysis_Part_ONE.ipynb`: the Jupyter notebook that extracts data from VIMS cubes.

 - `VIMS-IR_uncertainties_analysis_Part_TWO.ipynb`: the Jupyter notebook that extracts data from VIMS cubes.
