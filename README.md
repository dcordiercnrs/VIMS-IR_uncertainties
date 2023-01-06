# Material for VIMS-IR uncertainties estimations

## Requirements
Basically, the programs, we make publicly available, require a recent `Python` version (3.x) and the very commonly used packages:
 - `Numpy`
 - `Matplotlib`
 - `Pandas`

together with the VIMS data management tool:
 - `PyVIMS` 
 
all these packages may be installed using the `pip` with command lines similar to `pip install pyvims`

## Data and tools

 - `VIMSuncert_cubes_list.csv`: `CSV` file containing the full list of the 149 high spatial resolution VIMS cubes analyzed.
    These cubes have a spatial resolution better than 35km/pixel.
    
 - `VIMS-IR_uncertainties_analysis_Part_ONE.ipynb`: the Jupyter notebook that extracts data from VIMS cubes.
