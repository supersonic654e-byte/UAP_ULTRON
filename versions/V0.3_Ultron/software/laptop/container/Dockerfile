FROM ros:humble-desktop

# v4.2 B11: cap build parallelism.
ARG MAKEFLAGS=-j2

ENV DEBIAN_FRONTEND=noninteractive
ENV ROS_DISTRO=humble

RUN apt-get update && apt-get install -y \
    python3-colcon-common-extensions \
    python3-rosdep \
    ros-humble-navigation2 \
    ros-humble-nav2-bringup \
    ros-humble-robot-localization \
    ros-humble-slam-toolbox \
    ros-humble-nav2-map-server \
    ros-humble-rmw-cyclonedds-cpp \
    ros-humble-tf2-tools \
    ros-humble-teleop-twist-keyboard \
    ros-humble-rosbag2 \
    ros-humble-rosbag2-storage-mcap \
    ros-humble-diagnostic-updater \
    && rm -rf /var/lib/apt/lists/*

# v4.2 B3: CycloneDDS over Tailscale.
ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ENV ROS_DOMAIN_ID=42

WORKDIR /ultron_laptop
COPY config/ config/
COPY launch/ launch/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["ros2", "launch", "/ultron_laptop/launch/laptop_bringup.launch.py"]
