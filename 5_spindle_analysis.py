# -*- coding: utf-8 -*-
"""
Created on Mon May 23 10:52:38 2022

Find spindles using wonambi.detect.spindle.DetectSpindle
based on Mölle2011 - Mölle, M. et al. (2011) Sleep 34(10), 1411-21

@author: Simon Kern
"""

import os
import yasa
import wonambi
import mne
import pandas as pd
import warnings
import sleep_utils
import numpy as np
import utils # must be executed in the same folder as the utils.py
from tqdm import tqdm
from datetime import datetime
import seaborn as sns
from scipy.signal import find_peaks, welch, detrend
import matplotlib.pyplot as plt
from wonambi.dataset import Dataset
from wonambi.attr import Annotations, create_empty_annotations
import tempfile
import time
from wonambi.trans import select, resample, frequency, get_times, fetch

# some helper functions
def get_individual_spindle_peak(raw, hypno_upsampled, lfreq=10, hfreq=16):
    sfreq = raw.info['sfreq']
    data = raw.get_data()

    f, pxx = welch(data[:, hypno_upsampled == 2], sfreq, nperseg=(10 * sfreq),
                   noverlap=sfreq*5, scaling='spectrum')
    
    # Keep only frequencies of interest
    pxx = pxx[:, np.logical_and(f >= lfreq, f <= hfreq)]
    f = f[np.logical_and(f >= lfreq, f <= hfreq)]
    idx_peaks, _ = find_peaks(pxx.mean(0), distance=pxx.shape[-1])
    spindle_peak = f[idx_peaks[0]]
    if spindle_peak<10.2:
        warnings.warn(f'Spindle peak is at {spindle_peak}, probably detection did not work')
    return spindle_peak



def hypno2wonambi(hypno, artefacts, dataset):
    """
    create annotations file 
    
    :param hypno: hypnogram in 30 seconds base
    :param artefact: array with artefact markings
    :param dataset: a wonambi.Dataset type
    """
    # conv_dict = {0: 'Wake',
    #              1: 'NREM1',
    #              2: 'NREM2',
    #              3: 'NREM3',
    #              4: 'REM'}
    hypno_art = yasa.hypno_upsample_to_data(hypno, sf_hypno=1/30,
                                            data=artefacts, sf_data=1/winlen)
    tmp_xls = tmp_dir + f'/tmp_scoring_{subj}_{cond}_{time.time()}.xls'

    create_empty_annotations(tmp_xls, dataset)
    annot = Annotations(tmp_xls)
    annot.add_rater('U-Sleep')
    
    while len((stages:=annot.rater.find('stages'))) != 0:
        for stage in stages:
            stages.remove(stage)
            
    annot.create_epochs(winlen)
    
    assert len(hypno_art)==len(artefacts)

    for i, (stage, art) in enumerate(zip(hypno_art, artefacts)):
        # name = conv_dict[int(stage)]
        name = str(stage)
        if art:
            annot.set_stage_for_epoch(i*winlen, 'Poor',
                                                 attr='quality',
                                                 save=False)
        else:
            annot.set_stage_for_epoch(i*winlen, name, save=False)
        
    annot.save()
    return annot
#%% SETTINGS
data_dir = 'Z:/Exercise_Sleep_Project/EDF Export EEG'

channels = [ 'Pz'] # channel(s) that the spectrogram creation should be performed on
references = ['M1', 'M2'] # list of channels used to construct a reference

# denote stages that should be used for spindle detection
stages = [2, 3]

# which method to use for spindle detection
# for a full list of methods see https://wonambi-python.github.io/gui/methods.html
# changing the method might need some more parameters to be adapted
# in the wonambi.detect.spindle.DetectSpindle method call below
method = 'Moelle2011'

# either use a fixed spindle peak, i.e. `13` Hz or calculate the individual
# spindle frequency using spectrogram peak estimation 
spindle_peak = 'individual' # either a fixed number, ie. 13 or `individual`
spindle_range = 2 # +-2.5 Hz around the peak
spindle_duration = (0.5, 2) # min and max duration of spindles


#%%

edf_files = utils.list_files(data_dir, ext='edf')

tmp_dir = tempfile.mkdtemp()


tqdm_loop = tqdm(edf_files)

df_summary = pd.DataFrame()

for edf_file in edf_files:
    subj, cond = utils.get_subj_cond(edf_file)
    tqdm_loop.set_description(f'{subj}_{cond}, Loading data')

    raw = utils.load_edf(edf_file, channels, references)
    
    # now load the hypnogram that fits to this data
    hypno_file = utils.infer_hypno_file(edf_file)
    hypno = sleep_utils.read_hypno(hypno_file, verbose=False)
    hypno_upsampled = yasa.hypno_upsample_to_data(hypno, sf_hypno=1/30, data=raw)
    assert len(raw)//raw.info['sfreq']//30==len(hypno)

    # load artefacts for this participant
    art_file = f'{edf_file[:-4]}_artefacts.csv'
    artefacts = np.loadtxt(art_file).max(1)
    winlen = utils.get_var_from_comments(art_file, 'window_length')
    
    if spindle_peak=='individual':
        spindle_peak_freq = get_individual_spindle_peak(raw, hypno_upsampled)
    else:
        spindle_peak_freq = spindle_peak
        
    tqdm_loop.set_description(f'{subj}_{cond}, Determining segments')

    spindle_band = (spindle_peak_freq-spindle_range, 
                    spindle_peak_freq+spindle_range)
    
    detector = wonambi.detect.spindle.DetectSpindle(method=method, 
                                               frequency=spindle_band,
                                               duration=spindle_duration)
    dataset = Dataset(edf_file)  
    annot = hypno2wonambi(hypno, artefacts, dataset)
    
    df = pd.DataFrame()
    df_mean = pd.Series()

    for stage in stages:
        segments = fetch(dataset, annot, cat=(1,1,1,0), stage=[str(stage)])
        
        segments.read_data(chan=channels, ref_chan=references)
        data = segments[0]['data']
        tqdm_loop.set_description(f'{subj}_{cond}, Det, spindles stage {stage}')
    
        spindles = detector(data)
        
        df_spindles = pd.DataFrame(spindles.events)
    
        df_spindles['peak_val_orig'] = df_spindles['peak_val_orig'].astype(float)
        df_spindles['rms_orig'] = df_spindles['rms_orig'].astype(float)
        df_spindles['ptp_orig'] = df_spindles['ptp_orig'].astype(float)
        df_spindles['stage'] = stage
        df = pd.concat([df, df_spindles])
        
        mean_vars = ['dur', 'peak_val_det', 'peak_val_orig', 'auc_det', 'auc_orig',
                     'rms_det', 'rms_orig', 'power_orig', 'peak_freq', 'ptp_det',
                     'ptp_orig']
        df_mean_stage = df_spindles[mean_vars].mean()
        df_mean_stage['density'] = spindles.density[0]
        df_mean_stage.index += f'_stage{stage}'
        df_mean = pd.concat([df_mean, df_mean_stage], axis=0)
        
    df_mean.name = f'{subj}_{cond}'
    df_mean['subj'] = subj
    df_mean['condition'] = cond
    
    df_summary = df_summary.append(df_mean)
        
    tqdm_loop.update()
    
    spindles_csv = edf_file + '_spindles.csv'
    df.sort_values('start', inplace=True)
    df.to_csv(spindles_csv)
    
df_summary['method'] = method    
df_summary['spindle_peak'] = spindle_peak
df_summary['spindle_range'] = str(spindle_range)
df_summary['spindle_duration'] = str(spindle_duration)

cols = list(df_summary.columns)
cols = cols[-6:]+ cols[:-6]
df_summary = df_summary[cols]

summary_csv = f'{data_dir}/_summary_spindles.csv'
df_summary.to_csv(summary_csv)

sns.scatterplot(data=df_summary, x='subj', y='density_stage2', hue='condition')
