FROM ros:humble-ros-base

ENV DEBIAN_FRONTEND=noninteractive
ENV ROS_DISTRO=humble

# ROS message packages the bridge needs + web runtime.
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-rosdep \
    ros-humble-rmw-cyclonedds-cpp \
    ros-humble-nav2-msgs \
    ros-humble-sensor-msgs \
    ros-humble-nav-msgs \
    ros-humble-geometry-msgs \
    ros-humble-std-msgs \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir fastapi "uvicorn[standard]" pydantic

ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ENV ROS_DOMAIN_ID=42

WORKDIR /ultron_web
COPY server/ server/
COPY static/ static/
COPY requirements.txt entrypoint.sh ./
RUN chmod +x entrypoint.sh

EXPOSE 8080
ENTRYPOINT ["/ultron_web/entrypoint.sh"]
