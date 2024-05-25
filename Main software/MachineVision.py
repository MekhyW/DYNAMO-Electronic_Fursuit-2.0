import numpy as np
from scipy.special import expit
import math
import cv2
import mediapipe as mp
import pickle
import joblib
import warnings
warnings.filterwarnings("ignore")

mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
drawSpec = mp_drawing.DrawingSpec(thickness=1, circle_radius=2)
face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.5, min_tracking_confidence=0.5)
emotion_model = pickle.load(open('resources/emotion_model.pkl', 'rb'))
pca_model = joblib.load('resources/pca_model.pkl')
eye_closeness_model = pickle.load(open('resources/eyecloseness_model.pkl', 'rb'))
RIGHT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398, 362]
LEFT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246, 33] 
LEFT_IRIS = [468, 469, 470, 471, 472]
RIGHT_IRIS = [473, 474, 475, 476, 477]

results_mesh = None
mesh_points = None
displacement_eye = (0,0)
left_eye_closeness = 0
right_eye_closeness = 0
emotion_labels = ['angry', 'disgusted', 'happy', 'neutral', 'sad', 'surprised']
emotion_labels_extra = ['hypnotic', 'heart', 'rainbow', 'nightmare', 'gears', 'sans', 'mischievous']
emotion_scores = [0]*6

eye_tracking_mode = True
eye_sily_mode = False
expression_manual_mode = False
expression_manual_id = 0

cap = None
cap_id = 1

def open_camera(camera_id):
    global cap
    while True:
        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            print("Camera failure")
        else:
            return cap

def undistort_image(image, k1=-1, k2=1, k3=0.05):
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

def calculate_proximity(pointA, pointB, pointMid):
    dist_MA = math.sqrt((pointA[0] - pointMid[0])**2 + (pointA[1] - pointMid[1])**2 + (pointA[2] - pointMid[2])**2)
    dist_MB = math.sqrt((pointB[0] - pointMid[0])**2 + (pointB[1] - pointMid[1])**2 + (pointB[2] - pointMid[2])**2)
    return 2 * (dist_MA / (dist_MA + dist_MB)) - 1

def calculate_eye_displacement(iris_points, ex1, ex2, ey1, ey2):
    eye_center = np.mean(iris_points, axis=0)
    displacement_x = 2*calculate_proximity(ex1, ex2, eye_center)
    displacement_y = -2*calculate_proximity(ey1, ey2, eye_center)
    displacement = (displacement_x, displacement_y)
    return displacement

def calculate_sclera_area(mesh_points):
    lex1, lex2 = mesh_points[33], mesh_points[133]
    rex1, rex2 = mesh_points[362], mesh_points[263]
    area_sclera_left = 0
    area_sclera_right = 0
    for i in range(len(LEFT_EYE) - 1):
        area_sclera_left += (mesh_points[LEFT_EYE[i], 0] * mesh_points[LEFT_EYE[i + 1], 1]) - (mesh_points[LEFT_EYE[i + 1], 0] * mesh_points[LEFT_EYE[i], 1])
    for i in range(len(RIGHT_EYE) - 1):
        area_sclera_right += (mesh_points[RIGHT_EYE[i], 0] * mesh_points[RIGHT_EYE[i + 1], 1]) - (mesh_points[RIGHT_EYE[i + 1], 0] * mesh_points[RIGHT_EYE[i], 1])
    area_sclera_left = abs(area_sclera_left / (2*(math.sqrt((lex1[0]-lex2[0])**2 + (lex1[1]-lex2[1])**2)**2)))
    area_sclera_right = abs(area_sclera_right / (2*(math.sqrt((rex1[0]-rex2[0])**2 + (rex1[1]-rex2[1])**2)**2)))
    return area_sclera_left, area_sclera_right

def calculate_width_over_height(mesh_points):
    lex1 = mesh_points[33]
    lex2 = mesh_points[133]
    rex1 = mesh_points[362]
    rex2 = mesh_points[263]
    ley1 = mesh_points[159]
    ley2 = mesh_points[145]
    rey1 = mesh_points[386]
    rey2 = mesh_points[374]
    try:
        reason_left = math.sqrt((lex1[0]-lex2[0])**2+(lex1[1]-lex2[1])**2+(lex1[2]-lex2[2])**2)/math.sqrt((ley1[0]-ley2[0])**2+(ley1[1]-ley2[1])**2+(ley1[2]-ley2[2])**2)
        if reason_left > 20: reason_left = 20
    except ZeroDivisionError:
        reason_left = 20
    try:
        reason_right = math.sqrt((rex1[0]-rex2[0])**2+(rex1[1]-rex2[1])**2+(rex1[2]-rex2[2])**2)/math.sqrt((rey1[0]-rey2[0])**2+(rey1[1]-rey2[1])**2+(rey1[2]-rey2[2])**2)
        if reason_right > 20: reason_right = 20
    except ZeroDivisionError:
        reason_right = 20
    return reason_left, reason_right

def update_mesh_points(frame):
    global results_mesh, mesh_points
    H, W, _ = frame.shape
    results_mesh = face_mesh.process(frame)
    if results_mesh.multi_face_landmarks:
        mesh_points = np.array([np.multiply([p.x, p.y, p.z], [W, H, max(W, H)]).astype(int) for p in results_mesh.multi_face_landmarks[0].landmark])

def draw_tracking(frame):
    global results_mesh, mesh_points
    if results_mesh.multi_face_landmarks is not None:
        for faceLms in results_mesh.multi_face_landmarks:
            mp_drawing.draw_landmarks(frame, faceLms, mp_face_mesh.FACEMESH_CONTOURS,drawSpec,drawSpec)
        cv2.circle(frame, (int(np.mean(mesh_points[LEFT_IRIS], axis=0)[0]), int(np.mean(mesh_points[LEFT_IRIS], axis=0)[1])), 5, (0, 0, 255), -1)
        cv2.circle(frame, (int(np.mean(mesh_points[RIGHT_IRIS], axis=0)[0]), int(np.mean(mesh_points[RIGHT_IRIS], axis=0)[1])), 5, (0, 0, 255), -1)
    return frame

def draw_emotion(frame, emotion):
    if emotion:
        cv2.putText(frame, emotion, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
    return frame

def predict_emotion(frame, draw=False):
    global mesh_points, emotion_labels, emotion_scores
    if not expression_manual_mode:
        if mesh_points is None:
            return None
        nose_tip = mesh_points[4] 
        forehead = mesh_points[151]
        mesh_norm = mesh_points - nose_tip
        scale_factor = np.linalg.norm(forehead - nose_tip)
        if np.isclose(scale_factor, 0):
            scale_factor = 1e-6
        mesh_norm = np.divide(mesh_norm, scale_factor)
        landmarks_flat = mesh_norm.flatten()
        landmarks_transformed = pca_model.transform([landmarks_flat])
        pred = emotion_model.predict_proba(landmarks_transformed)[0]
        emotion_scores_noisy = transform_to_zero_one_numpy(pred)
        for score in range(len(emotion_scores)):
            emotion_scores_noisy[score] = expit(10 * (emotion_scores_noisy[score] - 0.5))
            emotion_scores[score] = emotion_scores[score]*0.9 + emotion_scores_noisy[score]*0.1
        if draw:
            pred_index = np.argmax(emotion_scores)
            frame = draw_emotion(frame, emotion_labels[pred_index])
    else:
        emotion_scores = [0]*len(emotion_labels)
        if expression_manual_id < len(emotion_labels):
            emotion_scores[expression_manual_id] = 1
        if draw:
            frame = draw_emotion(frame, emotion_labels[expression_manual_id])
    return frame

def calculate_eye_closeness(mesh_points):
    global left_eye_closeness, right_eye_closeness
    area_sclera_left, area_sclera_right = calculate_sclera_area(mesh_points)
    reason_left, reason_right = calculate_width_over_height(mesh_points)
    pred_left = transform_to_zero_one_numpy(eye_closeness_model.predict_proba([[area_sclera_left, reason_left]])[0], normalize=True)
    pred_right = transform_to_zero_one_numpy(eye_closeness_model.predict_proba([[area_sclera_right, reason_right]])[0], normalize=True)
    left_eye_closeness_noisy = 1.2 - (pred_left[0]*1.2 + pred_left[1]*1 + pred_left[2]*0.5)
    right_eye_closeness_noisy = 1.2 - (pred_right[0]*1.2 + pred_right[1]*1 + pred_right[2]*0.5)
    left_eye_closeness = 0.8 * left_eye_closeness + 0.2 * left_eye_closeness_noisy
    right_eye_closeness = 0.8 * right_eye_closeness + 0.2 * right_eye_closeness_noisy
    return left_eye_closeness, right_eye_closeness

def eye_track(frame, draw=False):
    global results_mesh, mesh_points, displacement_eye, left_eye_closeness, right_eye_closeness
    if eye_tracking_mode:
        H, W, _ = frame.shape
        if mesh_points is not None:
            left_eye_closeness, right_eye_closeness = calculate_eye_closeness(mesh_points)
            displacement_left_eye = calculate_eye_displacement(mesh_points[LEFT_IRIS], mesh_points[33], mesh_points[133], mesh_points[159], mesh_points[145])
            displacement_right_eye = calculate_eye_displacement(mesh_points[RIGHT_IRIS], mesh_points[362], mesh_points[263], mesh_points[386], mesh_points[374])
            displacement_eye_noisy = ((displacement_left_eye[0]+displacement_right_eye[0])/2, (displacement_left_eye[1]+displacement_right_eye[1])/2)
            displacement_eye_noisy = (max(min(1, displacement_eye_noisy[0]), -1), max(min(1, displacement_eye_noisy[1]), -1))
            displacement_eye = 0.5*np.array(displacement_eye) + 0.5*np.array(displacement_eye_noisy)
            if draw:
                frame = draw_tracking(frame)
    else:
        displacement_eye = (0,0)
        left_eye_closeness = 0.2
        right_eye_closeness = 0.2
    return frame

def main(draw=False):
    ret, frame = cap.read()
    if frame is not None:
        frame = undistort_image(frame)
        update_mesh_points(frame)
        frame = eye_track(frame, draw=draw)
        frame = predict_emotion(frame, draw=draw)
        if draw:
            cv2.imshow('frame', frame)
        cv2.waitKey(1)
        return frame
    else:
        open_camera(cap_id)
        return None

if __name__ == "__main__":
    import time
    open_camera(cap_id)
    while True:
        start = time.time()
        frame = main(draw=True)
        emotion_scores_rounded = [round(score, 2) for score in emotion_scores]
        fps = 1/(time.time()-start)
        print(fps, displacement_eye, left_eye_closeness, right_eye_closeness, emotion_scores_rounded)