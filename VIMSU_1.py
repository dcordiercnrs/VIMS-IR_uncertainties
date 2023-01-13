"""
First module: data extraction
D. Cordier, CNRS, France, January 2023
https://orcid.org/0000-0003-4515-6271
Licence: GPLv3
"""
# -----------------------------------------------------------------------------------------------------------------------------------
#
#                 Python module of data extraction from VIMS cube for IR photometric uncertainties
#
# -----------------------------------------------------------------------------------------------------------------------------------
import os.path
import numpy as np
from pyvims import VIMS
import pandas as pd
import time
import re

from VIMS_uncertainties import VIMS_uncert

class VIMS_u:
    """
    D. Cordier - January 2023.
    """
    def __init__(self, cub_list_CSV, cubes_dir, frac):
        # -------------------------------------------------------------------------------
        if os.path.isfile(cub_list_CSV):
            print (" > CSV file containing the list of cubes ---: ",  cub_list_CSV)
        else:
            print (" > The file: \"", cub_list_CSV,"\" is not available in the current directory!")
            print ("   We stop!")
            return

        self.cubes_PlotDistrib_dir = cubes_dir + '_Plot_Distrib/'
        if not os.path.exists(self.cubes_PlotDistrib_dir):
            os.makedirs(self.cubes_PlotDistrib_dir)

        # -------------------------------------------------------------------------------
        if os.path.isdir(cubes_dir):
            print (" > Directory containing the cubes ----------: ",  cubes_dir)
        else:
            print (" > The directory:",  cubes_dir, " is not available! Please create it!")
            print ("   We stop!")
            return

        # -------------------------------------------------------------------------------
        # We check if all the listed cubes are available in the directory:
        self.clist = np.loadtxt(cub_list_CSV, delimiter=",", dtype=str)
        self.clist = np.delete(self.clist, 0)
        for i, cname in enumerate(self.clist):
            fname = "C"+cname+"_ir.cub"
            if not os.path.isfile(cubes_dir+"/"+fname):
            #    print ("   - ", i, " : ", fname, " is present in '", cubes_dir ,"'")
            #else:
                print ("   - This cube is note present, we download: ", fname)
                cvims = VIMS(cname, root=cubes_dir)
                cNs   = cvims.NS # To force downloading.

        # -------------------------------------------------------------------------------
        # We set the number of VIMS channels:
        self.Nchan_VIMS = 256

        # -------------------------------------------------------------------------------
        # Fraction of cube pixels to be used:
        self.frac_px = frac

        # -------------------------------------------------------------------------------
        # We initialized the Pandas DataFrame that will contain the global data of cubes:
        #
        # Cube name : identifiant du cube.
        # Nsample   : nombre de pixels suivant l'axe 'sample' du cube.
        # Nline     : nombre de pixels suivant l'axe 'line' du cube.
        # Npix      : nombre total de pixels dans le cube.
        # Expo time : temps d'exposition du cube.
        # dT_1, dT_2, dT3 : les trois températures du "détecteur"
        # iT1, iT2  : les deux températures de "l'instrument".
        # oT1, oT2, oT3 : les trois températures de "l'optique".
        self.columns_Cubes = ['Cube name', 'Nsample', 'Nline', 'Npix', 'Expo Time', 'Ls', 'dT1', \
                              'dT2', 'dT3', 'iT1', 'iT2', 'oT1', 'oT2', 'oT3']

        # -------------------------------------------------------------------------------
        self.Cubes_DF = pd.DataFrame(data=None, columns= self.columns_Cubes)
        #
        # We initialized the Pandas DataFrame that will contain the data of 3x3 pixels blocks:
        #
        # Cube name : identifiant du cube.
        # Npav      : nombre total de pavés 3x3 dans le cube en question.
        # iPav      : indice du pavé considéré, parmi ceux du cube en cours d'utilisation.
        # s         : 'sample' du pixel central du pavé.
        # l         : 'line' du pixel central du pavé.
        # lat       : latitude du pixel central du pavé.
        # lon       : longitude du pixel central du pavé.
        # res       : résolution (diagonale ?) du pixel central.
        self.columns_Pav = ['Cube name', 'Npav', 'iPav', 's', 'l', 'lat', 'lon', 'res' ]

        # We add the relative standard deviations:
        list_of_names    = ['DIsF_'+str(i+1) for i in range(self.Nchan_VIMS)]
        self.columns_Pav = self.columns_Pav + list_of_names

        # We add the average I/F values:
        list_of_names    = ['IFav_'+str(i+1) for i in range(self.Nchan_VIMS)]
        self.columns_Pav = self.columns_Pav + list_of_names

        # We add the angular quantities:
        list_of_names    = ['Dinc', 'incAv', 'Deme', 'emeAv', 'Dphase', 'phaseAv']
        self.columns_Pav = self.columns_Pav + list_of_names

        # We initialized the Pandas DataFrame that will contain the data of 3x3 pixels blocks:
        self.Pav_DF = pd.DataFrame(data=None, columns= self.columns_Pav)
        #print(self.Pav_DF.head())

    # -----------------------------------------------------------------------------------
    def extract_3x3box (self, cubes_dir=None):
        """
        Extraction of 3x3 pixels boxes data.
        """
        list_smooth_err = np.empty((0, self.Nchan_VIMS), dtype=float)

        list_av_IF = np.array([])          # List of the average I/F, for each cube.
        list_av_Inc= np.array([])

        cube_exposure_time = np.array([])  # Cubes exposure time.
        cube_px_number = np.array([])      # Total number of cubes pixels.
        cube_exec_time = np.array([])      # Cubes processing time.

        nc = 0 # Number of cubes processed.
        Npx= 0 # Total number of pixels (i.e. over all cubes).

        tic = time.perf_counter()

        print ("")
        print (" > We have a total of '", len(self.clist), "' VIMS cubes to be processed.")
        print ("")

        print ("")

        for cname in self.clist:
            nc += 1
            tic_1 = time.perf_counter()
            #cubname_fig = re.sub(r"cub", "png", cubname) # Nom de la figure qu'on va enregistrer.
            cubname = "C"+cname+"_ir.cub"
            cubname_fig = re.sub(r"cub", "png", cubname) # Nom de la figure qu'on va enregistrer.
            #print (cubname)
            cub_VIMS        = VIMS(cubname, root=cubes_dir) # Lecture du cube dans le répertoire de stockage
            cub_VIMS_uncert = VIMS_uncert(cubname, root=cubes_dir)

            cubname = re.sub(r"_ir.cub", "", cubname)
            cubname = re.sub(r"C", "", cubname)

            # On traite le cube en tirant au sort les pavés 3x3 et en faisant les calculs nécessaires dessus :
            N_sample, N_line, Expo_time, Ls, detect_temp, instru_temp, opt_temp, \
            ns_rand, nl_rand, latC_pav, lonC_pav, res_av, log10_ectype_relat, IsF_av, ectr_inc, inc_av, \
            ectr_eme, eme_av, ectr_phase, phase_av = \
            cub_VIMS_uncert.comp_logect_pave(frac=self.frac_px, root = cubes_dir)

            # ---------------------------------------------------------------------------------
            # Construction du DataFrame concernant les données globales des cubes :
            Npix = N_sample*N_line
            ligne = [cubname] + [N_sample] + [N_line] + [Npix] + [Expo_time] + [Ls] + \
                [T for T in detect_temp] + [T for T in instru_temp] + [T for T in opt_temp]

            Cubes_DF_temp = pd.DataFrame([ligne], columns=self.columns_Cubes)      # DataFrame temporaire d'une ligne.
            self.Cubes_DF = pd.concat([self.Cubes_DF, Cubes_DF_temp], ignore_index=True) # On ajoute le DataFrame tempo. au DataFrame final

            # ---------------------------------------------------------------------------------
            # Construction du DataFrame concernant les données des paves :

            Npav = len(ns_rand)
            #print ('Npav = ', Npav)
            for iPav in range(Npav):
                s  = ns_rand[iPav]
                l  = nl_rand[iPav]
                lat= latC_pav[iPav]
                lon= lonC_pav[iPav]
                res= res_av[iPav]

                lectype_relat_Pav = log10_ectype_relat[iPav] # Pour un pavé donné : log(ec_IsF) en fonc. des canaux
                IsF_av_Pav        = IsF_av[iPav] # # Pour un pavé donné : I/F moy. en fonc. des canaux VIMS.

                eri = ectr_inc[iPav]
                i_av= inc_av[iPav]
                ere = ectr_eme[iPav]
                eav = eme_av[iPav]
                erph= ectr_phase[iPav]
                phav= phase_av[iPav]

                ligne = [cubname] + [Npav] + [iPav] + [s] + [l] + [lat] + [lon] + [res] + \
                        [DIsF  for DIsF  in lectype_relat_Pav] + [IsFav for IsFav in IsF_av_Pav] + \
                        [eri] + [i_av] + [ere]  + [eav] + [erph] + [phav]



                Pav_DF_temp = pd.DataFrame([ligne], columns=self.columns_Pav) # DataFrame temporaire d'une ligne.
                self.Pav_DF = pd.concat([self.Pav_DF, Pav_DF_temp], ignore_index=True) # On ajoute le DataFrame tempo. au DataFrame final

            # Plot of chosen box (central pixel):
            cub_VIMS_uncert.plot_pix_distri(frac=self.frac_px, root=cubes_dir, \
                                                plotdir=self.cubes_PlotDistrib_dir, figname=cubname_fig)

            Npx= Npx + cub_VIMS.NS * cub_VIMS.NL
            cube_px_number = np.append(cube_px_number, cub_VIMS.NS * cub_VIMS.NL)
            cube_exposure_time = np.append(cube_exposure_time, cub_VIMS.expo)

            cub_av_incid = np.mean(cub_VIMS.inc) # Cube average incident angle.
            cub_avIF     = self.cub_av_IF(cub_VIMS)   # Cube average I/F.


            ## # -- Détermination de la loi d'incertitude en fonction du canal, ceci pour chaque cube :
            ## cann, smoothed_fit = cub_VIMS_uncert.det_smoothed_fit(frac_px, root = cubes_dir) #


            toc_1 = time.perf_counter()
            cube_exec_time = np.append(cube_exec_time, toc_1 - tic_1)

            #print ( ' > Cube ', nc,':', cubname, ':', cubname_fig, ':', cub_VIMS.NL,'x', cub_VIMS.NS, cub_av_incid, cub_avIF)
            print ( '   - Cube ', nc,':', cubname, ':', cub_VIMS.NS * cub_VIMS.NL, ' px, ', f' processing performed in {toc_1 - tic_1:0.4f} seconds')
            Npx += 1
            #if nc == 2:
            #    break

        toc = time.perf_counter()

        print ("")
        print(f" > Cube processing performed in {toc - tic:0.4f} seconds")
        print(f" > Total number of pixels in these cubes: {Npx:} seconds")
        print ("")

        return self.Cubes_DF, self.Pav_DF

    # -----------------------------------------------------------------------------------
    def cub_av_IF (self, cube):
        """
           Compute the average I/F over the entire VIMS cube
           Parameters:
           - inputs: cube : VIMS cube
           - ouputs: the average cube I/F
        """
        list_av_IF = np.array([])
        for ss in range(cube.NS):
            for ll in range(cube.NL):
                spectre = cube[ss+1, ll+1].spectrum
                av_IF   = np.mean(spectre)
                #print (av_IF)
                list_av_IF = np.append(list_av_IF, av_IF)
        return np.mean(list_av_IF)
