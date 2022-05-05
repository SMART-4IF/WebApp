from sklearn.model_selection import train_test_split
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.callbacks import TensorBoard
import cv2
import numpy as np
import os
from matplotlib import pyplot as plt
import time
import mediapipe as mp

from . import configuration
from . import datacollection as datacollection
from . import configuration as conf

# log_dir = os.path.join('Logs')
# tb_callback = TensorBoard(log_dir=log_dir)

label_map = None

model = Sequential()

sequences, labels = [], []


def start_model(load=True):
    load_seq()
    build_model()
    if load:
        load_model()
    else:
        training_data = data_preparation()
        train_model(X_train=training_data.X_train, y_train=training_data.y_train)
    save_model()


class TrainingData:
    def __init__(self, X_train, X_test, y_train, y_test):
        self.X_train = X_train
        self.X_test = X_test
        self.y_train = y_train
        self.y_test = y_test


def data_preparation():
    X = np.array(sequences)
    print('Labels = ' + str(labels))
    y = to_categorical(labels).astype(int)
    print("X shape = " + str(X.shape))
    print("Y shape = " + str(y.shape))
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.05)
    return TrainingData(X_train, X_test, y_train, y_test)


def build_model():
    # time steps = sequence_length - dimension = number of points per sequence
    coef = 2
    model.add(LSTM(64*coef, return_sequences=True, activation='relu', input_shape=(configuration.max_number_frame, 258)))
    model.add(LSTM(128*coef, return_sequences=True, activation='relu'))
    model.add(LSTM(64*coef, return_sequences=False, activation='relu'))
    model.add(Dense(64*coef, activation='relu'))
    model.add(Dense(32*coef, activation='relu'))
    model.add(Dense(conf.actions.shape[0], activation='softmax'))


def train_model(X_train, y_train):
    # model.compile(optimizer="sgd", loss="mse", metrics=["mae", "acc"])
    # model.compile(optimizer='Adam', loss='poisson', metrics=['acc'])
    model.compile(optimizer='Adam', loss='categorical_crossentropy', metrics=['categorical_accuracy']) #latest
    model.fit(X_train, y_train, epochs=50)
    model.summary()


def save_model():
    model.save('streamApp/signai/action.h5')


def load_model():
    model.load_weights('streamApp/signai/action.h5')


def load_seq():
    global label_map
    label_map = {label: num for num, label in enumerate(conf.actions)}
    for root, directories, files in os.walk(conf.DATA_PATH):
        number_frames = len(files)
        if len(directories) == 0:
            print("root " + root + " : len files " + str(len(files)))
            window = []
            for frame_name in files:
                res = np.load(os.path.join(root, frame_name))
                # print("res : " + str(res))
                window.append(res)
            window_padded = fill_blank_sequence(window, number_frames, configuration.max_number_frame)
            sequences.append(window_padded)
            action = root.split("/")[len(root.split("/")) - 2]
            print("action : " + action)
            if configuration.actions.__contains__(action):
                # labels.append(action)
                print("Label map = " + str(label_map))
                labels.append(label_map[action])
    # print('Sequences = ' + str(sequences))
    print('Labels = ' + str(labels))

def getMaxNumberFrame():
    for root, directories, files in os.walk(conf.DATASET_PATH):
        if len(directories) == 0:
            if len(files) > conf.max_number_frame:
                conf.max_number_frame = len(files)


def fill_blank_sequence(sequence, length, max_length):
    filled_sequence = sequence.copy()
    i = max_length - length
    j = 0
    while j < i:
        filled_sequence.append(np.concatenate([np.zeros(33 * 4), np.zeros(21 * 3), np.zeros(21 * 3)]))
        j += 1
    return filled_sequence
