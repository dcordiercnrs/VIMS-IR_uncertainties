# Material for VIMS-IR uncertainties estimations

## About
The material available here is a supplementary material related to the paper 
``*Photometric Uncertainties of Cassini VIMS-IR Instrument*'' by Cordier, D., Seignovert, B., Le Mouélic, S. and 
Sotin, C.

 - Daniel Cordier      https://orcid.org/0000-0003-4515-6271
 - Benoît Seignovert   https://orcid.org/0000-0001-6533-275X
 - Stéphane Le Mouélic https://orcid.org/0000-0001-5260-1367
 - Christophe Sotin    https://orcid.org/0000-0003-3947-1072
 
The main goal of this work is to estimate photometric uncertainties remaining in VIMS-IR cubes after calibration using
USGS ISIS3 tool (https://isis.astrogeology.usgs.gov), the employed method relies on the definition of a collection of
3x3 pixels picked-up in each considered cube as it is summarized in the following sketch:

<center>
<img src="fig/scheme_VIMS_CUBE_SMALL.png">
</center>

within each individual "block" or "box", for a given spectral channel, the variability of photometric quantities is computed. 
The mean relative variability gives an approximation of uncertainties.

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
   form of 2 HDF5 files available in the directory `ANALYSIS_HDF5/`:
   - `stoDFrame_CubeData_NEW.hdf5` (48 KB) containing global features of employed cubes.
   - `stoDFrame_PavData_NEW.hdf5` (79 MB) containing the data of 3x3 pixels blocks picked-up in cubes.
   this way, any colleague, can potentially reproduce exactly the work we have done. Each of these compressed file contains
   a `Pandas` *DataFrame* which can be read and use *as it* in provided Jupyter notebooks. Of course, the interested reader
   can generate his/her own `HF5` file.
   
## Tools
The global analysis process is split into 2 steps:
 1. the random choice of 3x3 boxes in the cubes and the record of extracted data, stored in Pandas *DataFrames*, in
    `HDF5` files. This step can be accomplished with the Python Jupyter notebook:
    - `VIMS-IR_uncert_Part_ONE.ipynb`
    
    An example of spatial distribution of 3x3 boxes is reported in the following map of Titan surface, the colored
    encoding represents the surface density of chosen boxes:
    <center>
    <img src="fig/distri_map_boxes.png">
    </center>
    
    For memory, the Huygens landing site has been marked with a red square, while Selk crater
    (planned to be explored by [Dragonfly](https://dragonfly.jhuapl.edu)) is tagged with a yellow square. 
    Titan surface mosaic a credit: NASA/JPL-Caltech/Univ. Arizona
    a https://photojournal.jpl.nasa.gov/catalog/PIA22770

 2. the data analysis strictly speaking, which can be done with the second Python Jupyter notebook:
    - `VIMS-IR_uncert_Part_TWO.ipynb`
