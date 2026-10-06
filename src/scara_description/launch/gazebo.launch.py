import os
from ament_index_python.packages import get_package_share_directory, get_package_prefix

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable, TimerAction
from launch.conditions import IfCondition
from launch.substitutions import Command, LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue



def generate_launch_description():
    scara_description_dir = get_package_share_directory('scara_description')
    scara_description_share = os.path.join(get_package_prefix('scara_description'), 'share')
    scara_controller_lib = os.path.join(get_package_prefix('scara_controller'), 'lib')
    gazebo_ros_dir = get_package_share_directory('gazebo_ros')

    world_file = os.path.join(scara_description_dir, 'worlds', 'scara_pick.world')

    model_arg = DeclareLaunchArgument(
        name='model',
        default_value=os.path.join(
            scara_description_dir, 'urdf', 'scara.urdf.xacro'
        ),
        description='Absolute path to robot urdf file'
    )

    gui_arg = DeclareLaunchArgument(
        name='gui',
        default_value='true',
        description='Start the Gazebo graphical client'
    )

    model_path = os.pathsep.join(filter(None, [
        scara_description_share, os.environ.get('GAZEBO_MODEL_PATH', '')
    ]))
    env_var = SetEnvironmentVariable('GAZEBO_MODEL_PATH', model_path)
    plugin_path = os.pathsep.join(filter(None, [
        scara_controller_lib, os.environ.get('GAZEBO_PLUGIN_PATH', '')
    ]))
    plugin_env_var = SetEnvironmentVariable('GAZEBO_PLUGIN_PATH', plugin_path)

    robot_description = ParameterValue(
        Command(['xacro ', LaunchConfiguration('model')]),
        value_type=str
    )

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': True,
        }]
    )

    start_gazebo_server = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gazebo_ros_dir, 'launch', 'gzserver.launch.py')
        ),
        launch_arguments={
            'world': world_file,
            'server_required': 'true',
        }.items()
    )

    start_gazebo_client = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gazebo_ros_dir, 'launch', 'gzclient.launch.py')
        ),
        condition=IfCondition(LaunchConfiguration('gui'))
    )

    spawn_robot = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=['-entity', 'scara',
                   '-topic', 'robot_description',
                   '-timeout', '120',
                   ],
        output='screen'
    )

    spawn_robot_delayed = TimerAction(
        period=5.0,
        actions=[spawn_robot]
    )

    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager'],
    )

    arm_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['arm_controller', '--controller-manager', '/controller_manager'],
    )

    gripper_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['gripper_controller', '--controller-manager', '/controller_manager'],
    )

    controllers_delayed = TimerAction(
        period=12.0,
        actions=[
            joint_state_broadcaster_spawner,
            arm_controller_spawner,
            gripper_controller_spawner,
        ]
    )

    return LaunchDescription([
        env_var,
        plugin_env_var,
        model_arg,
        gui_arg,
        start_gazebo_server,
        start_gazebo_client,
        robot_state_publisher_node,
        spawn_robot_delayed,
        controllers_delayed,
    ])
