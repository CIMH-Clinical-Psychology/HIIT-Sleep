# -*- coding: utf-8 -*-
"""
Created on Mon May 16 14:22:45 2022

small script to display the bad epochs that YASA found.

@author: Simon
"""
import utils
import mne
import sys
import numpy as np
import matplotlib.pyplot as plt
#%% SETTINGS

data_dir = 'Z:/Exercise_Sleep_Project/EDF Export EEG'

channels = ['Pz'] # channel(s) that the artefact detection should be performed on
references = ['M1', 'M2'] # list of channels used to construct a reference

# ignore these channels while loading the data. Speeds up loading.
ch_ignore = ['II','EKG II', 'EMG1', 'Akku', 'Akku Stan', 'Lage', 'Licht', 'EOGl'
             'Aktivitaet', 'SpO2', 'Pulse',  'Pleth', 'Flow&Snor', 'RIP Abdom',
             'RIP Thora', 'Summe RIP', 'RIP', 'Stan', 'Abdom', 'Thora', 'EOGr',
             'EOGr:M2', 'EOGr:M1', 'EOGl:M2', 'Aktivitaet', 'C4:M1', 'C3:M2']


#%%


def plot_artefacts(edf_file, blocking=True):
    
    raw = utils.load_edf(edf_file, channels=channels, references=references)
    
    raw.resample(100)
    art_file = f'{edf_file[:-4]}_artefacts.csv'
     
    artefacts = np.loadtxt(art_file)
    with open(art_file, 'r') as f:
        lines = f.read().split('\n')
        winlen = [int(l[l.find('window_length')+14:]) for l in lines if 'window_length' in l][0]
    
    
    events = []
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
          
    events = np.array(events)   
    yasa_annotations = mne.Annotations(*events.T, orig_time=raw.info['meas_date'])        
    raw.set_annotations(yasa_annotations)  
    _ = raw.plot(duration=120, scalings=5e-4, block=False, lowpass=30)
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