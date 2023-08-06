import numpy as np
import cv2
import mediapipe as mp
displacement_eye = (0,0)
left_eye_closed = False
right_eye_closed = False
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
drawSpec = mp_drawing.DrawingSpec(thickness=1, circle_radius=2)
face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.5, min_tracking_confidence=0.5)
left_limit = 0.4
right_limit = -0.4
up_limit = -0.1
down_limit = 0.15
RIGHT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
LEFT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
RIGHT_EYE_EXTENDED = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398, 341, 256, 252, 253, 254, 339, 260, 259, 257, 258, 286, 414]
LEFT_EYE_EXTENDED = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246, 110, 24, 23, 22, 26, 112, 190, 56, 28, 27, 29, 30]  
LEFT_IRIS = [468, 469, 470, 471, 472]
RIGHT_IRIS = [473, 474, 475, 476, 477]

cap = cv2.VideoCapture(0)

def fit_ellipse(points):
    ellipse = cv2.fitEllipse(points)
    center, axes = ellipse[0], ellipse[1]
    return center, axes

def calculate_eye_displacement(eye_points, iris_points):
    center, axes = fit_ellipse(eye_points)
    eye_center = np.mean(iris_points, axis=0)
    displacement = (2*(center[0] - eye_center[0]) / (axes[0]), 2*(center[1] - eye_center[1]) / (axes[1]))
    displacement = (displacement[0]/(right_limit-left_limit), displacement[1]/(down_limit-up_limit))
    return displacement

def eye_track(frame):
    global displacement_eye, left_eye_closed, right_eye_closed
    H, W, _ = frame.shape
    rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results_mesh = face_mesh.process(rgb_image)
    if results_mesh.multi_face_landmarks:
        mesh_points = np.array([np.multiply([p.x, p.y], [W, H]).astype(int) for p in results_mesh.multi_face_landmarks[0].landmark])
        displacement_left_eye = calculate_eye_displacement(mesh_points[LEFT_EYE_EXTENDED], mesh_points[LEFT_IRIS])
        displacement_right_eye = calculate_eye_displacement(mesh_points[RIGHT_EYE_EXTENDED], mesh_points[RIGHT_IRIS])
        displacement_eye = ((displacement_left_eye[0]+displacement_right_eye[0])/2, (displacement_left_eye[1]+displacement_right_eye[1])/2)
        lex1, ley1 = np.min(mesh_points[LEFT_EYE], axis=0)
        lex2, ley2 = np.max(mesh_points[LEFT_EYE], axis=0)
        rex1, rey1 = np.min(mesh_points[RIGHT_EYE], axis=0)
        rex2, rey2 = np.max(mesh_points[RIGHT_EYE], axis=0)
        lex1_ext, ley1_ext = np.min(mesh_points[LEFT_EYE_EXTENDED], axis=0)
        lex2_ext, ley2_ext = np.max(mesh_points[LEFT_EYE_EXTENDED], axis=0)
        rex1_ext, rey1_ext = np.min(mesh_points[RIGHT_EYE_EXTENDED], axis=0)
        rex2_ext, rey2_ext = np.max(mesh_points[RIGHT_EYE_EXTENDED], axis=0)
        if abs(lex1-lex2)/abs(ley1-ley2) > 4:
            left_eye_closed = True
        else:
            left_eye_closed = False
        if abs(rex1-rex2)/abs(rey1-rey2) > 4:
            right_eye_closed = True
        else:
            right_eye_closed = False
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

while True:
    ret, frame = cap.read()
    eye_track(frame)
    print(displacement_eye, left_eye_closed, right_eye_closed)
    cv2.imshow('frame', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break