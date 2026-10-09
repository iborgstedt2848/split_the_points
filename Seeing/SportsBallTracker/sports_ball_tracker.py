from depthai_sdk import OakCamera
import depthai as dai
import cv2
from depthai_sdk.classes import DetectionPacket
from depthai_sdk.visualize.visualizer_helper import FramePosition, VisualizerHelper
# Import the labels for the COCO dataset
# from labels import labels

def clamp(value, min_value, max_value):
    """Clamp a value between a minimum and maximum value."""
    return max(min_value, min(value, max_value))


def remap_bbox_to_pixel(x1, y1, x2, y2, frame_width, frame_height):
    """Take floats from 0 to 1 and remap them to frame pixel coordinates depending on the frame size."""
    # Clamp the values to be within the frame. This is necessary because the model can sometimes return values off-frame.
    x1 = clamp(int(x1 * frame_width), 0, frame_width)
    y1 = clamp(int(y1 * frame_height), 0, frame_height)
    x2 = clamp(int(x2 * frame_width), 0, frame_width)
    y2 = clamp(int(y2 * frame_height), 0, frame_height)
    return x1, y1, x2, y2


def get_color_in_region(frame, x1, y1, x2, y2, shrink_factor=0.8):
    """Get the average color in a region of the frame. RGB format"""
    # Shrink the region of interest to avoid the edges of the bounding box
    adjusted_half_sf = (1 - shrink_factor) / 2
    x_diff = x2 - x1
    y_diff = y2 - y1
    x1 = int(x1 + x_diff * adjusted_half_sf)
    x2 = int(x2 - x_diff * adjusted_half_sf)
    y1 = int(y1 + y_diff * adjusted_half_sf)
    y2 = int(y2 - y_diff * adjusted_half_sf)

    # Get the region of interest
    roi = frame[y1:y2, x1:x2]
    # Calculate the average color in the region
    avg_color = roi.mean(axis=0).mean(axis=0)
    return [int(val) for val in avg_color]


def put_text_on_image(frame, text, position_x, position_y, font_color=(0, 255, 0)):
    """Helper function to put multiple lines of text on an image."""
    label_lines = text.split('\n')
    # Set the font parameters
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    line_type = 2
    line_height = 20  # Approximate height of one line of text

    # Draw each line of text separately
    for i, line in enumerate(label_lines):
        # Calculate the position for the current line

        line_position = (position_x, position_y + line_height * (i + 1))
        # Draw the text line on the frame
        cv2.putText(frame,
                    line,
                    line_position,
                    font,
                    font_scale,
                    font_color,
                    line_type)


def custom_visualizer(packet: DetectionPacket):
    """Take in the packet (frame + other data) and draw a bounding box around detected sports balls."""
    # These are all items detected by the model. A list of all items can be found here:
    # possible labels: https://github.com/amikelive/coco-labels/blob/master/coco-labels-2014_2017.txt
    # Note that the ID is one less than the list number (since we zero-index)
    detections = packet.img_detections.detections
    for detection in detections:
        # For each detection, check if it's a sports ball (label 32). If not, skip it.
        if detection.label not in [32]:  # 32 = sports ball
            continue

        # Convert the float values to pixel values
        x1, y1, x2, y2 = remap_bbox_to_pixel(
            detection.xmin,
            detection.ymin,
            detection.xmax,
            detection.ymax,
            packet.frame.shape[1],
            packet.frame.shape[0])

        # Draw the bounding box on the frame
        cv2.rectangle(packet.frame, (x1, y1), (x2, y2),
                      color=(0, 255, 0), thickness=2)

        # 3D spatial coordinates of the detected object
        x, y, z = detection.spatialCoordinates.x, detection.spatialCoordinates.y, detection.spatialCoordinates.z
        # Get the average color in the region of the bounding box (color of the detected object)
        r, g, b = get_color_in_region(packet.frame, x1, y1, x2, y2)
        # print(f"Detected sports ball at ({x}, {y}, {z}) with color ({r}, {g}, {b})")

        # text = f"{labels[detection.label]}: {int(detection.confidence * 100)}%"

        # put_text_on_image(packet.frame, text, x1, y1 - 10,
                          #font_color=(r, g, b))

    # Show the frame with any bounding boxes and labels
    cv2.imshow(packet.name, packet.frame)


with OakCamera() as oak:
    color = oak.create_camera('color')
    # List of models that are supported out-of-the-box by the SDK:
    # https://docs.luxonis.com/projects/sdk/en/latest/features/ai_models/#sdk-supported-modelsons     
    # nn = oak.create_nn('yolov6nr3_coco_640x352', color, spatial=True) (Isaac's model)
    
    nn = oak.create_nn('yolov6n_coco_640x640', color, spatial=True) # (Isabelle's model)

    # Set the confidence threshold for the model to 20%=0.2 (default is 50%=0.5)
    nn.config_nn(conf_threshold=0.3, resize_mode=None)

    # From boilerplate code. This sets up the spatial location calculator for the model.
    nn.config_spatial(
        bb_scale_factor=0.8,  # Scaling bounding box before averaging the depth in that ROI
        lower_threshold=300,  # Discard depth points below 30cm
        upper_threshold=10000,  # Discard depth pints above 10m
        # Average depth points before calculating X and Y spatial coordinates:
        calc_algo=dai.SpatialLocationCalculatorAlgorithm.AVERAGE
    )

    # nn.config_tracker(
    #     tracker_type=dai.TrackerType.ZERO_TERM_COLOR_HISTOGRAM,
    #     # Track only sports balls (from the object map. If unspecified, track all object types)
    #     track_labels=[32],
    #     # track_labels=['person'] # Track only people (for coco datasets, person is 1st object in the map)
    #     assignment_policy=dai.TrackerIdAssignmentPolicy.SMALLEST_ID,
    #     max_obj=10,  # Max objects to track, which can improve performance
    #     threshold=0.1  # Tracker threshold
    # )

    # Create a visualizer but let us manually handle it with the callback
    oak.visualize([nn.out.main], callback=custom_visualizer)

    # See more data (e.g. depth/spatial data):
    # oak.visualize([nn.out.passthrough, nn.out.spatials])

    # Run the pipeline
    oak.start(blocking=True)
