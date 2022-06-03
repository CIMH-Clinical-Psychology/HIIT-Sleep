# -*- coding: utf-8 -*-
"""
Created on Mon May 16 14:22:45 2022

small script to display bad epochs and spindles found in a file

@author: Simon
"""
import utils
import mne
import sys
import numpy as np
import pandas as pd
import sleep_utils
import yasa
import matplotlib.pyplot as plt
#%% SETTINGS

data_dir = 'Z:/Exercise_Sleep_Project/EDF Export EEG'

channels = ['EOGr', 'EOGl', 'Pz', 'C4'] # channel(s) that the artefact detection should be performed on
references = ['M1', 'M2'] # list of channels used to construct a reference


#%%


def plot_artefacts(edf_file, blocking=True):
    
    raw = utils.load_edf(edf_file, channels=channels, references=references)
    
    raw.resample(100)
    art_file = f'{edf_file[:-4]}_artefacts.csv'
    spindle_file = f'{edf_file}_spindles.csv'
    hypno_file = f'{edf_file}.txt'
    events = []
    
    artefacts = np.loadtxt(art_file)
    with open(art_file, 'r') as f:
        lines = f.read().split('\n')
        winlen = [int(l[l.find('window_length')+14:]) for l in lines if 'window_length' in l][0]

    # add annotations for spindles
    spindles = pd.read_csv(spindle_file)
    for start, stop in zip(spindles['start'], spindles['end']):
        duration = stop-start
        events.append([start, duration, 'spindle'])
    
    # add annotations for bad segments

    for art_i, art_x in enumerate(artefacts.T):
        if np.sum(art_x)==0: continue

        inside_art = False
        for i, is_art in enumerate(art_x):
            if is_art and not inside_art:
                start = int(i*winlen)
                duration = winlen
                inside_art = True
                
            elif is_art and inside_art:
                duration += winlen
                
            elif not is_art and inside_art:
                inside_art = False
                event = [start, duration, f'BADS_{art_i}']
                events.append(event)
        if inside_art:
          event = [start, duration, 99]
          events.append(event)  
          
    # add annotations for sleep stages
    hypno = sleep_utils.read_hypno(hypno_file)
    hypno_time = sleep_utils.tools.hypno2time(hypno, seconds_per_epoch=30).split('\n')[1:]
    stages = [line.split('\t')[0] for line in hypno_time if not len(line)==0]
    starts = [int(line.split('\t')[1]) for line in hypno_time if not len(line)==0]
    starts.insert(0, 0)
    durations = np.diff(starts)
    events += list(zip(starts, durations, stages))
          
    # plot the file
    events = np.array(events)   
    yasa_annotations = mne.Annotations(*events.T, orig_time=raw.info['meas_date'])        
    raw.set_annotations(yasa_annotations)  
    try:
        _ = raw.plot(duration=60, scalings=5e-4, block=False, lowpass=30, use_opengl=True)
    except:
        _ = raw.plot(duration=60, scalings=5e-4, block=False, lowpass=30, use_opengl=False)

    try:
        figManager = plt.get_current_fig_manager()
        figManager.window.state('zoomed') #works fine on Windows!
        # figManager.window.showMaximized()
    except:
        pass
    plt.show(block=blocking)
    
#%%    
if __name__=='__main__':
    
    if len(sys.argv)>1:
        import matplotlib; matplotlib.use('TkAgg')
        plot_artefacts(sys.argv[1], blocking=True)
    else:
        edf_files = utils.choose_files(data_dir, exts='edf', title='Choose edf file to look at')
        for edf_file in edf_files:
            plot_artefacts(edf_file)