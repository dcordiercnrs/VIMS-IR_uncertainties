"""
Second module: data analysis.
D. Cordier, CNRS? France, January 2023
https://orcid.org/0000-0003-4515-6271 
Licence: GPL 3
"""
# -----------------------------------------------------------------------------------------------------------------------------------
#           
#                 Python module of data extraction from VIMS cube for IR photometric uncertainties
#
# -----------------------------------------------------------------------------------------------------------------------------------
import numpy as np
import matplotlib.pyplot as plt

import pandas as pd
from pyvims import VIMS

from matplotlib.image import imread
import matplotlib.colors as colors

from matplotlib.collections import LineCollection
from matplotlib.patches import Rectangle

import matplotlib.ticker as ticker
from matplotlib.ticker import AutoMinorLocator

# -----------------------------------------------------------------------------------------------------------------------------------
def plot_boxes_map(bg,my_lon,my_lat,figname):
    """
    Plot the location of 3x3 pixels boxes over a map of Titan surface.
    Intputs:
      - bg (image) ---------------: image of the background map.
      - my_lon (numpy array) -----: longitudes.
      - my_lat (numpy array) -----: latitudes.
      - figname (string) ---------: name of the PNG, PDF, ... file in which the figure is saved.
    """
    fig, ax = plt.subplots(figsize=(15*1.3, 6*1.3))

    ax.imshow(bg, extent=[360, 0, -90, 90], cmap='gray')

    mes_lon = np.reshape(my_lon, (my_lon.shape[0]))
    mes_lat = np.reshape(my_lat, (my_lat.shape[0]))

    ax.set_xlabel('Longitude (°)')
    ax.set_ylabel('Latitude  (°)')

    ax.set_xticks(np.arange(0, 361, 30))
    ax.set_yticks(np.arange(-90, 91, 30))

    ax.set_xticklabels([f'{lon}°W' for lon in np.arange(0, 361, 30)]);
    ax.set_yticklabels([f'{lat}°N' if lat > 0 else f'{-lat}°S' if lat < 0 else 'Eq.' for lat in np.arange(-90, 91, 30)])

    hmin= 0
    hmax= 50
    
    h = ax.hist2d(mes_lon, mes_lat, bins=[360,180], cmap='winter', \
                  norm=colors.PowerNorm(gamma=1. / 5.),cmin=0.001,cmax=hmax)

    # Site Huygens
    lat_Huyg = 191
    lon_Huyg = -10.6 # Latitude SUD
    ax.scatter(lat_Huyg, lon_Huyg,s=80,marker='s',c='red')

    # Cratère Selk (site Dragonfly)
    lat_Selk = 199
    lon_Selk = +7 # Latitude SUD
    ax.scatter(lat_Selk, lon_Selk,s=80,c='gold',marker='s')

    ax.set_xlim(360,0)
    cbar = fig.colorbar(h[3], ax=ax)
    ax.grid('grey')
    cbar.set_label('Density of 3x3 px boxes (Nbr box per degree$^2$)')
    
    fig.savefig(figname)
    
    return

# -----------------------------------------------------------------------------------------------------------------------------------
def VIMS_band (i0,i1):
    """
    Construction de liste de mots clefs permettant d'identifier les colonnes d'un DataFrame dans lequel
    il y a les données concernants l'incertitude relative et le I/F moyen des pavés 3x3 pixels.
    inputs:
     i0 (int): indice du premier canal VIMS à considérer.
     i1 (int): indice du dernier canal VIMS à considérer.
    outputs:
     list_DIsF  : liste de string (les mots clefs) pour l'incertitude.
     list_IsFav : idem pour I/F moyen.
    """
    list_DIsF  = []
    list_IsFav = []
    for i in range(i0,i1+1):
        key_i = 'DIsF_'+str(i)
        list_DIsF.append(key_i)
        key_i = 'IFav_'+str(i)
        list_IsFav.append(key_i)
        
    return list_DIsF, list_IsFav

# -----------------------------------------------------------------------------------------------------------------------------------
def concat_VimsChan (DF,i0,i1):
    """
    Extraction de tableaux Numpy qui sont les données des pavés, concaténées sur des bandes de canaux VIMS.
    inputs:
     DF: le DataFrame Panda avec les données des pavés.
     i0 (int): indice du premier canal VIMS à considérer.
     i1 (int): indice du dernier canal VIMS à considérer.
    outputs:
     IsFav_band: tableau Numpy avec les I/F moyen sur la bande définie par i0 et i1.
     DIsF_band:  tableau Numpy avec les incertitudes sur la bande définie par i0 et i1.
    """
    list_DIsF, list_IsFav = VIMS_band (i0,i1)
    
    DIsF_band  = DF[list_DIsF[0]].to_numpy()
    IsFav_band = DF[list_IsFav[0]].to_numpy()
    
    for disf in list_DIsF[1:]:
        npDIsF     = DF[disf].to_numpy()
        DIsF_band  = np.append(DIsF_band, npDIsF)
        
    for isfav in list_IsFav[1:]:
        npIsFav    = DF[isfav].to_numpy()
        IsFav_band = np.append(IsFav_band, npIsFav)
        
    return IsFav_band, DIsF_band

# -----------------------------------------------------------------------------------------------------------------------------------
def concat_DIsF_expo (DF_pix,DF_cube,i0,i1):
    """
    Extraction des erreurs relatives de photométrie en fonction du temps d'exposition des cubes.
    Inputs:
      - DF_pix ----: le DataFrame contenant les données sur les pavés de 3x3 pixels.
      - Df_cube ---: le DaFrame contenant les données sur les cubes eux-mêmes.
      - i0 --------: indice du canal VIMS de début de la bande spectrale considérée.
      - i1 --------: indice du canal VIMS de fin de la bande spectrale considérée.
    Outputs:
      - DIsF_moy --: Numpy array des valeurs moyennes des erreurs relatives des pavés 3x3 pixels,
                     la moyenne étant faite sur la bande considérée définie par (i0, i1) pour tous les
                     pavés 3x3
      - expo_time -: les temps d'exposition (des cubes) correspondants.
    """
    list_DIsF = VIMS_band (i0,i1) # On récupère les mots clés définissant les canaux VIMS sur lesquels
                                  # on travaille.
    DIsF_moy  = np.array([])
    expo_time = np.array([])

    cub_list = DF_cube["Cube name"].to_list() # On récupère la liste des identifiants des cubes VIMS sur
                                              # lesquels on travaille.
    for cn in cub_list:
        DIsF_band  = DF_pix[list_DIsF[0]][DF_pix['Cube name'] == cn].to_numpy()
        exp_t = float(DF_cube[DF_cube['Cube name'] == cn]['Expo Time'])

        for dband in DIsF_band:
            m = np.mean(dband)
            #print (dband, m)
            DIsF_moy  = np.append(DIsF_moy, m)
            expo_time = np.append(expo_time, exp_t)

    return DIsF_moy, expo_time

# -----------------------------------------------------------------------------------------------------------------------------------
def concat_VimsChan_lowAngDis (DF0,i0,i1,Dang):
    """
    Même chose que 'concat_VimsChan', sauf qu'on applique une condition sur les écart-types relatifs des
    angles : Dphase, Dinc, Deme, les valeurs de ces "D***" devant être inférieures à 'Dang'.
 
    inputs:
     DF0 -----------: le DataFrame Panda avec les données des pavés.
     i0 (int) ------: indice du premier canal VIMS à considérer.
     i1 (int) ------: indice du dernier canal VIMS à considérer.
     Dang (float) --: valeur max. des écart-types _relatifs_ sur les angles.
     
    outputs:
     IsFav_band ----: tableau Numpy avec les I/F moyen sur la bande définie par i0 et i1.
     DIsF_band -----:  tableau Numpy avec les incertitudes sur la bande définie par i0 et i1.
    """
    
    list_DIsF, list_IsFav = VIMS_band (i0,i1)
    
    DF         = DF0[(DF0['Dphase'] < Dang) & (DF0['Dinc'] < Dang) & (DF0['Deme'] < Dang)]

    DIsF_band  = DF[list_DIsF[0]].to_numpy()
    IsFav_band = DF[list_IsFav[0]].to_numpy()
    
    for disf in list_DIsF[1:]:
        npDIsF     = DF[disf].to_numpy()
        DIsF_band  = np.append(DIsF_band, npDIsF)
        
    for isfav in list_IsFav[1:]:
        npIsFav    = DF[isfav].to_numpy()
        IsFav_band = np.append(IsFav_band, npIsFav)
        
    return IsFav_band, DIsF_band

# -----------------------------------------------------------------------------------------------------------------------------------
def rm_NaN_Inf_nega (arrIsF,arrDIsF):
    """
    On enlève les NaN, +/-Inf et I/F négatifs dans les tableaux 'IsF_av' et 'DIsF', quand un élément d'un des deux est 
    enlevé, on enlève celui correspondant dans l'autre tableau (même s'il est ni NaN ou +/-Inf) ce qui 
    permet de garder le même nombre d'éléments.
    Inputs:
     arrIsF: tableau Numpy des IsF_av des pavés de 3x3 pixels.
     arrDIsF: tableau Numpa des incertitudes relatives de 3x3 pixels.
    Outputs:
     IsF_clean: tableau Numpy sans les NaN et +/-Inf.
     DIsF_clean: Idem.
    """
    dataF = pd.DataFrame({'IsF_av': arrIsF, 'DIsF': arrDIsF})
    dataF.replace([np.inf, -np.inf], np.nan, inplace=True)
    dataF.dropna(subset = ['IsF_av'], inplace=True)
    dataF.dropna(subset = ['DIsF'], inplace=True)
    
    #indexNames = dataF[dataF['IsF_av'] <= 0 ].index # On enlève les valeurs négatives.
    #dataF.drop(indexNames , inplace=True)
    #
    #indexNames = dataF[dataF['DIsF'] <= 0 ].index
    #dataF.drop(indexNames , inplace=True)

    dataF = dataF[dataF['IsF_av']>0]
    
    IsF_clean  = dataF['IsF_av'].to_numpy()
    DIsF_clean = dataF['DIsF'].to_numpy()
    return IsF_clean, DIsF_clean

# -----------------------------------------------------------------------------------------------------------------------------------
def IsFavBand(Pav_DF,band,Dang):
    """
    Inputs:
      - Pav_DF (Pandas DataFrame) ----: DataFrame containing data of 3x3 boxes extracted from VIMS cubes.
      - Band (list) ------------------: list specifying the properties of spectral bands used for the work.
      - Dang (float) -----------------: maximum relative standard deviation of angles between pixels in 
                                        a given 3x3 boxes.
    Outputs:
      - IsFav_band_Da (list of Numpy array) --: average I/F for each band, for all 3x3 pixels boxes.
      - DIsF_band_Da (list of Numpy array) ---: relative standard deviation of I/F for each band, for
                                                all 3x3 pixels boxes.
    """
    nbr_band = len(band)
    IsFav_band_Da = [np.array([])]*nbr_band
    DIsF_band_Da  = [np.array([])]*nbr_band

    for i in range(nbr_band):
        IsFav_band_Da[i], DIsF_band_Da[i] = concat_VimsChan_lowAngDis (Pav_DF,band[i][0],band[i][1],Dang)
   
    k=5
    #print (len(IsFav_band_Da[k]))

    # Cleaning up: we remove all the Nan and Inf present within the data:
    for i in range(nbr_band):    
        IsFav_band_Da[i], DIsF_band_Da[i] = rm_NaN_Inf_nega (IsFav_band_Da[i], DIsF_band_Da[i])
    
    #print (len(IsFav_band_Da[k]))
    
    return IsFav_band_Da, DIsF_band_Da

    #
    
# -----------------------------------------------------------------------------------------------------------------------------------
def plot_band_avIF_DIF(band,cubes_dir,cname,IsFav_band,DIsF_band,figname):
    """
    Inputs:
 #     - nbr_band (int) ----------------------: number of spectral bands considered.
      - band (list) -------------------------: contains the specification of employed spectral bands.
      - cubes_dir (string) ------------------: name of the VIMS cubes directory.
      - cname (string) ----------------------: an example
      - IsFav_band (list of numpy arrays) ---: average I/F for each band, for all 3x3 pixels boxes.
      - DIsF_band (list of numpy arrays) ----: relative standard deviation of I/F for each band, for
                                               all 3x3 pixels boxes.
      - figPDFname (string) -----------------: name of the PDF file in which the figure is saved.
    """
    # ---------------------------------------------------------------------------
    fig, (ax0,ax1) = plt.subplots(2,1,figsize=(15, 10), tight_layout=True)
    # ---------------------------------------------------------------------------
    
    nbr_band = len(band)
    cub_VIMS = VIMS('1732876622_1', root=cubes_dir)
    px = [3,4]
    cann_lambda = cub_VIMS.wvlns
    spectre = cub_VIMS[px].spectrum

    BANDS = {
        1: (band[0][0], band[0][1], band[0][2]),
        2: (band[1][0], band[1][1], band[1][2]),
        3: (band[2][0], band[2][1], band[2][2]),
        4: (band[3][0], band[3][1], band[3][2]),
        5: (band[4][0], band[4][1], band[4][2]),
        6: (band[5][0], band[5][1], band[5][2]),
    }
    #

    minor_locator = AutoMinorLocator(10)
    ax0.xaxis.set_minor_locator(minor_locator)
    minor_locator = AutoMinorLocator(5)
    ax1.xaxis.set_minor_locator(minor_locator)

    ax0.grid(True)
    ax0.set_ylim(-0.02, 0.20)

    ax0.set_xlabel('Wavelength (µm)')
    ax0.set_ylabel(r'$I/F$');

    ax0.xaxis.get_label().set_fontsize(20)
    ax0.yaxis.get_label().set_fontsize(20)
    ax0.tick_params(axis='x',labelsize=14)
    ax0.tick_params(axis='y',labelsize=14)

    #ax0.plot(cann,spectre,color='lightsteelblue')
    ax0.plot(cann_lambda,spectre,color='steelblue')
    ax0.scatter(cann_lambda,spectre,color='steelblue',s=10)

    for i, (b0, b1, color) in BANDS.items():
        w0, w1 = cub_VIMS.wvlns[b0], cub_VIMS.wvlns[b1]

        print(f'Band {i}: {b0}-{b1} | {w0:.3f}-{w1:.3f} µm')
    
        ax0.add_patch(Rectangle((w0, -0.005), w1 - w0, 0.1, edgecolor=color, facecolor='none'))
        ax0.text((w1 + w0) / 2, 0.105, i, color=color, va='center', ha='center')

    ax0.set_ylim(-0.005, None)

    # ---------------------------------------------------------------------------------------
    #
    ax1.xaxis.get_label().set_fontsize(20)
    ax1.yaxis.get_label().set_fontsize(20)
    ax1.grid(True)
    ax1.set_xlim(-0.02, 0.30)
    ax1.set_ylim(-3.2, 0.10)
    ax1.set(xlabel='Average $I/F$ over each 3x3 block', ylabel=r'$I/F$ standard deviation') 
    #

    malpha = 0.1

    for i in range(nbr_band):
        ax1.scatter(IsFav_band[i], DIsF_band[i],  color=band[i][2],       s=2, marker='.',alpha=malpha)
    #
    # ---------------------------------------------------------------------------
    # On sauvegarde dans un fichier :
    fig.savefig(figname, dpi=300, facecolor='w', edgecolor='w',
            orientation='landscape')
    
    return

