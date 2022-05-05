import cv2

from . import configuration
from . import model as m
from . import datacollection as datacollection
import numpy as np

from sklearn.metrics import multilabel_confusion_matrix, accuracy_score


def test_model(X_test, y_test):
    yhat = m.model.predict(X_test)
    ytrue = np.argmax(y_test, axis=1).tolist()
    yhat = np.argmax(yhat, axis=1).tolist()
    multilabel_confusion_matrix(ytrue, yhat)
    accuracy_score(ytrue, yhat)


colors = [(245, 117, 16), (117, 245, 16), (16, 117, 245), (245, 100, 16), (117, 25, 16), (36, 117, 245), (245, 117, 56),
          (127, 245, 16), (16, 117, 245), (56, 117, 245), (245, 117, 16), (117, 245, 16), (16, 117, 245),
          (245, 100, 16), (117, 25, 16), (36, 117, 245), (245, 117, 56), (127, 245, 16), (16, 117, 245), (56, 117, 245),
          (245, 117, 16), (117, 245, 16), (16, 117, 245), (245, 100, 16), (117, 25, 16), (36, 117, 245), (245, 117, 56),
          (127, 245, 16), (16, 117, 245), (56, 117, 245), (245, 117, 16), (117, 245, 16), (16, 117, 245),
          (245, 100, 16), (117, 25, 16), (36, 117, 245), (245, 117, 56), (127, 245, 16), (16, 117, 245), (56, 117, 245),
          (245, 117, 16), (117, 245, 16), (16, 117, 245), (245, 100, 16), (117, 25, 16), (36, 117, 245), (245, 117, 56),
          (127, 245, 16), (16, 117, 245), (56, 117, 245)]


def prob_viz(res, actions, input_frame, colors):
    output_frame = input_frame.copy()
    for num, prob in enumerate(res):
        cv2.rectangle(output_frame, (0, 60 + num * 40), (int(prob * 100), 90 + num * 40), colors[num], -1)
        cv2.putText(output_frame, actions[num], (0, 85 + num * 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2,
                    cv2.LINE_AA)
    return output_frame


def realtime_prediction(mp_data, image, cv2, sequence, sentence, predictions):
    # 1. New detection variables
    threshold = 0.4

    # 2. Prediction logic
    keypoints = datacollection.extract_keypoints(mp_data)
    sequence.append(keypoints)
    sequence = sequence[-30:]

    if len(sequence) == 30:
        sequence_padded = m.fill_blank_sequence(sequence, len(sequence), configuration.max_number_frame)
        res = m.model.predict(x=np.expand_dims(sequence_padded, axis=0))[0]
        best_fit = np.argmax(res)
        predicted_action = configuration.actions[best_fit]
        print('Label = ' + configuration.actions[best_fit] + ' accuracy = ' + str(
            best_fit) + ' frame number = ' + str(len(sequence)) + ' padded up to ' + str(
            configuration.max_number_frame))
        predictions.append(predicted_action)

        # 3. Viz logic
        if predictions[-30:].count(predicted_action) > 20:
            if res[best_fit] > threshold:

                if len(sentence) > 0:
                    if predicted_action != sentence[-1]:
                        sentence.append(predicted_action)
                else:
                    sentence.append(predicted_action)

        if len(sentence) > 5:
            sentence = sentence[-5:]

        # Viz probabilities
        image = prob_viz(res, configuration.actions, image, colors)

        cv2.rectangle(image, (0, 0), (640, 40), (245, 117, 16), -1)
        cv2.putText(image, ' '.join(sentence), (3, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

        return sentence


def local_prediction():
    cap = cv2.VideoCapture(0)
    # Set mediapipe model
    with datacollection.mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
        while cap.isOpened():

            # Read feed
            ret, frame = cap.read()
            # print("Frame = " + str(frame))

            # Make detections
            image, results = datacollection.mediapipe_detection(frame, holistic)
            # print("Results = " + str(results))

            # Draw landmarks
            datacollection.draw_styled_landmarks(image, results)

            analyse_mp(mp_data=results, image=image, cv2=cv2)

            # Show to screen
            cv2.imshow('OpenCV Feed', image)

            # Break gracefully
            if cv2.waitKey(10) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()
