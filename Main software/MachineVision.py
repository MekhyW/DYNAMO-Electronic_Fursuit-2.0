import numpy as np
from scipy.special import expit
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe import solutions
from mediapipe.framework.formats import landmark_pb2
import pickle
import joblib
import warnings
warnings.filterwarnings("ignore")

try:
    detector = vision.FaceLandmarker.create_from_options(
        vision.FaceLandmarkerOptions(base_options=python.BaseOptions(model_asset_path='models/face_landmarker_v2_with_blendshapes.task'),
        output_face_blendshapes=True,
        num_faces=1
    ))
    emotion_model = pickle.load(open('models/emotion_model.pkl', 'rb'))
    pca_model = joblib.load('models/pca_model.pkl')
except Exception as e:
    print(f"MachineVision constructor failed with error: {e}")

LEFT_IRIS = [468, 469, 470, 471, 472]
RIGHT_IRIS = [473, 474, 475, 476, 477]
EMOTION_LABELS = ['angry', 'disgusted', 'happy', 'neutral', 'sad', 'surprised']
EMOTION_LABELS_EXTRA = ['hypnotic', 'heart', 'rainbow', 'nightmare', 'gears', 'sans', 'mischievous']
CROSS_EYEDNESS_THRESHOLD = 0.4
UPSIDE_DOWN = True

cap = None
cap_id = 0
detection_result = None
mesh_points = None
displacement_eye = (0,0)
left_eye_closeness = 0
right_eye_closeness = 0
cross_eyedness = 0
emotion_scores = [0] * len(EMOTION_LABELS)
left_eye_closeness_noisy = [0, 0, 0, 0, 0]
right_eye_closeness_noisy = [0, 0, 0, 0, 0]
cross_eyedness_noisy = [0, 0, 0, 0, 0]
eye_tracking_mode = True
force_crossed_eye = False
expression_manual_mode = False
expression_manual_id = 0

def open_camera(camera_id):
    global cap
    while True:
        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            print("Camera failure")
        else:
            return cap

def undistort_image(image, k1=-1, k2=1, k3=0.05):
    if UPSIDE_DOWN:
        image = cv2.rotate(image, cv2.ROTATE_180)
    height, width = image.shape[:2]
    focal_length = width
    center = (width/2, height/2)
    camera_matrix = np.array([[focal_length, 0, center[0]],
                              [0, focal_length, center[1]],
                              [0, 0, 1]], dtype=np.float32)
    distortion_coefficients = np.array([k1, k2, k3, 0, 0], dtype=np.float32)
    undistorted_image = cv2.undistort(image, camera_matrix, distortion_coefficients)
    if width > height:
        undistorted_image = undistorted_image[:, int((width-height)/2):int((width+height)/2)]
    return undistorted_image

def rolling_average(readings, new_reading):
    readings.append(new_reading)
    readings.pop(0)
    return np.mean(readings), readings

def transform_to_zero_one_numpy(arr, normalize=False):
    if not len(arr):
        return arr
    min_val = np.min(arr)
    max_val = np.max(arr)
    if min_val == max_val:
        return np.zeros_like(arr)
    value_range = max_val - min_val
    transformed_arr = (arr - min_val) / value_range
    if normalize:
        transformed_arr /= np.sum(transformed_arr)
    return transformed_arr

def calculate_eye_displacement(iris_points, ex1, ex2, ey1, ey2):
    eye_center = np.mean(iris_points, axis=0)
    ex1, ex2 = np.array(ex1), np.array(ex2)
    ey1, ey2 = np.array(ey1), np.array(ey2)
    dist_x1 = np.linalg.norm(ex1 - eye_center)
    dist_x2 = np.linalg.norm(ex2 - eye_center)
    dist_y1 = np.linalg.norm(ey1 - eye_center)
    dist_y2 = np.linalg.norm(ey2 - eye_center)
    displacement_x = 2 * (dist_x1 / (dist_x1 + dist_x2)) - 1
    displacement_y = -2 * (dist_y1 / (dist_y1 + dist_y2)) - 1
    return (displacement_x, displacement_y)

def inference(cv2image):
    global mesh_points, detection_result
    if cv2image is None:
        return None
    image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(cv2image, cv2.COLOR_BGR2RGB))
    detection_result = detector.detect(image)
    if detection_result is None or not len(detection_result.face_blendshapes):
        return None
    blendshapes = detection_result.face_blendshapes[0]
    landmarks = detection_result.face_landmarks[0]
    blendshapes_scores = [cat.score for cat in blendshapes]
    mesh_points = np.array([[p.x, p.y, p.z] for p in landmarks])
    normalized_mesh_points = np.linalg.norm(mesh_points - mesh_points[151], axis=1) / np.linalg.norm(mesh_points[4] - mesh_points[151])
    return [*blendshapes_scores, *normalized_mesh_points]

def draw_tracking(rgb_image):
  global detection_result
  face_landmarks_list = detection_result.face_landmarks
  annotated_image = np.copy(rgb_image)
  for idx in range(len(face_landmarks_list)):
    face_landmarks = face_landmarks_list[idx]
    face_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
    face_landmarks_proto.landmark.extend([landmark_pb2.NormalizedLandmark(x=landmark.x, y=landmark.y, z=landmark.z) for landmark in face_landmarks])
    solutions.drawing_utils.draw_landmarks(image=annotated_image,landmark_list=face_landmarks_proto,connections=mp.solutions.face_mesh.FACEMESH_TESSELATION,landmark_drawing_spec=None,connection_drawing_spec=mp.solutions.drawing_styles.get_default_face_mesh_tesselation_style())
    solutions.drawing_utils.draw_landmarks(image=annotated_image,landmark_list=face_landmarks_proto,connections=mp.solutions.face_mesh.FACEMESH_CONTOURS,landmark_drawing_spec=None,connection_drawing_spec=mp.solutions.drawing_styles.get_default_face_mesh_contours_style())
    solutions.drawing_utils.draw_landmarks(image=annotated_image,landmark_list=face_landmarks_proto,connections=mp.solutions.face_mesh.FACEMESH_IRISES,landmark_drawing_spec=None,connection_drawing_spec=mp.solutions.drawing_styles.get_default_face_mesh_iris_connections_style())
  return annotated_image

def draw_emotion(frame, emotion):
    if emotion:
        cv2.putText(frame, f"Expr: {emotion.capitalize()}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
    return frame

def draw_eyecloseness(frame, left_eye_closeness, right_eye_closeness):
    cv2.putText(frame, f"L eye closed: {round(left_eye_closeness, 2)}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
    cv2.putText(frame, f"R eye closed: {round(right_eye_closeness, 2)}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
    return frame

def draw_gaze(frame, displacement_eye, cross_eyedness):
    cv2.putText(frame, f"Gaze: {round(displacement_eye[0], 2)} {round(displacement_eye[1], 2)}", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
    cv2.putText(frame, f"Crosseyed: {round(cross_eyedness, 2)}", (10, 180), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
    return frame

def predict_emotion(frame, scores, draw=False):
    global mesh_points, EMOTION_LABELS, emotion_scores
    if not expression_manual_mode:
        if scores is None:
            return None
        landmarks_transformed = pca_model.transform([scores])
        pred = emotion_model.predict_proba(landmarks_transformed)[0]
        emotion_scores_noisy = transform_to_zero_one_numpy(pred)
        for score in range(len(emotion_scores)):
            emotion_scores_noisy[score] = expit(10 * (emotion_scores_noisy[score] - 0.5))
            emotion_scores[score] = emotion_scores[score]*0.9 + emotion_scores_noisy[score]*0.1
        if draw:
            pred_index = np.argmax(emotion_scores)
            frame = draw_emotion(frame, EMOTION_LABELS[pred_index])
    else:
        emotion_scores = [0]*len(EMOTION_LABELS)
        if expression_manual_id < len(EMOTION_LABELS):
            emotion_scores[expression_manual_id] = 1
        if draw:
            frame = draw_emotion(frame, EMOTION_LABELS[expression_manual_id])
    return frame

def eye_track(frame, scores, draw=False):
    global detection_result, mesh_points, displacement_eye, left_eye_closeness, right_eye_closeness, left_eye_closeness_noisy, right_eye_closeness_noisy, cross_eyedness, cross_eyedness_noisy
    if eye_tracking_mode and scores:
        left_eye_closeness, left_eye_closeness_noisy = rolling_average(left_eye_closeness_noisy, scores[9]*1.2  + scores[19]*0.6 - scores[21]*1.2)
        right_eye_closeness, right_eye_closeness_noisy = rolling_average(right_eye_closeness_noisy, scores[10]*1.2 + scores[20]*0.6 - scores[22]*1.2)
        displacement_left_eye = calculate_eye_displacement(mesh_points[LEFT_IRIS], mesh_points[33], mesh_points[133], mesh_points[159], mesh_points[145])
        displacement_right_eye = calculate_eye_displacement(mesh_points[RIGHT_IRIS], mesh_points[362], mesh_points[263], mesh_points[386], mesh_points[374])
        displacement_left_eye = (max(min(1, displacement_left_eye[0]), -1), max(min(1, displacement_left_eye[1]), -1))
        displacement_right_eye = (max(min(1, displacement_right_eye[0]), -1), max(min(1, displacement_right_eye[1]), -1))
        displacement_eye_noisy = ((displacement_left_eye[0]+displacement_right_eye[0])/2, (displacement_left_eye[1]+displacement_right_eye[1])/2)
        displacement_eye = 0.5*np.array(displacement_eye) + 0.5*np.array(displacement_eye_noisy)
        cross_eyedness, cross_eyedness_noisy = rolling_average(cross_eyedness_noisy, displacement_left_eye[0] - displacement_right_eye[0])
        if draw:
            frame = draw_tracking(frame)
            frame = draw_eyecloseness(frame, left_eye_closeness, right_eye_closeness)
            frame = draw_gaze(frame, displacement_eye, cross_eyedness)
    else:
        displacement_eye = (0,0)
        left_eye_closeness = 0.2
        right_eye_closeness = 0.2
        cross_eyedness = 0
    return frame

def main(draw=False):
    _, frame = cap.read()
    if frame is not None:
        frame = undistort_image(frame)
        scores = inference(frame)
        frame = eye_track(frame, scores, draw=draw)
        frame = predict_emotion(frame, scores, draw=draw)
        if draw:
            try:
                cv2.imshow('frame', frame)
            except cv2.error:
                print("Frame not ready")
        cv2.waitKey(1)
        return frame
    else:
        open_camera(cap_id)
        return None

if __name__ == "__main__":
    open_camera(cap_id)
    import time
    fps = 0
    while True:
        start = time.time()
        frame = main(draw=True)
        fps = (fps*0.9) + ((1/(time.time()-start))*0.1)
        print(fps)