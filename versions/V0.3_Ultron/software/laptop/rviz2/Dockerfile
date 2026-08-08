FROM ros:humble-desktop

ENV DEBIAN_FRONTEND=noninteractive
ENV ROS_DISTRO=humble

RUN apt-get update && apt-get install -y \
    ros-humble-rmw-cyclonedds-cpp \
    ros-humble-rviz2 \
    && rm -rf /var/lib/apt/lists/*

ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ENV ROS_DOMAIN_ID=42

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["rviz2", "-d", "/ultron_rviz/ultron.rviz"]
