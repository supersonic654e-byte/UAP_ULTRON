# Kinect 1414 camera calibration (intrinsics)

Calibrate the *color* and *depth* camera intrinsics so TF offsets and the
depth-to-scan projection are trustworthy. Record the output here after each
run (`calibration/camera_intrinsics_*.yaml`).

## Prerequisites (laptop container or native ROS 2)

```bash
sudo apt install -y ros-humble-camera-calibration
```

## Procedure

1. Print a large checkerboard (e.g. 9x6 inner corners, square = 0.024 m) and
   fix it to a rigid board.

2. Point the Kinect at the board from ~0.5-1.5 m and run:

```bash
ros2 run camera_calibration cameracalibrator \
    --size 9x6 --square 0.024 \
    --camera_name kinect_color \
    -i /kinect/color/image_raw -c /kinect/color/camera_info
```

   For depth (mono 16UC1):

```bash
ros2 run camera_calibration cameracalibrator \
    --size 9x6 --square 0.024 \
    --camera_name kinect_depth \
    -i /kinect/depth/image_raw -c /kinect/depth/camera_info
```

3. Move the board slowly to all corners of the view until "CALIBRATE"
   activates; press it, then SAVE and COMMIT.

4. Record the resulting `camera_intrinsics_<camera>.yaml` in
   `calibration/` (small, commit it).

## Verify

```bash
ros2 run camera_calibration camera_calibration_checker \
    --camera /kinect/depth/camera_info --frame /kinect/depth/image_raw
```

> The stock intrinsics used by `kinect_driver_node` (fx=fy=574.0527954,
> cx=319.5, cy=239.5) are factory values; a real calibration typically shifts
> them by <1%. Update `KINECT_FX/CX` in the node params if the calibration
> shows a larger shift.
