"""Laptop bringup — SLAM mode (mapping + Nav2).

Starts the EKF (single odom->base_link publisher, B4), slam_toolbox for
mapping, and the full Nav2 stack. Use during Local Lab Mode to build maps.

Save a finished map with:
  ros2 run nav2_map_server map_saver_cli -f /ultron_laptop/maps/map
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    nav2_bringup = get_package_share_directory('nav2_bringup')
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')

    return LaunchDescription([

        DeclareLaunchArgument('use_sim_time', default_value='false'),

        # EKF: single publisher of odom->base_link (v4.2 B4).
        Node(package='robot_localization', executable='ekf_node',
             name='ekf_filter_node', output='screen',
             parameters=['/ultron_laptop/config/ekf_params.yaml']),

        # SLAM mapping.
        Node(package='slam_toolbox', executable='sync_slam_toolbox_node',
             name='slam_toolbox', output='screen',
             parameters=['/ultron_laptop/config/slam_params.yaml']),

        # Full Nav2 stack (controller, planner, recoveries, costmaps, BT).
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                [nav2_bringup, '/launch/bringup_launch.py']),
            launch_arguments={
                'params_file': '/ultron_laptop/config/nav2_params.yaml',
                'use_sim_time': use_sim_time,
                'autostart': 'true',
                'map': '',
            }.items(),
        ),
    ])
