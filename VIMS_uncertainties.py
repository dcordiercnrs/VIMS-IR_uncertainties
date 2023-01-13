"""
Module d'estimation des incertitudes sur des cubes VIMS.
Version du 6 octobre 2020.
D. Cordier, CNRS, France
https://orcid.org/0000-0003-4515-6271
Licence: GPLv3
"""
# ------------------------------------------------------------------------------------
import datetime  # Pour avoir la date et l'heure.
# Générateur de nombres pseudo-aléatoires pour le tirage au sort des pixels
import random as rand
# Ici pour sortir du programme en cas d'erreur :
import sys

# L'inévitable bibliothèque 'Numpy' :
import numpy as np

# Pour pouvoir faire de belles figures :
import matplotlib
import matplotlib.pyplot as plt

# On importer la classe 'VIMS' :
from pyvims import VIMS

# Pour pouvoir faire de l'interpolation "smoothée" avec des splines :
from scipy.interpolate import UnivariateSpline

# Pour pouvoir calculer la longitude solaire du cube :
from titan import orbit

# ------------------------------------------------------------------------------------
# Définition de la classe 'VIMS_uncert' qui hérite de 'VIMS' :
class VIMS_uncert(VIMS):
    """Classe héritant de la classe 'VIMS' et proposant en plus des méthodes d'estimation d'incertitudes"""

    # --------------------------------------------------------------------------------
    def nbpix_util(self, root='.'):
        """Calculate the number of usefull pixels in a cube.

        Determine the number of pixels that could be chosen,
        given that those along the cude side cannot be taken
        since we are using sets of 3x3 pixels, centered on each
        randomly chosen pixels.

        -------------------------
        |   |   |   |   |   |   |
        -------------------------
        |   | x | x | x | x |   |
        -------------------------
        |   | x | x | x | x |   |
        -------------------------
        |   | x | x | x | x |   |
        -------------------------
        |   |   |   |   |   |   |
        -------------------------

        Returns
        -------
        int
            n_sample : n. sample
            n_line   : n. line
            n_util   : Number of usefull pixels.

        """

        cube = VIMS(self.img_id, root=root)
        nbpix= cube.NP
        n_sample= cube.NS
        n_line  = cube.NL
        n_util  = nbpix - (2*n_sample + 2 * (n_line-2)) # On retire le nbr de pixels sur les bords du cube.
        return n_sample, n_line, n_util

    # --------------------------------------------------------------------------------
    def choice_pix(self,frac,root='.'):
        """
        Random choise of pixels in the cube:
        > input:
            - frac: float
                    the fraction of useful pixels, must be positive and smaller than 1.
        > output: two lists giving sample et line of chosen pixels
            - ns_rand: list of indexes 'sample' for the central chosen pixels.
            - nl_rand: list of indexes 'line' for central chosen pixels.
        """
        if frac <= 0. or frac > 1.:
            print (' > Problem in "VIMS_uncert": frac bad value!')
            sys.exit('we stop')
        n_sample, n_line, n_util= self.nbpix_util(root)
        n_pix = int(frac*n_util)


        #ns_rand = np.array([rand.randrange(2, n_sample) for i in range(n_pix)])
        #nl_rand = np.array([rand.randrange(2, n_line)   for i in range(n_pix)])

        ns_rand = np.array([np.random.randint(2, n_sample) for i in range(n_pix)])
        nl_rand = np.array([np.random.randint(2, n_line)   for i in range(n_pix)])

        #print (frac, n_sample, n_line, n_util, n_pix, '\n\n', ns_rand, '\n\n', nl_rand)

        #print ('> Dans choice_pix : ', n_sample, n_line, ' et les tableaux : ', ns_rand, nl_rand)
        return ns_rand, nl_rand

    # --------------------------------------------------------------------------------
    def plot_pix_distri(self,frac, root='.', plotdir= '.', figname='Untitled.png'):
        """
        Plot, over the considered cube, of the randomly chosen pixels.
        > input:
            - frac: the fraction of useful pixels, must be positive and smaller than 1.
        """
        ns_rand, nl_rand = self.choice_pix(frac,root)

        fig, axes = plt.subplots(sharey=True,figsize=(12, 6))
        plt.rcParams.update({'figure.max_open_warning': 0})

        self.plot(2.03, ax=axes)
        for i in  range(ns_rand.size):
            isample= ns_rand[i]
            iline  = nl_rand[i]
            axes.plot(isample, iline, 'o', color='r')

        fig.savefig(plotdir + figname)

    # --------------------------------------------------------------------------------
    def comp_logect(self,frac,root='.'):
        """
        Détermination de l'écart-type relatif en fonction du canal VIMS, ceci pour la fraction 'frac'
        de pixels choisis.
        > input:
            - frac: the fraction of useful pixels, must be positive and smaller than 1.
        > output:
            - nb_pix: number of 3x3 pixels blocks.
            - cano: list of VIMS channels.
            - log10_ectype_relat_list: list of list of computed relative standard deviations (in log10),
                  corresponding to the 'npix' 3x3 blocks.
            - spl_func_list: list of fitting function (based on splines).
        """
        nb_VIMS_channels = 256

        cano = np.array([i for i in range(nb_VIMS_channels)]) # Construction de la liste des indices des canaux VIMS.
        spl_func_list     = [] # Liste des functions de splines basées sur le fit des écart-types relatifs.
        log10_ectype_relat_list = [] # On stocke la liste des lois d'écart-type relatifs. Chaque élément de cette liste
                       # correspond à un pixel.

        # Construction des listes de coordonnées des pixels choisis :
        ns_rand, nl_rand = self.choice_pix(frac,root)
        nb_pix = ns_rand.size

        for i in  range(nb_pix):
            s = ns_rand[i]
            l = nl_rand[i]
            pixels = [ [s-1,l-1], [s,l-1], [s+1,l-1],
                       [s-1,l  ], [s,l  ], [s+1,l],
                       [s-1,l+1], [s,l+1], [s+1,l+1] ]
            # Boucle sur les canaux VIMS :
            log10_ectype_relat = np.array([])
            for can in range(nb_VIMS_channels):
                IsF_block = np.array([]) # On construit une liste avec les I/F du canal VIMS considéré,
                                         # ceci sur les 9 pixels du "pavé" considéré.
                for pix in pixels:
                    #print (pix)
                    sa = pix[0]
                    li = pix[1]
                    IsF = self[sa, li].spectrum[can]
                    IsF_block = np.append(IsF_block, IsF)
                # On calcule, pour le canal en question, l'écart-type relatif pour les 9 pixels considérés :
                #   - Rq. : on élimine les valeurs aberrantes qui surviennent pour quelques pixels, ceci en
                #           remplaçant leur écart-type relatif par "0.5"
                ectr = np.std(IsF_block)/np.mean(IsF_block) # l'écart-type relatif calculé sur le pavé de 9x9 pixels
                if (ectr > 0.) and (ectr < 1.):
                    log10_ectype_relat = np.append(log10_ectype_relat, np.log10(ectr))
                else:
                    ectr = 0.5
                    log10_ectype_relat = np.append(log10_ectype_relat, np.log10(ectr))

            # On stocke le dataset des écart-types relatifs "observés" de chaque pavé de pixels :
            log10_ectype_relat_list.append(log10_ectype_relat)

            # Construction de la fonction de fit par splines, une par pavé de pixels :
            spl = UnivariateSpline(cano, log10_ectype_relat, k=5)
            spl_func_list.append(spl)
        # On renvoit deux listes de listes, la première avec les 256 valeurs observées pour chaque
        # pavés 3x3 de pixels, l'autres avec les fonctions d'interpolation correspondantes (cette deuxième
        # liste est donc une liste de fonctions).
        return nb_pix, cano, log10_ectype_relat_list, spl_func_list

    # --------------------------------------------------------------------------------
    def plot_obs_ect(self,frac,root='.'):
        """
        Plot _all_ observed relative standard deviation read in the considered VIMS cube, using
        a set of 9x9 pixels blocks.
        > input:
            - frac: the fraction of useful pixels, must be positive and smaller than 1.
        """
        npix, cann, log10_ectype_relat_list, spl_func_list = self.comp_logect(frac)
        fig, ax = plt.subplots()
        plt.xlabel('VIMS channels')
        for ipix in range(npix):
            ax.scatter(cann, log10_ectype_relat_list[ipix])

    # --------------------------------------------------------------------------------
    def plot_fitted_ect(self,frac):
        """
        Plot all fit corresponding to all 9x9 pixels blocks.
        > input:
            - frac: the fraction of useful pixels, must be positive and smaller than 1.
        """
        npix, cann, log10_ectype_relat_list, spl_func_list = self.comp_logect(frac,root)
        fig, ax = plt.subplots()
        plt.xlabel('VIMS channels')
        plt.ylabel('Fit law, one for each VIMS pixel')
        for ispl in range(npix):
            #ax.scatter(cano, ectype_relat_list[ipix])
            spl= spl_func_list[ispl]
            ax.plot(cann, spl(cann), lw=2)

    # --------------------------------------------------------------------------------
    def det_smoothed_fit(self,frac,root='.'):
        """
        Reduce to set of nblock fitting function to only one (computing an average value
        for each VIMS channel)
        > input:
            - frac: the fraction of useful pixels, must be positive and smaller than 1.
        > output:
            - cann: list of VIMS channels
            - smoothed_fit: the values of the final fit function.
        """
        npix, cann, log10_ectype_relat_list, spl_func_list = self.comp_logect(frac,root)
        # On construit la fonction de fit "moyenne", en moyennant pour chaque canal les valeurs
        # obtenues avec chaque fit :
        smoothed_fit= np.array([]) # Création d'un array 1D vide.
        for chan in cann:
            somme= 0.
            for ispl in range(npix):
                spl= spl_func_list[ispl]
                somme= somme + spl(chan)
            moy= somme / npix
            smoothed_fit = np.append(smoothed_fit, moy)
        return cann, smoothed_fit

    # --------------------------------------------------------------------------------
    def plot_smoothFit_obs(self,frac,root='.'):
        """
        Plot the experimental relative standard deviation, plus the finale smoothed
        fitting function.
        > input:
            - frac: the fraction of useful pixels, must be positive and smaller than 1.
        """
        npix, cann, log10_ectype_relat_list, spl_func_list = self.comp_logect(frac,root)
        cann, smoothed_fit= self.det_smoothed_fit(frac,root)
        fig, ax = plt.subplots()
        plt.xlabel('VIMS channels')
        for ipix in range(npix):
            ax.scatter(cann, log10_ectype_relat_list[ipix])
        ax.plot(cann, smoothed_fit, lw=2, color='r')

    # --------------------------------------------------------------------------------
    def write_STDdevFit_output_file(self,frac,root='.'):
        """
        For a given VIMS cube and a fraction of pixel involved in our analysis
        write a text file
        """
        datetime_object = datetime.datetime.now()
        filename= self.img_id
        filename= 'VIMScubeUncert_'+filename+".out"

        # Affichage:
        print(Fore.RED  + " > On écrit le fichier de sortie : ", end='')
        print(Fore.BLUE + filename)
        print(Style.RESET_ALL)

        # Determination of the final smoothed fit function:
        can, smoothed_fit= self.det_smoothed_fit(frac,root)

        # We write the output ASCII file (which will be read by the Ratiative Transfer FORTRAN program)
        fileout = open(filename, "w")
        fileout.write("# "+str(datetime_object)+"\n")
        for i in range(can.size):
            fileout.write("%4d %16.8E \n" % (can[i]+1,smoothed_fit[i]) )
        fileout.close()

    # --------------------------------------------------------------------------------
    # ================================================================================
    # ================================================================================
    # ================================================================================
    # 5 octobre 2020 : version qui pour un cube donné sort toutes les caractéristiques
    #                  de tous les pavés de 3x3 pixels.
    def comp_logect_pave(self,frac,root='.'):
        """
        Détermination de l'écart-type relatif en fonction du canal VIMS, ceci pour la fraction 'frac'
        de pixels choisis.

        > input:
            - frac: the fraction of useful pixels, must be positive and smaller than 1.
        > output:
            - N_sample : dimension 'sample' du cube utilisé.
            - N_line   : dimension 'line' du cube utilisé.
            - Expo_time: cube exposure based on `channel`.
            - Ls       : longitude solaire (calculée avec le module 'titan-moon' de Benoît)
            - detect_temp: liste des températures "du détecteur".
            - instru_temp: liste des températures "de l'instrument".
            - opt_temp   : liste des températures "de l'optique".
            - ns_rand  : liste des coord. 'sample' des pixels aux centres des pavés 3x3.
            - nl_rand  : liste des coord. 'line' des pixels aux centres des pavés 3x3.
            - latC_pav : liste des latitudes des pixels centraux des pavés 3x3.
            - lonC_pav : liste des longitudes des pixels centraux des pavés 3x3.
            - res_av   : resolution moyenne individuelle des pixels centraux des pavés 3x3.
            - log10_ectype_relat: log10 des écart-types relatifs de I/F sur les pavés 3x3 (list de tableaux Numpy de 256 éléments, ie nbr de canaux VIMS).
            - IsF_av   : valeurs moyennes des I/F correspondantes (list de tableaux Numpy de 256 éléments, ie nbr de canaux VIMS).
            - ectr_inc : écart-types relatifs sur les angles d'incidence, sur les pavés.
            - inc_av   : valeurs moyennes des angles d'incidence, sur les pavés.
            - ectr_eme : écart-types relatifs sur les angles d'émission, sur les pavés.
            - eme_av   : valeurs moyennes sur les angles d'émission, sur les pavés.
            - ectr_phase : écart-types relatifs sur les angles de phase, sur les pavés.
            - phase_av   : valeurs moyennes des angles de phases, sur les pavés.
        """
        nb_VIMS_channels = 256

        # ----------------------------------------------------------
        # Caractéristiques du cube :
        N_sample = self.NS   # Nombre de sample
        N_line   = self.NL   # Nombre de line
        Expo_time= self.expo # Temps d'exposition

        # Détermination de la longitude solaire du cube :
        Ls     = orbit.Ls(self)

        # Les températures de l'instrument :
        detect_temp = self.isis['DETECTOR_TEMPERATURE']
        instru_temp = self.isis['INSTRUMENT_TEMPERATURE']
        opt_temp    = self.isis['OPTICS_TEMPERATURE']

        # ----------------------------------------------------------
        log10_ectype_relat_list = [] # On stocke la liste des lois d'écart-type relatifs. Chaque élément de cette liste
                                     # correspond à un pixel.

        # ----------------------------------------------------------
        # Construction des listes de coordonnées des pixels centraux (i.e. pixels aux centres des
        # pavés 3x3 tirés au sort dans le cube) choisis :
        ns_rand, nl_rand = self.choice_pix(frac,root)
        nb_pix = ns_rand.size

        # ----------------------------------------------------------
        # Construction des tableaux des latitudes, longitudes et résolution
        # moyenne des pixels centraux des pavés 3x3 :
        latC_pav = np.array([])
        lonC_pav = np.array([])
        res_av   = np.array([])
        for i in  range(nb_pix):
            s = ns_rand[i]
            l = nl_rand[i]
            myLat = self[s,l].lat # Planetocentric North latitude
            myLon = self[s,l].lon # Planetocentric West longitude.
            myRes = self[s,l].res # :
            latC_pav = np.append(latC_pav, myLat)
            lonC_pav = np.append(lonC_pav, myLon)
            res_av   = np.append(res_av, myRes)

        # ----------------------------------------------------------
        # Construction des tableaux d'écrat-types relatif et de moyenne de I/F
        # ceci sur tous les pavés 3x3 et les canaux VIMS :
        log10_ectype_relat = []
        IsF_av             = []
        for i in  range(nb_pix):
            s = ns_rand[i]
            l = nl_rand[i]
            pixels = [ [s-1,l-1], [s,l-1], [s+1,l-1],
                       [s-1,l  ], [s,l  ], [s+1,l],
                       [s-1,l+1], [s,l+1], [s+1,l+1] ]

            # Boucle sur les canaux VIMS :
            log10_ectype_relat_temp = np.array([])
            IsF_av_temp             = np.array([])
            for can in range(nb_VIMS_channels):
                IsF_block = np.array([]) # On construit une liste avec les I/F du canal VIMS considéré,
                                         # ceci sur les 9 pixels du "pavé" considéré.
                for pix in pixels:
                    #print (pix)
                    sa = pix[0]
                    li = pix[1]
                    IsF = self[sa, li].spectrum[can]
                    IsF_block = np.append(IsF_block, IsF)
                # On calcule, pour le canal en question, l'écart-type relatif pour les 9 pixels considérés :
                #   - Rq. : on élimine les valeurs aberrantes qui surviennent pour quelques pixels, ceci en
                #           remplaçant leur écart-type relatif par "0.5"
                ectr = np.std(IsF_block)/np.mean(IsF_block) # l'écart-type relatif calculé sur le pavé de 3x3 pixels
                if (ectr > 0.) and (ectr < 1.):
                    log10_ectype_relat_temp = np.append(log10_ectype_relat_temp, np.log10(ectr))
                else:
                    ectr = 0.5
                    log10_ectype_relat_temp = np.append(log10_ectype_relat_temp, np.log10(ectr))
                # Et pour le canal en question du pavé considéré on calcul la moyenne de I/F :
                IsF_av_temp = np.append(IsF_av_temp, np.mean(IsF_block))

            log10_ectype_relat.append(log10_ectype_relat_temp)
            IsF_av.append(IsF_av_temp)

        # ----------------------------------------------------------
        # Construction des tableaux d'écart-types relatifs et de moyennes
        # pour les angles : incidence, émergence et phase :
        ectr_inc = np.array([])
        inc_av   = np.array([])
        ectr_eme = np.array([])
        eme_av   = np.array([])
        ectr_phase = np.array([])
        phase_av   = np.array([])

        for i in  range(nb_pix):
            s = ns_rand[i]
            l = nl_rand[i]
            pixels = [ [s-1,l-1], [s,l-1], [s+1,l-1],
                       [s-1,l  ], [s,l  ], [s+1,l],
                       [s-1,l+1], [s,l+1], [s+1,l+1] ]

            inc_temp   = np.array([])
            eme_temp   = np.array([])
            phase_temp = np.array([])

            for pix in pixels:
                #print (pix)
                sa = pix[0]
                li = pix[1]
                inc_temp   = np.append(inc_temp, self[sa,li].inc)
                eme_temp   = np.append(eme_temp, self[sa,li].eme)
                phase_temp = np.append(phase_temp, self[sa,li].phase)

            ectr_inc   = np.append(ectr_inc, np.std(inc_temp)/np.mean(inc_temp))
            inc_av     = np.append(inc_av,   np.mean(inc_temp))

            ectr_eme   = np.append(ectr_eme, np.std(eme_temp)/np.mean(eme_temp))
            eme_av     = np.append(eme_av,   np.mean(eme_temp))

            ectr_phase = np.append(ectr_phase, np.std(phase_temp)/np.mean(phase_temp))
            phase_av   = np.append(phase_av,   np.mean(phase_temp))

        # ----------------------------------------------------------
        # Sorties :
        return N_sample, N_line, Expo_time, Ls, detect_temp, instru_temp, opt_temp, \
               ns_rand, nl_rand, latC_pav, lonC_pav, res_av, log10_ectype_relat, IsF_av, \
               ectr_inc, inc_av, \
               ectr_eme, eme_av, \
               ectr_phase, phase_av
