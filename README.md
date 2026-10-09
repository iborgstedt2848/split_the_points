# HARPER Project

## Introduction

Vassar's Cognitive Science Department is currently working on a project called HARPER, which stands for Humanoid Autonomous Robotic Platform for Experimental Research. The goal of this project is to create a humanoid robot that can be used for research in the cognitive sciences. The robot will be able to interact with humans and perform a variety of tasks, such as object recognition, speech recognition, and natural language processing. Creating this robot will also facilitate research into humanoid systems (movement, perception, comprehension, etc.)

## History

This project started in 2022. The main head of the project is Professor Ken Livingston. Much of the project work is accomplished through Vassar's URSI program

# Software-Side Overview

This project is a systems integration project. Here are the current discrete components of the project, software-wise:

1. Sight. See [./Seeing/README.md](./Seeing/README.md) for more information
2. Speech. See [./Speaking/README.md](./Speaking/README.md) for more information
3. Hearing. See [./Hearing/README.md](./Hearing/README.md) for more information

TO BE ADDED:

1. A Movement Controller Module
2. Advanced LLM-Powered Response Generation (likely with Ollama.ai)
3. A Primary Control System (Likely through ROS)

Integration of these components is the main goal of the project. The goal is to have the robot be able to see, hear, and speak to humans. This will allow for a more natural interaction between the robot and humans. One simple example of integration is `.Programs/repeat_after_me.py` which combines the hearing and speaking components.

# Hardware-Side Overview

HARPER is adapted from [InMoov's Open-Source 3d-printed robot](https://inmoov.fr/build-yours/). More details can be found at their website. The robot is controlled with an NVIDIA Jetson AGX Orin, which is a semipowerful AI-capable computer. The robot is equipped with a Luxonis OAK-D Pro camera, which is, similarly, a powerful AI camera.

The robot is also equipped with a microphone and speaker for speech recognition and synthesis. The latter two are generic components.
