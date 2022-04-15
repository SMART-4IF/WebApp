import cv2
import numpy as np
from streamApp import media
from streamApp.media import mp_holistic


class VideoCamera(object):
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        self.holistic = mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5)

    def __del__(self):
        self.cap.release()

    def get_frame(self):
        # ret, frame = self.cap.read()
        # frame_flip = cv2.flip(frame, 1)
        # ret, frame = cv2.imencode('.jpg', frame_flip)
        frame = media.media_detection(self.cap, self.holistic)  # returns an image
        frame_flip = cv2.flip(frame, 1)
        ret, frame = cv2.imencode('.jpg', frame_flip)
        return frame.tobytes()
