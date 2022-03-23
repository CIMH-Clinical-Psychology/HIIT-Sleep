# -*- coding: utf-8 -*-
"""
Created on Mon Mar 21 11:06:38 2022

@author: Simon
"""
print('Loading libraries...')
import os
import mne
import yasa
import pyedflib
import utils
import easygui
import pandas as pd
from tqdm import tqdm
from pyedflib import highlevel

print('Please select EDF files for loading..')
#%% choose files to run analysis on
edf_files = utils.choose_files(exts='edf')

# edf_files = ('Z:/Exercise_Sleep_Project/EDF Export EEG/AA3_EX_AA3_EX_(1).edf',
#   'Z:/Exercise_Sleep_Project/EDF Export EEG/AA3_REST_AA3_REST_(1).edf')

#%% check all files and scan channels

# ignore these channels in the selection
ch_ignore = ['II','EKG II', 'EMG1', 'Akku', 'Akku Stan', 'Lage', 'Licht', 
             'Aktivitaet', 'SpO2', 'Pulse',  'Pleth', 'Flow&Snor', 'RIP Abdom',
             'RIP Thora', 'Summe RIP', 'RIP', 'Stan', 'Abdom', 'Thora']
all_chs = set()
common_chs = set()
common_stages = []

for edf_file in tqdm(edf_files, desc='Scanning files'):
    # first check the channels that are available
    header = highlevel.read_edf_header(edf_file)
    duration = header['Duration']
    chs = [ch for ch in header['channels'] if not ch in ch_ignore]
    if len(common_chs)==0: 
        common_chs = set(chs)
    common_chs.intersection(chs)
    all_chs = all_chs.union(chs)
    
    # now check that there is a hypnogram available
    hypno_file = utils.infer_hypno_file(edf_file)
    assert hypno_file, f'No hypnogram found for {edf_file}, make sure it\'s in the same folder'
    hypno = utils.read_hypno(hypno_file, verbose=False, exp_seconds=duration)
    common_stages.extend(hypno)
    assert (len(hypno)-(duration/30))<2, \
        f'hypnogram does not match length of file: hypno {len(hypno)} epochs, file {(duration/30)} epochs'
    
common_chs = sorted(common_chs)
#%% select channel to run analysis on

preselect_ch = common_chs.index('C3') if 'C3' in common_chs else 0
preselect_ref = common_chs.index('M2') if 'C3' in common_chs else 0

ch = easygui.choicebox(f'Please select main channel for running the spindle analysis',  
                       choices=common_chs, preselect=preselect_ch)
ref = easygui.choicebox(f'Please select REFERENCE for {ch}', preselect=preselect_ref,
                        choices=['no referencing'] + common_chs)

assert ch, 'no channel selected'
assert ref, 'no reference selected'

#%% select stages to run analysis on
stages = set(common_stages)
stages = [f'{s} - {utils.stages_dict[s]}' for s in stages]

stages_sel = easygui.multchoicebox(f'Which stages do you want to limit the analysis to?',
                           choices=stages, preselect=[2, 3])
stages_sel = [int(x[0]) for x in stages_sel]

report_mode = easygui.buttonbox(f'Do you want the report on the selected stages ({stages_sel}) together or each stage individually?',
                  choices=['together', 'individually'])

#%% run spindle analysis

tqdm_loop = tqdm(total=len(edf_files))
def set_desc(desc):
    tqdm_loop.set_description(f'{desc} - {os.path.basename(edf_file)}')


all_summary = pd.DataFrame()
for i, edf_file in enumerate(edf_files):
    
    summary_csv = os.path.join(os.path.dirname(edf_file), f'_summary_{len(edf_files)}_subjects.csv')
    
    subj = os.path.basename(edf_file)    
    spindles_csv = f'{edf_file}_spindles.csv'

    
    set_desc('Loading file')
    ch_ignore = all_chs.difference([ch, ref])
    
    raw = mne.io.read_raw_edf(edf_file, exclude=ch_ignore, preload=True, verbose='WARNING') # we load the file into memory using the function `mne.io.read_raw_edf`
    if ref!='no referencing':
        raw = mne.set_bipolar_reference(raw, anode=[ch], cathode=[ref], verbose=False)
        ch_pick = f'{ch}-{ref}'
    else:
        ch_pick = ch
    raw.pick_channels([ch_pick])
    
    hypno_file = utils.infer_hypno_file(edf_file)
    hypno = utils.read_hypno(hypno_file, verbose=False)
    hypno_resampled = yasa.hypno_upsample_to_data(hypno, sf_hypno=1/30, data=raw)

    set_desc(f'Detecing spindles')
    try:
        spindles = yasa.spindles_detect(raw, hypno=hypno_resampled, include=stages_sel)    
    except Exception as e:
        print(f'ERROR: {e}')
        continue
    spindles_subj = spindles.summary()
    spindles_subj.to_csv(summary_csv)
    
    spindles_subj.drop(['Start', 'Peak', 'End'], inplace=True, axis=1)
    

    if report_mode=='together':
        summary = spindles_subj.mean(0)
        samples_stages = sum([(hypno_resampled==s).sum() for s in stages_sel])
        stages_minutes = samples_stages/60/raw.info['sfreq']
        summary['Density'] = len(spindles_subj)/stages_minutes
    elif report_mode=='individually':
        for stage in stages_sel:
            spindles_stage = spindles_subj[spindles_subj['Stage']==stage]
            summary = spindles_stage.mean(0)
            samples_stages = (hypno_resampled==stage).sum() 
            stages_minutes = samples_stages/60/raw.info['sfreq']
            summary['Density'] = len(spindles_stage)/stages_minutes
    else:
        raise ValueError(f'mode not known: {report_mode}')
        
    summary.name = subj
    
    all_summary = all_summary.append(summary)
    tqdm_loop.update()
    
    all_summary.to_csv(summary_csv)


try:
    import pandasgui
    pandasgui.show(all_summary)
except:
    print('INFO: pandasgui is not installed, cannot show results. To visualize the results, install via `pip install pandasgui`')