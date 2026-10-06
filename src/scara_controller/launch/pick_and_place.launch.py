import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    gui = LaunchConfiguration('gui')
    rviz = LaunchConfiguration('rviz')
    gazebo_launch = os.path.join(
        get_package_share_directory('scara_description'), 'launch', 'gazebo.launch.py')
    rviz_config = os.path.join(
        get_package_share_directory('scara_description'), 'rviz', 'display.rviz')

    return LaunchDescription([
        DeclareLaunchArgument('gui', default_value='true'),
        DeclareLaunchArgument('rviz', default_value='true'),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(gazebo_launch),
            launch_arguments={'gui': gui}.items()),
        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', rviz_config],
            parameters=[{'use_sim_time': True}],
            condition=IfCondition(rviz),
            output='screen'),
        TimerAction(
            period=5.0,
            actions=[Node(
                package='scara_controller',
                executable='pick_and_place.py',
                output='screen')]),
    ])
