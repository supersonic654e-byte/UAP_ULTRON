"""Laptop bringup — LOCALIZATION mode (saved map + AMCL + Nav2).

Use in Field Deployment Mode (§16.3): robot localizes against a saved map.
Args: map:=/path/to/map.yaml  (default /ultron_laptop/maps/map.yaml)
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
    map_yaml = LaunchConfiguration('map',
                                   default='/ultron_laptop/maps/map.yaml')

    return LaunchDescription([

        DeclareLaunchArgument('use_sim_time', default_value='false'),
        DeclareLaunchArgument('map', default_value='/ultron_laptop/maps/map.yaml'),

        # EKF: single publisher of odom->base_link (v4.2 B4).
        Node(package='robot_localization', executable='ekf_node',
             name='ekf_filter_node', output='screen',
             parameters=['/ultron_laptop/config/ekf_params.yaml']),

        # Nav2 localization_launch starts map_server + AMCL + lifecycle manager.
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                [nav2_bringup, '/launch/localization_launch.py']),
            launch_arguments={
                'map': map_yaml,
                'params_file': '/ultron_laptop/config/nav2_params.yaml',
                'use_sim_time': use_sim_time,
                'autostart': 'true',
            }.items(),
        ),
    ])
