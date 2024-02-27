import numpy as np
from scipy.special import expit
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
RIGHT_EYE_EXTENDED = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398, 341, 256, 252, 253, 254, 339, 260, 259, 257, 258, 286, 414]
LEFT_EYE_EXTENDED = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246, 110, 24, 23, 22, 26, 112, 190, 56, 28, 27, 29, 30]  
LEFT_IRIS = [468, 469, 470, 471, 472]
RIGHT_IRIS = [473, 474, 475, 476, 477]

results_mesh = None
mesh_points = None
displacement_eye = (0,0)
left_eye_closeness = 0
right_eye_closeness = 0
emotion_labels = ['angry', 'disgusted', 'happy', 'neutral', 'sad', 'surprised']
emotion_labels_extra = ['hypnotic', 'heart', 'rainbow', 'nightmare', 'gears', 'sans']
emotion_scores = [0]*6

eye_tracking_mode = True
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

def calculate_roll_angle(landmarks):
    left_ear = np.array([landmarks[234].x, landmarks[234].y])
    right_ear = np.array([landmarks[454].x, landmarks[454].y])
    delta = right_ear - left_ear
    angle_deg = np.degrees(np.arctan2(delta[1], delta[0]))
    return angle_deg

def compensate_head_roll(frame, results_mesh, W, H):
    roll_angle_deg = calculate_roll_angle(results_mesh.multi_face_landmarks[0].landmark)
    M = cv2.getRotationMatrix2D((W/2, H/2), roll_angle_deg, 1)
    alpha = M[0, 0]
    beta = M[0, 1]
    frame = cv2.warpAffine(frame, np.array([[alpha, beta, (1 - alpha) * W / 2 - beta * H / 2],
                                            [-beta, alpha, beta * W / 2 + (1 - alpha) * H / 2]]), (W, H))
    return frame

def fit_ellipse(points):
    ellipse = cv2.fitEllipse(points)
    center, axes = ellipse[0], ellipse[1]
    return center, axes

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

def calculate_proximity(lower, upper, x):
    mid_point = (lower + upper) / 2
    proximity = (x - mid_point) / (upper - mid_point)
    return proximity

def calculate_eye_displacement(iris_points, ex1, ex2, ey1, ey2):
    eye_center = np.mean(iris_points, axis=0)
    displacement_x = 2*calculate_proximity(ex1, ex2, eye_center[0])
    displacement_y = -2*calculate_proximity(ey1, ey2, eye_center[1])
    displacement = (displacement_x, displacement_y)
    return displacement

def calculate_sclera_area(mesh_points):
    lex1, lex2 = mesh_points[33, 0], mesh_points[133, 0]
    rex1, rex2 = mesh_points[362, 0], mesh_points[263, 0]
    area_sclera_left = 0
    area_sclera_right = 0
    for i in range(len(LEFT_EYE) - 1):
        area_sclera_left += (mesh_points[LEFT_EYE[i], 0] * mesh_points[LEFT_EYE[i + 1], 1]) - (mesh_points[LEFT_EYE[i + 1], 0] * mesh_points[LEFT_EYE[i], 1])
    for i in range(len(RIGHT_EYE) - 1):
        area_sclera_right += (mesh_points[RIGHT_EYE[i], 0] * mesh_points[RIGHT_EYE[i + 1], 1]) - (mesh_points[RIGHT_EYE[i + 1], 0] * mesh_points[RIGHT_EYE[i], 1])
    area_sclera_left = abs(area_sclera_left / (2*(abs(lex1 - lex2)**2)))
    area_sclera_right = abs(area_sclera_right / (2*(abs(rex1 - rex2)**2)))
    return area_sclera_left, area_sclera_right

def calculate_width_over_height(mesh_points):
    lex1 = mesh_points[33][0]
    lex2 = mesh_points[133][0]
    rex1 = mesh_points[362][0]
    rex2 = mesh_points[263][0]
    ley1 = mesh_points[159][1]
    ley2 = mesh_points[145][1]
    rey1 = mesh_points[386][1]
    rey2 = mesh_points[374][1]
    reason_left = abs(lex1-lex2)/abs(ley1-ley2)
    reason_right = abs(rex1-rex2)/abs(rey1-rey2)
    if reason_left > 20: reason_left = 20
    if reason_right > 20: reason_right = 20
    return reason_left, reason_right

def update_mesh_points(frame):
    global results_mesh, mesh_points
    H, W, _ = frame.shape
    results_mesh_local = face_mesh.process(frame)
    if results_mesh_local.multi_face_landmarks:
        frame = compensate_head_roll(frame, results_mesh_local, W, H)
        results_mesh = face_mesh.process(frame)
    if results_mesh.multi_face_landmarks:
        mesh_points = np.array([np.multiply([p.x, p.y], [W, H]).astype(int) for p in results_mesh.multi_face_landmarks[0].landmark])

def draw_tracking(frame, lex1_ext, ley1_ext, lex2_ext, ley2_ext, rex1_ext, rey1_ext, rex2_ext, rey2_ext):
    global results_mesh, mesh_points
    if results_mesh.multi_face_landmarks is not None:
        for faceLms in results_mesh.multi_face_landmarks:
            mp_drawing.draw_landmarks(frame, faceLms, mp_face_mesh.FACEMESH_CONTOURS,drawSpec,drawSpec)
        ellipse_center_L, ellipse_axes_L = fit_ellipse(mesh_points[LEFT_IRIS])
        ellipse_center_R, ellipse_axes_R = fit_ellipse(mesh_points[RIGHT_IRIS])
        cv2.ellipse(frame, (int(ellipse_center_L[0]), int(ellipse_center_L[1])), (int(ellipse_axes_L[0]/2), int(ellipse_axes_L[1]/2)), 0, 0, 360, (0, 0, 255), 2)
        cv2.ellipse(frame, (int(ellipse_center_R[0]), int(ellipse_center_R[1])), (int(ellipse_axes_R[0]/2), int(ellipse_axes_R[1]/2)), 0, 0, 360, (0, 0, 255), 2)
        cv2.rectangle(frame, (lex1_ext, ley1_ext), (lex2_ext, ley2_ext), (0, 255, 0), 2)
        cv2.rectangle(frame, (rex1_ext, rey1_ext), (rex2_ext, rey2_ext), (0, 255, 0), 2)
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
    left_eye_closeness = 0.7 * left_eye_closeness + 0.3 * left_eye_closeness_noisy
    right_eye_closeness = 0.7 * right_eye_closeness + 0.3 * right_eye_closeness_noisy
    return left_eye_closeness, right_eye_closeness

def eye_track(frame, draw=False):
    global results_mesh, mesh_points, displacement_eye, left_eye_closeness, right_eye_closeness
    if eye_tracking_mode:
        H, W, _ = frame.shape
        if mesh_points is not None:
            lex1_ext, ley1_ext = np.min(mesh_points[LEFT_EYE_EXTENDED], axis=0)
            lex2_ext, ley2_ext = np.max(mesh_points[LEFT_EYE_EXTENDED], axis=0)
            rex1_ext, rey1_ext = np.min(mesh_points[RIGHT_EYE_EXTENDED], axis=0)
            rex2_ext, rey2_ext = np.max(mesh_points[RIGHT_EYE_EXTENDED], axis=0)
            left_eye_closeness, right_eye_closeness = calculate_eye_closeness(mesh_points)
            displacement_left_eye = calculate_eye_displacement(mesh_points[LEFT_IRIS], lex1_ext, lex2_ext, ley1_ext, ley2_ext)
            displacement_right_eye = calculate_eye_displacement(mesh_points[RIGHT_IRIS], rex1_ext, rex2_ext, rey1_ext, rey2_ext)
            displacement_eye_noisy = ((displacement_left_eye[0]+displacement_right_eye[0])/2, (displacement_left_eye[1]+displacement_right_eye[1])/2)
            displacement_eye_noisy = (max(min(1, displacement_eye_noisy[0]), -1), max(min(1, displacement_eye_noisy[1]), -1))
            displacement_eye = 0.5*np.array(displacement_eye) + 0.5*np.array(displacement_eye_noisy)
            if draw:
                frame = draw_tracking(frame, lex1_ext, ley1_ext, lex2_ext, ley2_ext, rex1_ext, rey1_ext, rex2_ext, rey2_ext)
    else:
        displacement_eye = (0,0)
        left_eye_closeness = 0
        right_eye_closeness = 0
    return frame

def main(draw=False):
    ret, frame = cap.read()
    if frame is not None:
        update_mesh_points(frame)
        frame = eye_track(frame, draw=draw)
        frame = predict_emotion(frame, draw=draw)
        cv2.waitKey(1)
        return frame
    else:
        open_camera(cap_id)
        return None

if __name__ == "__main__":
    open_camera(cap_id)
    while True:
        frame = main(draw=True)
        emotion_scores_rounded = [round(score, 2) for score in emotion_scores]
        print(displacement_eye, left_eye_closeness, right_eye_closeness, emotion_scores_rounded)
        if frame is not None:
            cv2.imshow('frame', frame)