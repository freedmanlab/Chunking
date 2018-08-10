import numpy as np
from parameters import *
import model
import sys
from analysis import *

task = "chunking"

file_list = ['shuffling_chunking_8_cue_on.pkl']

for file in file_list:
    print('Analyzing network...')
    save_fn = 'cutting_' + file[10:]
    analyze_model_from_file(file, savefile = save_fn)
