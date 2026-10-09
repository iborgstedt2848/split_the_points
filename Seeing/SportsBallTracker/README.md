
One such example is the `sports_ball_tracker.py` file. This file is a simple example of how to track a ball and report its x/y/z coordinates and color. This is a simple example of how to use the camera to track objects in the environment.

# sports_ball_tracker.py

The goal of this file is to track a ball and report the x/y/z coordinates along with the color of the ball. The intent is to use this as a starting point for a larger project that will be able to track any YOLO-model object and report both coordinates and other ascertainable information (color is a simple example)

# Currently Implemented:

- Identifies a ball in the frame
- Reports x/y coordinates of the ball
- Identify the color of the ball
- Identify the depth of the ball (z coordinate)

# To be Implemented:

N/A

# Notes

Sometimes, you will run into an "interpreter shutdown" issue. This is a problem only for python v3.12+ due to threading issues. It SHOULD work for lesser versions of python. It has been tested with 3.9.0. See below for more information.
https://stackoverflow.com/questions/77631477/runtimeerror-cant-create-new-thread-at-interpreter-shutdown-python-3-12

# Resources of note:

https://docs.luxonis.com/projects/sdk/en/latest/samples/NNComponent/sdk_spatial_detection/
https://docs.luxonis.com/projects/sdk/en/latest/samples/NNComponent/sdk_yolo/
https://docs.luxonis.com/projects/sdk/en/latest/features/ai_models/#sdk-supported-models
https://docs.luxonis.com/projects/sdk/en/latest/samples/visualizer/SDK_visualizer_callback/?highlight=callback
