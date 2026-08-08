FROM ros:humble-ros-base

# v4.2 B11: cap build parallelism so the 4GB Nano does not OOM.
ARG MAKEFLAGS=-j2

ENV DEBIAN_FRONTEND=noninteractive
ENV ROS_DISTRO=humble

RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-serial \
    python3-numpy \
    python3-transforms3d \
    python3-pytest \
    setserial \
    libfreenect-dev \
    python3-freenect \
    usbutils \
    build-essential cmake git wget curl \
    ros-humble-rplidar-ros \
    ros-humble-sensor-msgs \
    ros-humble-nav-msgs \
    ros-humble-geometry-msgs \
    ros-humble-tf2-ros \
    ros-humble-tf2-geometry-msgs \
    ros-humble-rmw-cyclonedds-cpp \
    ros-humble-robot-localization \
    ros-humble-diagnostic-msgs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /ultron_ws
COPY src/ src/

RUN . /opt/ros/humble/setup.sh && \
    colcon build --symlink-install \
        --cmake-args -DCMAKE_BUILD_TYPE=Release \
    && rm -rf build log

COPY config/ config/
COPY launch/ launch/

# v4.2 B3: CycloneDDS over Tailscale (see Section 7).
ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ENV CYCLONEDDS_URI=file:///ultron_ws/config/cyclonedds.xml
ENV ROS_DOMAIN_ID=42

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["ros2", "launch", "/ultron_ws/launch/jetson_bringup.launch.py"]
