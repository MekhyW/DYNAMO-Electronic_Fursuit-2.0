import numpy as np
import cv2
import mediapipe as mp
import math
displacement_eye = (0,0)
left_eye_closed = False
right_eye_closed = False
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
drawSpec = mp_drawing.DrawingSpec(thickness=1, circle_radius=2)
face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.5, min_tracking_confidence=0.5)
RIGHT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
LEFT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
RIGHT_EYE_EXTENDED = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398, 341, 256, 252, 253, 254, 339, 260, 259, 257, 258, 286, 414]
LEFT_EYE_EXTENDED = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246, 110, 24, 23, 22, 26, 112, 190, 56, 28, 27, 29, 30]  
LEFT_IRIS = [468, 469, 470, 471, 472]
RIGHT_IRIS = [473, 474, 475, 476, 477]

cap = cv2.VideoCapture(0)

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

def eye_track(frame, draw=True):
    global displacement_eye, left_eye_closed, right_eye_closed
    H, W, _ = frame.shape
    results_mesh = face_mesh.process(frame)
    if results_mesh.multi_face_landmarks:
        frame = compensate_head_roll(frame, results_mesh, W, H)
        results_mesh = face_mesh.process(frame)
    if results_mesh.multi_face_landmarks:
        mesh_points = np.array([np.multiply([p.x, p.y], [W, H]).astype(int) for p in results_mesh.multi_face_landmarks[0].landmark])
        lex1, ley1 = np.min(mesh_points[LEFT_EYE], axis=0)
        lex2, ley2 = np.max(mesh_points[LEFT_EYE], axis=0)
        rex1, rey1 = np.min(mesh_points[RIGHT_EYE], axis=0)
        rex2, rey2 = np.max(mesh_points[RIGHT_EYE], axis=0)
        lex1_ext, ley1_ext = np.min(mesh_points[LEFT_EYE_EXTENDED], axis=0)
        lex2_ext, ley2_ext = np.max(mesh_points[LEFT_EYE_EXTENDED], axis=0)
        rex1_ext, rey1_ext = np.min(mesh_points[RIGHT_EYE_EXTENDED], axis=0)
        rex2_ext, rey2_ext = np.max(mesh_points[RIGHT_EYE_EXTENDED], axis=0)
        displacement_left_eye = calculate_eye_displacement(mesh_points[LEFT_IRIS], lex1_ext, lex2_ext, ley1_ext, ley2_ext)
        displacement_right_eye = calculate_eye_displacement(mesh_points[RIGHT_IRIS], rex1_ext, rex2_ext, rey1_ext, rey2_ext)
        displacement_eye_noisy = ((displacement_left_eye[0]+displacement_right_eye[0])/2, (displacement_left_eye[1]+displacement_right_eye[1])/2)
        displacement_eye = ((displacement_eye[0]*0.8+displacement_eye_noisy[0]*0.2), (displacement_eye[1]*0.8+displacement_eye_noisy[1]*0.2))
        if abs(lex1-lex2)/abs(ley1-ley2) > 5:
            left_eye_closed = True
        else:
            left_eye_closed = False
        if abs(rex1-rex2)/abs(rey1-rey2) > 5:
            right_eye_closed = True
        else:
            right_eye_closed = False
        if draw:
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

while True:
    ret, frame = cap.read()
    frame = eye_track(frame)
    print(displacement_eye, left_eye_closed, right_eye_closed)
    cv2.imshow('frame', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break