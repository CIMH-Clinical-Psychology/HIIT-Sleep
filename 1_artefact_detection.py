# -*- coding: utf-8 -*-
"""
Created on Mon May 16 11:27:48 2022

This script performs some automatic artefact detection and saves
the results to the data directory as .txt files

@author: Simon
"""
import os
import sys
import yasa
import subprocess
import artefact_explorer
import mne
import pandas as pd
import sleep_utils
import numpy as np
import matplotlib.pyplot as plt
import utils # must be executed in the same folder as the utils.py
from tqdm import tqdm
from scipy.stats import kurtosis

#%% SETTINGS

data_dir = 'Z:/Exercise_Sleep_Project/EDF Export EEG'

show_plots = True # show the resulting artefact annotation
show_plots_blocking = True  # will wait until you close the window to show the next file
# only set blocking=False if you have enough memory

with_hypno = True # perform artefact detection separated by stages
window_length = 10 # time window for the artefact detection, e.g. 10 seconds
threshold = 3 # number of standard deviations to be regarded as artefact

channels = ['Pz'] # channel(s) that the artefact detection should be performed on
references = ['M1', 'M2'] # list of channels used to construct a reference

#%% artefact detection

def artefact_heuristic(raw, wlen=10, plot=False):
    """
    a heuristic function to detect if a segment is strongly
    contanimated with noise
    """
    
    thresh1 = 50 # standarddeviation of first derivative, should reliably detect noise
    thresh2 = 600 # 600 uV peak-to-peak, should be enough for k komplex
    thresh3 = 20 # 600 uV peak-to-peak, should be enough for k komplex

    
    data = raw.get_data().squeeze()*1e6
    sfreq = int(raw.info['sfreq'])
    stepsize = int(sfreq * wlen)
    
    val1 = np.zeros(len(raw)//sfreq//wlen)
    val2 = np.zeros(len(raw)//sfreq//wlen)
    val3 = np.zeros(len(raw)//sfreq//wlen)

    
    for i, t in enumerate(range(0, len(raw), stepsize)):
        view = data[t:t+stepsize]
        val1[i] = np.std(np.diff(view))
        val2[i] = (view.max()-view.min())
        val3[i] = kurtosis(np.diff(view))
    
    if plot:
        fig, axs = plt.subplots(3, 1); axs=axs.flatten()
        axs[0].plot(val1)
        axs[0].hlines(thresh1, 0, len(val1))
        axs[1].plot(val2)
        axs[1].hlines(thresh2, 0, len(val2))
        axs[2].plot(val3)
        axs[2].hlines(thresh3, 0, len(val2))
        plt.suptitle(raw.filenames)
        plt.pause(0.1)

    noise_ind = np.vstack([val1>thresh1, val2>thresh2, val3>thresh3]).T
    
    return noise_ind


files = utils.list_files(data_dir)

df = pd.DataFrame()

for edf_file in tqdm(files[25:], desc='calculating artefacts'):
    
    # first of all, load the file itself into memory
    raw = utils.load_edf(edf_file, channels, references)

    # secondly load the hypnogram associated with this sleep recording
    hypno_file = utils.infer_hypno_file(edf_file)
    hypno = sleep_utils.read_hypno(hypno_file)
    
    
    # hypno_upsampled = yasa.hypno_upsample_to_data(hypno, sf_hypno=1/30, data=raw)
    # # run yasa artefact detection on file
    # art1, scores = yasa.art_detect(raw, 
    #                               hypno=hypno_upsampled if with_hypno else None, 
    #                               threshold=threshold,
    #                               include=(0, 1, 2, 3, 4) if with_hypno else None, # which stages to include
    #                               window=window_length,
    #                               verbose='info')
    
    art = artefact_heuristic(raw, wlen=window_length, plot=show_plots).astype(int)

    art_file = f'{edf_file[:-4]}_artefacts.csv'
    comments = f'{window_length=}\n'
    comments += f'{channels=}\n'
    comments += f'{references=}\n'
    
    np.savetxt(art_file, art, fmt='%d', newline='\n', header=comments)

    hypno_art = yasa.hypno_upsample_to_data(hypno, sf_hypno=1/30, data=art, sf_data=1/window_length)
    art = art.max(1)
    art_total = np.sum(art) / len(art)*100
    art_wake = art[hypno_art==0].sum() / len(art[hypno_art==0])*100
    art_n1 = art[hypno_art==1].sum() / len(art[hypno_art==1])*100
    art_n2 = art[hypno_art==2].sum() / len(art[hypno_art==2])*100
    art_n3 = art[hypno_art==3].sum() / len(art[hypno_art==3])*100
    art_rem = art[hypno_art==4].sum() / len(art[hypno_art==4])*100
        
    df = df.append(pd.Series({   'group': 'REST' if 'REST' in edf_file else 'EX',
                                 '% art total': f'{art_total:.1f}%',
                                 '% art Wake': f'{art_wake:.1f}%',
                                 '% art N1': f'{art_n1:.1f}%',
                                 '% art N2': f'{art_n2:.1f}%',
                                 '% art N3': f'{art_n3:.1f}%',
                                 '% art REM': f'{art_rem:.1f}%',
                                 'windows length': window_length,
                                 'threshold' : threshold,
                                 'channels' : channels,
                                 'references' : references}, 
                             name= os.path.basename(edf_file)))
    if show_plots: 
        if show_plots_blocking:
            res = subprocess.check_output(['python', 'artefact_explorer.py', edf_file], 
                         shell=True)
            print(res)
        else:
            subprocess.Popen(['python', 'artefact_explorer.py', edf_file], 
                             stdout=subprocess.PIPE)
    stop
         
      
artefact_csv = f'{data_dir}/_results_artefacts.csv'
df.to_csv(artefact_csv)