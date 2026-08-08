import launch
import launch_ros
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    params_file = '/ultron_ws/config/params.yaml'
    ekf_params_file = '/ultron_ws/config/ekf_params.yaml'
    logging_enabled = LaunchConfiguration('logging_enabled')
    mission_id = LaunchConfiguration('mission_id')
    ekf_onboard = LaunchConfiguration('ekf_onboard')

    return LaunchDescription([

        DeclareLaunchArgument('logging_enabled', default_value='false',
                              description='Enable onboard JSONL pilot logger'),
        DeclareLaunchArgument('mission_id', default_value='',
                              description='Pilot mission id (required if '
                                          'logging_enabled:=true)'),
        # P1 (audit): move EKF from the laptop to the Jetson to shrink the
        # network/clock dependency (risk R5). B4 rule: run this ONLY with the
        # laptop EKF disabled (laptop launch run_ekf:=false) so there is a
        # single odom->base_link publisher.
        DeclareLaunchArgument('ekf_onboard', default_value='false',
                              description='Run robot_localization EKF onboard '
                                          '(disable the laptop EKF: '
                                          'run_ekf:=false)'),

        # RPLiDAR A1M8 (Bible §9 NODE 1 uses the standalone rplidar_node).
        Node(package='rplidar_ros',
             executable='rplidar_node',
             name='rplidar', output='screen',
             parameters=[params_file]),

        Node(package='ultron_onboard',
             executable='kinect_driver_node',
             name='kinect_driver', output='screen',
             parameters=[params_file]),

        Node(package='ultron_onboard',
             executable='depth_to_scan_node',
             name='depth_to_scan', output='screen',
             parameters=[params_file]),

        Node(package='ultron_onboard',
             executable='safety_node',
             name='ultron_safety_node', output='screen',
             parameters=[params_file]),

        Node(package='ultron_onboard',
             executable='serial_node',
             name='ultron_serial_node', output='screen',
             parameters=[params_file]),

        # P1: onboard EKF (optional). Single odom->base_link publisher (B4).
        Node(package='robot_localization', executable='ekf_node',
             name='ekf_filter_node', output='screen',
             parameters=[ekf_params_file],
             condition=IfCondition(ekf_onboard)),

        # Static TFs — adjust xyz to physical measurements (Bible §2.3).
        Node(package='tf2_ros', executable='static_transform_publisher',
             name='base_to_laser',
             arguments=['0.10', '0.0', '0.12', '0', '0', '0', '1',
                        'base_link', 'laser_link']),

        Node(package='tf2_ros', executable='static_transform_publisher',
             name='base_to_kinect',
             # -10° pitch, half-angle: y=sin(-5°)=-0.08716, w=cos(-5°)=0.99619
             arguments=['0.05', '0.0', '0.30', '0', '-0.08716', '0', '0.99619',
                        'base_link', 'kinect_depth_frame']),

        Node(package='tf2_ros', executable='static_transform_publisher',
             name='base_to_imu',
             arguments=['0', '0', '0.05', '0', '0', '0', '1',
                        'base_link', 'imu_link']),

        # Optional pilot logging (Section 17) — disabled by default.
        Node(package='ultron_onboard', executable='data_logger_node',
             name='ultron_data_logger', output='screen',
             parameters=[params_file,
                         {'enabled': logging_enabled,
                          'mission_id': mission_id}]),
    ])
