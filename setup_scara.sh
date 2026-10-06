#!/bin/bash

set -e


sudo apt update && sudo apt upgrade -y

sudo apt install -y software-properties-common curl


sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
    -o /usr/share/keyrings/ros-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
    | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

sudo apt update
sudo apt install -y ros-humble-desktop


sudo apt install -y gazebo libgazebo-dev

sudo apt install -y \
    ros-humble-gazebo-ros \
    ros-humble-gazebo-ros2-control \
    ros-humble-gazebo-plugins \
    ros-humble-ros2-control \
    ros-humble-ros2-controllers \
    ros-humble-forward-command-controller \
    ros-humble-joint-state-broadcaster \
    ros-humble-joint-state-publisher-gui \
    ros-humble-robot-state-publisher \
    ros-humble-xacro \
    ros-humble-rviz2 \
    python3-colcon-common-extensions \
    python3-rosdep

cd ~
git clone https://github.com/ThalesS-Santos/Projeto-Rob-SCARA.git scara_ws

cd ~/scara_ws
source /opt/ros/humble/setup.bash
colcon build


echo "" >> ~/.bashrc
echo "# ROS2 e SCARA" >> ~/.bashrc
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
echo "source ~/scara_ws/install/setup.bash" >> ~/.bashrc


