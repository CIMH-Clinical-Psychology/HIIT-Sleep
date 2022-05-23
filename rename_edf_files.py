# -*- coding: utf-8 -*-
"""
Created on Fri May 20 10:53:19 2022

@author: Simon
"""
import utils
from pathlib import Path

#%% SETTINGS
data_dir = '/data/Exercise_Sleep_Project/EDF Export EEG'
new_name_template = '{subject}_{condition}.edf'

# rename other files that have a similar pattern as well
# e.g. AF4_EX.edf_artefacts.csv
rename_related_files = True 



#%% SCRIPT

# Rename all files in the folder with the given pattern
#
#
edf_files = utils.list_files(data_dir, ext='edf')

for edf_file in edf_files:
    subject, condition = utils.get_subj_cond(edf_file)
    
    new_name = eval(f"f'{new_name_template}'")

    old_file = Path(edf_file)
    # continue
    old_file.rename(Path(data_dir, new_name))

    if rename_related_files:
        related_files = [Path(f) for f in utils.list_files(data_dir, ext='')]
        related_files = [f for f in related_files if f.stem.startswith(old_file.stem)]
        new_related_name = [str(f).replace(old_file.stem, new_name[:-4]) for f in related_files]
        
        [f_old.rename(f_new) for f_old, f_new in zip(related_files, new_related_name)]