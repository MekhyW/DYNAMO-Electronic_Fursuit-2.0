import numpy as np
import cv2
import mediapipe as mp
import math
import pickle
import joblib
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
drawSpec = mp_drawing.DrawingSpec(thickness=1, circle_radius=2)
face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.5, min_tracking_confidence=0.5)
emotion_model = pickle.load(open('resources/emotion_model.pkl', 'rb'))
pca_model = joblib.load('resources/pca_model.pkl')
cap = cv2.VideoCapture(0)

eye_left_limit = 0.4
eye_right_limit = -0.4
eye_up_limit = -0.1
eye_down_limit = 0.15
RIGHT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
LEFT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
RIGHT_EYE_EXTENDED = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398, 341, 256, 252, 253, 254, 339, 260, 259, 257, 258, 286, 414]
LEFT_EYE_EXTENDED = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246, 110, 24, 23, 22, 26, 112, 190, 56, 28, 27, 29, 30]  
LEFT_IRIS = [468, 469, 470, 471, 472]
RIGHT_IRIS = [473, 474, 475, 476, 477]

results_mesh = None
mesh_points = None
displacement_eye = (0,0)
left_eye_closed = False
right_eye_closed = False
emotion_labels = ['angry', 'disgusted', 'fear', 'happy', 'neutral', 'sad', 'surprised']
emotion_scores = [0]*7

def calculate_roll_angle(landmarks):
    left_ear_x = landmarks[234].x
    left_ear_y = landmarks[234].y
    right_ear_x = landmarks[454].x
    right_ear_y = landmarks[454].y
    angle_rad = math.atan2(right_ear_y - left_ear_y, right_ear_x - left_ear_x)
    angle_deg = math.degrees(angle_rad)
    return angle_deg

def compensate_head_roll(frame, results_mesh, W, H):
    roll_angle_deg = calculate_roll_angle(results_mesh.multi_face_landmarks[0].landmark)
    M = cv2.getRotationMatrix2D((W/2, H/2), roll_angle_deg, 1)
    frame = cv2.warpAffine(frame, M, (W, H))
    return frame

def fit_ellipse(points):
    ellipse = cv2.fitEllipse(points)
    center, axes = ellipse[0], ellipse[1]
    return center, axes

def transform_to_zero_one_numpy(arr):
    if len(arr) == 0:
        return arr
    min_val = np.min(arr)
    max_val = np.max(arr)
    if min_val == max_val:
        return np.zeros_like(arr)
    value_range = max_val - min_val
    transformed_arr = (arr - min_val) / value_range
    return transformed_arr

def calculate_eye_displacement(eye_points, iris_points):
    center, axes = fit_ellipse(eye_points)
    eye_center = np.mean(iris_points, axis=0)
    displacement = (2*(center[0] - eye_center[0]) / (axes[0]), 2*(center[1] - eye_center[1]) / (axes[1]))
    displacement = (displacement[0]/(eye_right_limit-eye_left_limit), displacement[1]/(eye_down_limit-eye_up_limit))
    return displacement

def update_mesh_points(frame):
    global results_mesh, mesh_points
    H, W, _ = frame.shape
    results_mesh = face_mesh.process(frame)
    if results_mesh.multi_face_landmarks:
        frame = compensate_head_roll(frame, results_mesh, W, H)
        results_mesh = face_mesh.process(frame)
    if results_mesh.multi_face_landmarks:
        mesh_points = np.array([np.multiply([p.x, p.y], [W, H]).astype(int) for p in results_mesh.multi_face_landmarks[0].landmark])

def draw_tracking(frame, lex1, ley1, lex2, ley2, rex1, rey1, rex2, rey2, lex1_ext, ley1_ext, lex2_ext, ley2_ext, rex1_ext, rey1_ext, rex2_ext, rey2_ext):
    global results_mesh, mesh_points
    if results_mesh.multi_face_landmarks is not None:
        for faceLms in results_mesh.multi_face_landmarks:
            mp_drawing.draw_landmarks(frame, faceLms, mp_face_mesh.FACEMESH_CONTOURS,drawSpec,drawSpec)
        ellipse_center_L, ellipse_axes_L = fit_ellipse(mesh_points[LEFT_IRIS])
        ellipse_center_R, ellipse_axes_R = fit_ellipse(mesh_points[RIGHT_IRIS])
        cv2.ellipse(frame, (int(ellipse_center_L[0]), int(ellipse_center_L[1])), (int(ellipse_axes_L[0]/2), int(ellipse_axes_L[1]/2)), 0, 0, 360, (0, 0, 255), 2)
        cv2.ellipse(frame, (int(ellipse_center_R[0]), int(ellipse_center_R[1])), (int(ellipse_axes_R[0]/2), int(ellipse_axes_R[1]/2)), 0, 0, 360, (0, 0, 255), 2)
        cv2.rectangle(frame, (lex1, ley1), (lex2, ley2), (0, 255, 0), 2)
        cv2.rectangle(frame, (rex1, rey1), (rex2, rey2), (0, 255, 0), 2)
        cv2.rectangle(frame, (lex1_ext, ley1_ext), (lex2_ext, ley2_ext), (0, 255, 0), 2)
        cv2.rectangle(frame, (rex1_ext, rey1_ext), (rex2_ext, rey2_ext), (0, 255, 0), 2)
    return frame

def draw_emotion(frame, emotion):
    if emotion:
        cv2.putText(frame, emotion, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
    return frame

def predict_emotion(frame, draw=False):
    global mesh_points, emotion_labels, emotion_scores
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
    pred_index = np.argmax(pred)
    emotion_scores_noisy = transform_to_zero_one_numpy(pred)
    emotion_scores_noisy = np.multiply(emotion_scores_noisy, emotion_scores_noisy)
    for score in range(len(emotion_scores)):
        emotion_scores[score] = emotion_scores[score]*0.9 + emotion_scores_noisy[score]*0.1
    if draw:
        frame = draw_emotion(frame, emotion_labels[pred_index])
    return frame

def eye_track(frame, draw=False):
    global results_mesh, mesh_points, displacement_eye, left_eye_closed, right_eye_closed
    H, W, _ = frame.shape
    if mesh_points is not None:
        displacement_left_eye = calculate_eye_displacement(mesh_points[LEFT_EYE_EXTENDED], mesh_points[LEFT_IRIS])
        displacement_right_eye = calculate_eye_displacement(mesh_points[RIGHT_EYE_EXTENDED], mesh_points[RIGHT_IRIS])
        displacement_eye_noisy = ((displacement_left_eye[0]+displacement_right_eye[0])/2, (displacement_left_eye[1]+displacement_right_eye[1])/2)
        displacement_eye_noisy = (max(min(1, displacement_eye_noisy[0]), -1), max(min(1, displacement_eye_noisy[1]), -1))
        displacement_eye = ((displacement_eye[0]*0.8+displacement_eye_noisy[0]*0.2), (displacement_eye[1]*0.8+displacement_eye_noisy[1]*0.2))
        lex1, ley1 = np.min(mesh_points[LEFT_EYE], axis=0)
        lex2, ley2 = np.max(mesh_points[LEFT_EYE], axis=0)
        rex1, rey1 = np.min(mesh_points[RIGHT_EYE], axis=0)
        rex2, rey2 = np.max(mesh_points[RIGHT_EYE], axis=0)
        lex1_ext, ley1_ext = np.min(mesh_points[LEFT_EYE_EXTENDED], axis=0)
        lex2_ext, ley2_ext = np.max(mesh_points[LEFT_EYE_EXTENDED], axis=0)
        rex1_ext, rey1_ext = np.min(mesh_points[RIGHT_EYE_EXTENDED], axis=0)
        rex2_ext, rey2_ext = np.max(mesh_points[RIGHT_EYE_EXTENDED], axis=0)
        if abs(lex1-lex2)/abs(ley1-ley2) > 5:
            left_eye_closed = True
        else:
            left_eye_closed = False
        if abs(rex1-rex2)/abs(rey1-rey2) > 5:
            right_eye_closed = True
        else:
            right_eye_closed = False
        if draw:
            frame = draw_tracking(frame, lex1, ley1, lex2, ley2, rex1, rey1, rex2, rey2, lex1_ext, ley1_ext, lex2_ext, ley2_ext, rex1_ext, rey1_ext, rex2_ext, rey2_ext)
    return frame

def main(draw=False):
    ret, frame = cap.read()
    update_mesh_points(frame)
    frame = eye_track(frame, draw=draw)
    frame = predict_emotion(frame, draw=draw)
    cv2.waitKey(1)
    return frame

if __name__ == "__main__":
    while True:
        frame = main(draw=True)
        print(displacement_eye, left_eye_closed, right_eye_closed)
        print(emotion_scores)
        cv2.imshow('frame', frame)