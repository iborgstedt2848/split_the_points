from depthai_sdk import OakCamera
import cv2


from depthai_sdk.classes.packets import ImgLandmarksPacket
from depthai_sdk.visualize.visualizer_helper import FramePosition, VisualizerHelper
from labels import labels
import numpy as np


# Clamp code is from Isaac's sports ball code
def clamp(value, min_value, max_value):
    """Clamp a value between a minimum and maximum value."""
    return max(min_value, min(value, max_value))


def remap_points_to_pixel(x1, y1, x2, y2, frame_width, frame_height):
    """Take floats from 0 to 1 and remap them to frame pixel coordinates depending on the frame size."""
    # Clamp the values to be within the frame. This is necessary because the model can sometimes return values off-frame.
    x1 = clamp(int(x1 * frame_width), 0, frame_width)
    y1 = clamp(int(y1 * frame_height), 0, frame_height)
    x2 = clamp(int(x2 * frame_width), 0, frame_width)
    y2 = clamp(int(y2 * frame_height), 0, frame_height)
    return x1, y1, x2, y2


def calculate_angle(a, b, c):
    """Calculate the angle between three points.
    The angle is calculated at point 'b' between lines 'ab' and 'bc'.
    """
    ab = np.array(a) - np.array(b)
    bc = np.array(c) - np.array(b)

    cosine_angle = np.dot(ab, bc) / (np.linalg.norm(ab) * np.linalg.norm(bc))
    angle = np.arccos(cosine_angle)

    return np.degrees(angle)


landmarks_to_observe = set([
    "ClavicleRight",  # 0
    "ClavicleLeft",   # 1
    "UpperArmRight",  # 2
    "LowerArmRight",  # 3
    "UpperArmLeft",   # 4
    "LowerArmLeft",   # 5
    "TorsoRight",     # 6
    "TorsoLeft",      # 9
    "Neck",           # 12
])


def filter_landmarks(landmarks, indices):
    """Filter landmarks to only include the ones we want to observe (as defined in landmarks_to_observe)."""
    filtered_landmarks = []
    filtered_indices = []
    for (landmark, index) in zip(landmarks, indices):
        if labels[index] in landmarks_to_observe:
            filtered_landmarks.append(landmark)
            filtered_indices.append(index)
    return filtered_landmarks, filtered_indices


def draw_landmark(frame, landmark, index):
    """Given a frame, landmark, and the index (ID) of the landmark, draw the landmark on the frame."""
    x1, y1, x2, y2 = remap_points_to_pixel(
        landmark[0][0], landmark[0][1],
        landmark[1][0], landmark[1][1],
        frame.shape[1], frame.shape[0])

    cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

    midpoint_x = (x1 + x2) // 2
    midpoint_y = (y1 + y2) // 2
    text = f"{index}: {labels[index]}"
    cv2.putText(frame, text, (midpoint_x, midpoint_y), cv2.FONT_HERSHEY_SIMPLEX,
                0.8, (0, 0, 255), 2)


def callback(packet: ImgLandmarksPacket):
    """Handle the pose estimation packet and make calls to draw the landmarks on the frame."""

    # We need to add this check because if there are no landmarks detected,
    # packet.landmarks.landmarks[0] would be out of range
    if len(packet.landmarks.landmarks) > 0:

        # Filter the landmarks to only include the ones we want to observe
        landmarks, indices = filter_landmarks(
            packet.landmarks.landmarks[0],
            packet.landmarks.landmarks_indices[0])

        # Draw the filtered landmarks on the frame
        for landmark, index in zip(landmarks, indices):
            draw_landmark(packet.frame, landmark, index)

    # Regardless of whether landmarks were detected or not, we display the frame
    # If they were detected, the added visuals will be displayed as part of the frame
    cv2.imshow(packet.name, packet.frame)


with OakCamera() as oak:
    color = oak.create_camera('color')
    human_pose_nn = oak.create_nn('human-pose-estimation-0001', color)
    oak.visualize(human_pose_nn, callback=callback)
    # oak.visualize(human_pose_nn)
    oak.start(blocking=True)
