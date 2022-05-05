import os
import numpy as np

# Path for exported data, numpy arrays
DATA_PATH = "streamApp/signai/MediaPipe-Data"

# Path for import dataset
DATASET_PATH = "streamApp/signai/videos"

# Actions that we try to detect
# Let actions empty to detect all actions (signs)
# Write down actions wanted like ["action1", "action2", "action3"] (it will manage)
actions_wanted = np.array([])

# Folder start
start_folder = 1

## GLOBAL VARIABLES DO NOT CHANGE #############################

actions = np.array([])
action_paths = {}

# Total of videos for each sign
no_sequences = []

sequence_length = 20

max_number_frame = 30
