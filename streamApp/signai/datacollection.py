import shutil
import cv2
import numpy as np
import os
from . import configuration as configuration
import time
import mediapipe as mp

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
mp_holistic = mp.solutions.holistic  # Holistic model
mp_drawing = mp.solutions.drawing_utils  # Drawing utilitiesdef mediapipe_detection(image, model):


def init_video_variables():
    for root, directories, files in os.walk(configuration.DATASET_PATH):
        if len(directories) == 0:
            actual_dir = root.split("/")[len(root.split("/")) - 1]
            if len(configuration.actions_wanted) == 0 or actual_dir in configuration.actions_wanted:
                configuration.actions = np.append(configuration.actions, actual_dir)
                configuration.action_paths[actual_dir] = root
                n_seq = 0
                for video in files:
                    n_seq += 1
                    # video_path = os.path.join(DATASET_PATH, actualdir, video)
                configuration.no_sequences.append(n_seq)


def mediapipe_detection(image, model):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # COLOR CONVERSION BGR 2 RGB
    image.flags.writeable = False  # Image is no longer writeable
    results = model.process(image)  # Make prediction
    image.flags.writeable = True  # Image is now writeable
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)  # COLOR CONVERSION RGB 2 BGR
    return image, results


def draw_landmarks(image, results):
    mp_drawing.draw_landmarks(image, results.face_landmarks, mp_holistic.FACEMESH_TESSELATION)  # Draw face connections
    mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_holistic.POSE_CONNECTIONS)  # Draw pose connections
    mp_drawing.draw_landmarks(image, results.left_hand_landmarks,
                              mp_holistic.HAND_CONNECTIONS)  # Draw left hand connections
    mp_drawing.draw_landmarks(image, results.right_hand_landmarks,
                              mp_holistic.HAND_CONNECTIONS)  # Draw right hand connections


def draw_styled_landmarks(image, results):
    # Draw face connections
    # mp_drawing.draw_landmarks(
    #    image, results.face_landmarks, mp_holistic.FACEMESH_TESSELATION,
    #    mp_drawing.DrawingSpec(color=(80, 110, 10), thickness=1, circle_radius=1),
    #    mp_drawing.DrawingSpec(color=(80, 256, 121), thickness=1, circle_radius=1)
    # )
    # Draw pose connections
    mp_drawing.draw_landmarks(
        image, results.pose_landmarks, mp_holistic.POSE_CONNECTIONS,
        mp_drawing.DrawingSpec(color=(80, 22, 10), thickness=2, circle_radius=4),
        mp_drawing.DrawingSpec(color=(80, 44, 121), thickness=2, circle_radius=2)
    )
    # Draw left hand connections
    mp_drawing.draw_landmarks(
        image, results.left_hand_landmarks, mp_holistic.HAND_CONNECTIONS,
        mp_drawing.DrawingSpec(color=(121, 22, 76), thickness=2, circle_radius=4),
        mp_drawing.DrawingSpec(color=(121, 44, 250), thickness=2, circle_radius=2)
    )
    # Draw right hand connections
    mp_drawing.draw_landmarks(
        image, results.right_hand_landmarks, mp_holistic.HAND_CONNECTIONS,
        mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=4),
        mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2)
    )


def extract_keypoints_holistic(results):
    pose = np.array([[res.x, res.y, res.z, res.visibility] for res in
                     results.pose_landmarks.landmark]).flatten() if results.pose_landmarks else np.zeros(33 * 4)
    face = np.array([[res.x, res.y, res.z] for res in
                     results.face_landmarks.landmark]).flatten() if results.face_landmarks else np.zeros(468 * 3)
    lh = np.array([[res.x, res.y, res.z] for res in
                   results.left_hand_landmarks.landmark]).flatten() if results.left_hand_landmarks else np.zeros(21 * 3)
    rh = np.array([[res.x, res.y, res.z] for res in
                   results.right_hand_landmarks.landmark]).flatten() if results.right_hand_landmarks else np.zeros(
        21 * 3)
    return np.concatenate([pose, face, lh, rh])


def folder_preparation():
    # Génération des dossiers
    if not os.path.exists(configuration.DATA_PATH):
        os.makedirs(configuration.DATA_PATH)

    # TODO Check useless first branching for actions wanted cause they are already filtered and contained in the actions
    for action in configuration.actions:
        if os.path.exists(os.path.join(configuration.DATA_PATH, action)):
            shutil.rmtree(os.path.join(configuration.DATA_PATH, action))
        os.makedirs(os.path.join(configuration.DATA_PATH, action))

    for action, nbVideo in zip(configuration.actions, configuration.no_sequences):
        if np.array(os.listdir(os.path.join(configuration.DATA_PATH, action))).astype(int).size != 0:
            dirmax = np.max(np.array(os.listdir(os.path.join(configuration.DATA_PATH, action))).astype(int))
        else:
            dirmax = 0
        for sequence in range(1, nbVideo + 1):
            try:
                os.makedirs(os.path.join(configuration.DATA_PATH, action, str(dirmax + sequence)))
            except:
                pass


def extract_keypoints(results):
    # Search center point in results
    pose, face, lh, rh = None, None, None, None
    if results.pose_landmarks is not None and results.pose_landmarks.landmark[0] is not None:
        ref = results.pose_landmarks.landmark[0]
        pose = np.array(
            [[res.x - ref.x, res.y - ref.y, res.z - ref.z, res.visibility] for res in
             results.pose_landmarks.landmark]
        ).flatten() if results.pose_landmarks else np.zeros(33 * 4)
        face = np.array(
            [[res.x - ref.x, res.y - ref.y, res.z - ref.z] for res in
             results.face_landmarks.landmark]
        ).flatten() if results.face_landmarks else np.zeros(468 * 3)
        lh = np.array(
            [[res.x - ref.x, res.y - ref.y, res.z - ref.z] for res in
             results.left_hand_landmarks.landmark]
        ).flatten() if results.left_hand_landmarks else np.zeros(
            21 * 3)
        rh = np.array(
            [[res.x - ref.x, res.y - ref.y, res.z - ref.z] for res in
             results.right_hand_landmarks.landmark]
        ).flatten() if results.right_hand_landmarks else np.zeros(
            21 * 3)
        return np.concatenate([pose, lh, rh])
    elif results.pose_landmarks is not None:
        pose = np.array([[res.x, res.y, res.z, res.visibility] for res in
                         results.pose_landmarks.landmark]).flatten() if results.pose_landmarks else np.zeros(33 * 4)
        face = np.array([[res.x, res.y, res.z] for res in
                         results.face_landmarks.landmark]).flatten() if results.face_landmarks else np.zeros(468 * 3)
        lh = np.array([[res.x, res.y, res.z] for res in
                       results.left_hand_landmarks.landmark]).flatten() if results.left_hand_landmarks else np.zeros(
            21 * 3)
        rh = np.array([[res.x, res.y, res.z] for res in
                       results.right_hand_landmarks.landmark]).flatten() if results.right_hand_landmarks else np.zeros(
            21 * 3)
        return np.concatenate([pose, lh, rh])
    return np.array([])


def analyse_data() -> object:
    # Set mediapipe model
    with mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:

        # NEW LOOP
        # Loop through actions
        for action, nbVideo in zip(configuration.actions, configuration.no_sequences):
            video_num = 0

            # Loop through sequences aka videos
            for video in os.listdir(configuration.action_paths.get(action)):
                cap = cv2.VideoCapture(configuration.action_paths.get(action) + "/" + video)

                video_num += 1

                frame_number = frame_count(configuration.action_paths.get(action) + "/" + video, True)
                print(configuration.action_paths.get(action) + "/" + video + " :: " + str(frame_number) + " frames")

                increment = 0
                idASCII = 97
                # Loop through video length aka sequence length
                for frame_num in range(frame_number):

                    # Read feed
                    success, frame = cap.read()

                    if not success:
                        print("Ignoring empty camera frame on video N° " + str(video_num))
                        break
                    # Make detections
                    image, results = mediapipe_detection(frame, holistic)

                    # Draw landmarks
                    draw_styled_landmarks(image, results)

                    # Export keypoints
                    keypoints = extract_keypoints(results)
                    npy_path = os.path.join(configuration.DATA_PATH, action, str(video_num),
                                            chr(idASCII) + str(increment))
                    np.save(npy_path, keypoints)

                    if increment == 9:
                        increment = 0
                        idASCII += 1
                    else:
                        increment += 1

                    # Break gracefully
                    if cv2.waitKey(10) & 0xFF == ord('q'):
                        break

                cap.release()

        cv2.destroyAllWindows()


# Record mediapipe detected sequences of landmarks
def record_data():
    cap = cv2.VideoCapture(0)
    # Set mediapipe model
    with mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:

        # NEW LOOP
        # Loop through actions
        for action in configuration.actions:
            # Loop through sequences aka videos
            time.sleep(2)

            # set start_folder
            # dirmax = np.max(np.array(os.listdir(os.path.join(configuration.DATA_PATH, action))).astype(int))
            # start_folder = dirmax - configuration.no_sequences + 1

            for sequence in range(1, 10):
                # Loop through video length aka sequence length
                for frame_num in range(configuration.sequence_length):  # TODO Fix

                    # Read feed
                    ret, frame = cap.read()

                    # Make detections
                    image, results = mediapipe_detection(frame, holistic)

                    # Draw landmarks
                    draw_styled_landmarks(image, results)

                    # NEW Apply wait logic
                    if frame_num == 0:
                        cv2.putText(image, 'STARTING COLLECTION', (120, 200),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 4, cv2.LINE_AA)
                        cv2.putText(image, 'Collecting frames for {} Video Number {}'.format(action, sequence),
                                    (15, 12),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
                        # Show to screen
                        cv2.imshow('OpenCV Feed', image)
                        cv2.waitKey(500)
                    else:
                        cv2.putText(image, 'Collecting frames for {} Video Number {}'.format(action, sequence),
                                    (15, 12),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
                        # Show to screen
                        cv2.imshow('OpenCV Feed', image)

                    # NEW Export keypoints
                    keypoints = extract_keypoints(results)
                    npy_path = os.path.join(configuration.DATA_PATH, action, str(sequence), str(frame_num))
                    np.save(npy_path, keypoints)

                    # Break gracefully
                    if cv2.waitKey(10) & 0xFF == ord('q'):
                        break

        cap.release()
        cv2.destroyAllWindows()


def frame_count(video_path, manual=True):
    def manual_count(handler):
        frames = 0
        while True:
            status, frame = handler.read()
            if not status:
                break
            frames += 1
        return frames

    cap = cv2.VideoCapture(video_path)
    # Slow, inefficient but 100% accurate method
    if manual:
        frames = manual_count(cap)
    # Fast, efficient but inaccurate method
    else:
        try:
            frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        except:
            frames = manual_count(cap)
    cap.release()
    return frames
