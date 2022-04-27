# -*- coding: utf-8 -*-
"""
Created on Mon Apr  4 07:12:51 2022

@author: Simon
"""
import os
import importlib
try:
    import utils
except ModuleNotFoundError:
    raise ModuleNotFoundError('Could not find utils script - please check you are' 
                              'running in the same folder as the spindle repository,'
                              ' and that utils.py is located there')



print('Loading libraries...')
utils.install('sleep-utils', ['--upgrade', '--no-deps'])

libraries = ['llvmlite', 'pandas', 'numpy', 'easygui', 'tqdm', 'pyedflib', 'joblib',
             'sleep_utils']
for lib in libraries:
    try:
        print(f'Loading {lib}...')
        importlib.import_module(lib)
    except ModuleNotFoundError:
        print(f'Library `{lib}` not found, attempting to install')
        utils.install(lib)
        
try:
    import numpy as np
    import easygui
    from tqdm import tqdm
    from pyedflib import highlevel
    import matplotlib.pyplot as plt
    import sleep_utils
    from sleep_utils.sigproc import resample
except ModuleNotFoundError as e:
    
    raise ModuleNotFoundError(f'Could not find library {e.name}\nPlease install '
                              f'via the command `pip install {e.name}`')


#%%

if __name__=='__main__':
    edf_files = utils.choose_files(exts='edf')
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
        
    common_chs = sorted(common_chs)
    
    preselect_ch = common_chs.index('Pz') if 'Pz' in common_chs else 0
    preselect_ref = [common_chs.index('M1')+1, common_chs.index('M2')+1] if 'M1' in common_chs else 0
    
    ch = easygui.choicebox('Please select main channel for creating the spectograms.\nHere is a list of channels that is available in all recordings.',  
                           choices=common_chs, preselect=preselect_ch)
    ref = easygui.multchoicebox(f'Please select one or more REFERENCE for {ch}', preselect=preselect_ref,
                            choices=['no referencing'] + common_chs)
    
    
    assert ch, 'no channel selected'
    assert ref, 'no reference selected'
    
    
    fig = plt.figure(figsize=[9,7])
    
    gs = fig.add_gridspec(3,1) # two more for larger summary plots
    axs = []
    
    ax1 = fig.add_subplot(gs[:2, :])
    ax2 = fig.add_subplot(gs[2:, :])
            
    
    tqdm_loop = tqdm(total=len(edf_files), desc='creating spectrograms')
    
    for edf_file in tqdm(edf_files):
        ax1.clear()
        ax2.clear()
        subj = os.path.basename(edf_file)
        
        # we load the file into memory using the function `mne.io.read_raw_edf`
        tqdm_loop.set_description('Loading file')
        ####
        
        sig, sigheads, header = highlevel.read_edf(edf_file, ch_names = [ch] + ref)
            
        if 'no referencing' in ref:
            # set the reference
            data = sig[0]
        else:
            sfreqs = [s['sample_rate'] for s in sigheads]
            refdata = np.atleast_2d(sig[1:])
            if len(set(sfreqs))>1:
                tqdm_loop.set_description('Resampling')

                # print(f'Not all sampling frequencies are the same for {ch} and {ref}: {sfreqs}')
                refdata = [resample(x, sfreqs[i+1], sfreqs[0]) for i, x in enumerate(refdata)]
            data = sig[0] - np.mean(refdata, 0)
                  
        
        png_file = edf_file + f'_{ch}.png'
        
        hypno_file = utils.infer_hypno_file(edf_file)
        if hypno_file:
            hypno = sleep_utils.read_hypno(hypno_file, verbose=False)
            sleep_utils.plot_hypnogram(hypno, ax=ax2, verbose=False)
            
        else:
          print( f'No hypnogram found for {edf_file}, make sure it\'s in the same folder')

        tqdm_loop.set_description('Creating spectrogram')
        
        sleep_utils.specgram_multitaper(data[:], sfreqs[0], ufreq=20, ax=ax1)
        
        tqdm_loop.set_description('Saving plot')
        fig.savefig(png_file)
        tqdm_loop.update()
        
        
        
        
        