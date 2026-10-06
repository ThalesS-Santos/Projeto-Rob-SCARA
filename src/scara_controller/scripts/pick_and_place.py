#!/usr/bin/env python3

import math
import time

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from gazebo_msgs.msg import ModelStates
from std_msgs.msg import Float64MultiArray


ARM_JOINTS = ('joint_1', 'joint_2', 'joint_3', 'wrist_joint')
FIRST_ARM_LENGTH = 0.2
SECOND_ARM_LENGTH = 0.2562
FINGER_CENTER_HOME_Z = 0.21925
JOINT_3_MIN = -0.22
GRIPPER_OPEN = 0.0
GRIPPER_CLOSED_ON_CUBE = 0.006
CUBE_SIDE = 0.03
TARGET_TOP_OFFSET = 0.002


class PickAndPlace(Node):
    def __init__(self):
        super().__init__('scara_pick_and_place')
        self.arm_pub = self.create_publisher(
            Float64MultiArray, '/arm_controller/commands', 10)
        self.gripper_pub = self.create_publisher(
            Float64MultiArray, '/gripper_controller/commands', 10)
        self.create_subscription(JointState, '/joint_states', self.on_joints, 10)
        self.create_subscription(ModelStates, '/model_states', self.on_models, 10)
        self.joints = {}
        self.models = {}

    def on_joints(self, msg):
        self.joints.update(zip(msg.name, msg.position))

    def on_models(self, msg):
        self.models = dict(zip(msg.name, msg.pose))

    def wait_for_world(self, timeout=5.0):
        time.sleep(timeout)
        rclpy.spin_once(self, timeout_sec=0.1)

    def arm_state(self):
        return tuple(self.joints[name] for name in ARM_JOINTS)

    def solve_xy(self, x, y):
        cosine = ((x * x + y * y - FIRST_ARM_LENGTH ** 2
                   - SECOND_ARM_LENGTH ** 2)
                  / (2 * FIRST_ARM_LENGTH * SECOND_ARM_LENGTH))
        joint_2 = math.acos(cosine)
        joint_1 = (math.atan2(y, x)
                   - math.atan2(SECOND_ARM_LENGTH * math.sin(joint_2),
                                FIRST_ARM_LENGTH + SECOND_ARM_LENGTH * cosine))
        return joint_1, joint_2

    def extension_for_cube_height(self, cube_center_z):
        extension = cube_center_z - FINGER_CENTER_HOME_Z
        return extension

    def publish_arm(self, values):
        self.arm_pub.publish(Float64MultiArray(data=list(values)))

    def publish_gripper(self, value):
        self.gripper_pub.publish(Float64MultiArray(data=[float(value)]))

    def move_arm(self, target, description):
        self.get_logger().info(description)
        start = self.arm_state()
        duration = max(
            1.5,
            max(abs(a - b) for a, b in zip(start[:2], target[:2])) / 0.55,
            abs(start[2] - target[2]) / 0.045,
        )
        steps = math.ceil(duration * 20)
        started = time.monotonic()
        for step in range(1, steps + 1):
            fraction = step / steps
            self.publish_arm(tuple(a + (b - a) * fraction
                                   for a, b in zip(start, target)))
            rclpy.spin_once(self, timeout_sec=0.001)
            time.sleep(max(0.0, started + step * duration / steps - time.monotonic()))

        time.sleep(1.0)

    def set_gripper(self, target, description):
        self.get_logger().info(description)
        self.publish_gripper(target)
        time.sleep(1.0)

    def wait_for_cube_lift(self, start_z):
        time.sleep(1.0)

    def run(self):
        self.wait_for_world()
        home_arm = (0.0, 0.0, 0.0, 0.0)
        cube = self.models['caixa_a'].position
        target = self.models['zona_entrega'].position
        pickup_xy = self.solve_xy(cube.x, cube.y)
        drop_xy = self.solve_xy(target.x, target.y)
        pickup_wrist = -sum(pickup_xy)
        pickup_extension = self.extension_for_cube_height(cube.z + 0.012)
        drop_cube_z = target.z + TARGET_TOP_OFFSET + CUBE_SIDE / 2
        drop_extension = self.extension_for_cube_height(drop_cube_z + 0.015)
        travel_extension = max(pickup_extension + 0.12, -0.10)

        self.get_logger().info(f'cubo: {cube.x:.3f}, {cube.y:.3f}, {cube.z:.3f} \ alvo: {target.x:.3f}, {target.y:.3f}')
        self.set_gripper(GRIPPER_OPEN, 'abrindo garra')
        self.move_arm((*pickup_xy, 0.0, pickup_wrist), 'indo pra cima do cubo')
        self.move_arm((*pickup_xy, pickup_extension, pickup_wrist), 'descendo no cubo')
        self.set_gripper(GRIPPER_CLOSED_ON_CUBE, 'fechando garra')
        self.move_arm((*pickup_xy, travel_extension, pickup_wrist), 'subindo o cubo')
        self.wait_for_cube_lift(cube.z)
        self.move_arm((*drop_xy, travel_extension, pickup_wrist), 'indo pro circulo')
        self.move_arm((*drop_xy, drop_extension, pickup_wrist), 'descendo no circulo')
        self.set_gripper(GRIPPER_OPEN, 'soltando cubo')
        time.sleep(1.0)
        self.move_arm((*drop_xy, travel_extension, pickup_wrist), 'saindo de perto')
        self.move_arm(home_arm, 'voltando pra base')

        self.get_logger().info('acabou a dinamica')


def main():
    rclpy.init()
    node = PickAndPlace()
    try:
        node.run()
    except Exception as e:
        node.get_logger().error(f'problema: {e}')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
