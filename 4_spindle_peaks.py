# -*- coding: utf-8 -*-
"""
Created on Mon May 16 11:27:48 2022

Script to detect spindle peak frequencies using different methods described in
https://github.com/raphaelvallat/yasa/blob/master/notebooks/04_spindles_slow_fast.ipynb

@author: Simon
"""
import os
import yasa
import mne
import pandas as pd
import sleep_utils
import numpy as np
import utils # must be executed in the same folder as the utils.py
from tqdm import tqdm
import seaborn as sns
from scipy.signal import find_peaks, welch, detrend
import matplotlib.pyplot as plt

#%% SETTINGS
data_dir = 'Z:/Exercise_Sleep_Project/EDF Export EEG'


channels = [ 'Pz'] # channel(s) that the spectrogram creation should be performed on
references = ['M1', 'M2'] # list of channels used to construct a reference

# denote stages that should be used for spindle detection
stages = [2]



#%%
edf_files = utils.list_files(data_dir, ext='edf')


df = pd.DataFrame()

df_plot = pd.DataFrame()

for edf_file in tqdm(edf_files):
    
    subj, cond = utils.get_subj_cond(edf_file)
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
        
    # upsample artefacts to match the hypnogram
    art_upsampled =  yasa.hypno_upsample_to_data(artefacts, 
                                                 sf_hypno=1/winlen, 
                                                 data=raw)
    
    # remove artefacted segments
    hypno_art = hypno_upsampled.copy()
    hypno_art[art_upsampled==1] = -1
    
    
    # calculate spindle peak using spectrogram approach
    data = raw.get_data()
    sfreq = raw.info['sfreq']
    f, pxx = welch(data[:, hypno_upsampled == 2], sfreq, nperseg=(10 * sfreq),
                   noverlap=sfreq*5, scaling='spectrum')
    
    # Keep only frequencies of interest
    pxx = pxx[:, np.logical_and(f >= 9, f <= 15)]
    f = f[np.logical_and(f >= 9, f <= 15)]
    idx_peaks, _ = find_peaks(pxx.mean(0), distance=pxx.shape[-1])
    spindle_peak = f[idx_peaks[0]]
    
    # calculate spindle peak based on YASA
    sp = yasa.spindles_detect(raw, include=(2), freq_sp=(11, 15)).summary()
    # plt.figure()
    # plt.hist(sp['Frequency'], 100)
    spindle_peak_yasa = sp['Frequency'].mean()
    
    
    df = df.append(pd.Series({'Subject': subj,
                              'Condition': cond,
                              'spindle peak freq (spectrogram)': np.round(spindle_peak,1),
                                'spindle peak freq (yasa)': np.round(spindle_peak_yasa, 1),
                              'stage': stages
                              }),
                                ignore_index=True)
    
    if spindle_peak<11:
        continue
    else:
        pass
    power = pxx.mean(0)
    power = power/power.max()
    df_plot = df_plot.append(pd.DataFrame({'subject': subj, 
                                           'condition': cond,
                                           'frequency': f,
                                           'power': power}), ignore_index=True)
    
    # Plot average spectrum
    # plt.figure(figsize=(10, 6))
    # plt.plot(f, pxx.mean(0), 'ko-', lw=3)
    # plt.plot(f, np.rollaxis(pxx, axis=1), lw=1.5, ls=':', color='grey')
    # plt.xlim(10, 15)
    # plt.title(f'{subj}: channel-based spectrum for {channels}')
    # plt.xlabel('Frequency (Hz)')
    # plt.vlines(f[idx_peaks[0]], 0, pxx.mean(0)[idx_peaks[0]], color='r', alpha=0.5, linewidth=10)
    # _ = plt.ylabel('Power (dB)')
    
    
fig, axs = plt.subplots(2, 1); axs=axs.flatten()
sns.lineplot(data=df_plot, x='frequency', y='power', hue='condition', ax=axs[0])
axs[0].set_ylabel('normalized power (spectrogram)')

sns.scatterplot(data=df, x='Subject', y='spindle peak freq (yasa)', hue='Condition', ax=axs[1])

dfx = df.drop('stage', axis=1).drop('spindle peak freq (spectrogram)', axis=1)
grouped = dfx.groupby('Subject').diff()

spindle_peak_csv = f'{data_dir}/_results_spindle_peaks.csv'
df.to_csv(spindle_peak_csv)

