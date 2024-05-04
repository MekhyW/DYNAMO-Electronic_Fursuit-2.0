import cv2
import numpy as np

def resize_image(image, target_width=480):
    h, w = image.shape[:2]
    resized_image = cv2.resize(image, (target_width, int(target_width/(w/h))), interpolation=cv2.INTER_NEAREST)
    return resized_image

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

image = cv2.imread('Test scripts/distorted_image.jpg')
undistorted_image = undistort_image(resize_image(image))

cv2.imshow('Original Image', image)
cv2.imshow('Undistorted Image', undistorted_image)
cv2.waitKey(0)
cv2.destroyAllWindows()
