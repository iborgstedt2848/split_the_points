# Successfully counts colored balls

from depthai_sdk import OakCamera
import depthai as dai
import cv2
import numpy as np

# Function to create a mask for a specific color range
def create_color_mask(hsv_image, lower_bound, upper_bound):
    mask = cv2.inRange(hsv_image, lower_bound, upper_bound)
    return mask

# Function to count the number of contours detected in the mask
def count_contours(mask, min_area=500):
    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    filtered_contours = [contour for contour in contours if cv2.contourArea(contour) > min_area]
    return filtered_contours

# Custom clustering function based on simple distance threshold
def custom_cluster_contours(contours, distance_threshold=50):
    centers = [np.mean(contour, axis=0).astype(int).tolist()[0] for contour in contours]
    clusters = []
    for center in centers:
        added = False
        for cluster in clusters:
            if np.linalg.norm(np.array(cluster[0]) - np.array(center)) < distance_threshold:
                cluster.append(center)
                added = True
                break
        if not added:
            clusters.append([center])
    return len(clusters)

# Define color ranges for pink, green, and yellow in HSV
pink_lower = np.array([140, 50, 50])
pink_upper = np.array([170, 255, 255])

green_lower = np.array([40, 50, 50])
green_upper = np.array([70, 255, 255])

yellow_lower = np.array([20, 50, 50])
yellow_upper = np.array([30, 255, 255])

# Initialize the DepthAI pipeline
pipeline = dai.Pipeline()

# Create color camera node
cam_rgb = pipeline.create(dai.node.ColorCamera)
cam_rgb.setPreviewSize(640, 480)
cam_rgb.setInterleaved(False)
cam_rgb.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)

# Create XLinkOut node to stream frames to the host
xout_rgb = pipeline.create(dai.node.XLinkOut)
xout_rgb.setStreamName("rgb")
cam_rgb.preview.link(xout_rgb.input)

# Start the pipeline
with dai.Device(pipeline) as device:
    # Get output queue
    q_rgb = device.getOutputQueue(name="rgb", maxSize=4, blocking=False)

    while True:
        in_rgb = q_rgb.get()  # Blocking call, will wait until a new data has arrived
        frame = in_rgb.getCvFrame()
        hsv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Create masks for each color
        pink_mask = create_color_mask(hsv_image, pink_lower, pink_upper)
        green_mask = create_color_mask(hsv_image, green_lower, green_upper)
        yellow_mask = create_color_mask(hsv_image, yellow_lower, yellow_upper)
        
        # Detect contours
        pink_contours = count_contours(pink_mask)
        green_contours = count_contours(green_mask)
        yellow_contours = count_contours(yellow_mask)
        
        # Cluster contours to count balls
        pink_count = custom_cluster_contours(pink_contours)
        green_count = custom_cluster_contours(green_contours)
        yellow_count = custom_cluster_contours(yellow_contours)
        
        # Display the counts on the frame
        cv2.putText(frame, f'Pink Balls: {pink_count}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2)
        cv2.putText(frame, f'Green Balls: {green_count}', (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f'Yellow Balls: {yellow_count}', (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        
        cv2.imshow("Frame", frame)
        if cv2.waitKey(1) == ord('q'):
            break

    cv2.destroyAllWindows()