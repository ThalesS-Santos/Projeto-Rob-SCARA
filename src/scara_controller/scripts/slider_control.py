#!/usr/bin/env python3
import sys
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray
from python_qt_binding.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QPushButton
)
from python_qt_binding.QtCore import Qt, QTimer

SCALE = 10000
ARM = [
    ('joint_1', -3.1416, 3.1416),
    ('joint_2', -1.5708, 1.5708),
    ('joint_3', -0.22, 0.0),
    ('wrist_joint', -1.5708, 1.5708),
]
GRIPPER = ('gripper (fechar)', 0.0, 0.015)


class SliderControl(QWidget):
    def __init__(self, node):
        super().__init__()
        self.node = node
        self.arm_pub = node.create_publisher(Float64MultiArray, '/arm_controller/commands', 10)
        self.grip_pub = node.create_publisher(Float64MultiArray, '/gripper_controller/commands', 10)
        self.setWindowTitle('SCARA - Controle')
        layout = QVBoxLayout(self)
        self.sliders = []
        self.labels = []
        for name, lo, hi in ARM + [GRIPPER]:
            row = QHBoxLayout()
            title = QLabel(name)
            title.setMinimumWidth(110)
            slider = QSlider(Qt.Horizontal)
            slider.setRange(int(lo * SCALE), int(hi * SCALE))
            slider.setValue(0)
            slider.setMinimumWidth(300)
            value = QLabel('0.000')
            value.setMinimumWidth(60)
            slider.valueChanged.connect(self.update_labels)
            row.addWidget(title)
            row.addWidget(slider)
            row.addWidget(value)
            layout.addLayout(row)
            self.sliders.append(slider)
            self.labels.append(value)
        reset = QPushButton('Zerar tudo')
        reset.clicked.connect(self.reset)
        layout.addWidget(reset)
        self.timer = QTimer()
        self.timer.timeout.connect(self.publish)
        self.timer.start(100)

    def values(self):
        return [s.value() / SCALE for s in self.sliders]

    def update_labels(self):
        for label, v in zip(self.labels, self.values()):
            label.setText('%.3f' % v)

    def reset(self):
        for s in self.sliders:
            s.setValue(0)

    def publish(self):
        if not rclpy.ok():
            self.timer.stop()
            QApplication.quit()
            return
        try:
            v = self.values()
            self.arm_pub.publish(Float64MultiArray(data=v[:4]))
            self.grip_pub.publish(Float64MultiArray(data=[v[4]]))
            rclpy.spin_once(self.node, timeout_sec=0)
        except Exception:
            self.timer.stop()
            QApplication.quit()


def main():
    rclpy.init()
    node = Node('scara_slider_control')
    app = QApplication(sys.argv)
    win = SliderControl(node)
    win.show()
    try:
        code = app.exec_()
    except KeyboardInterrupt:
        code = 0
    finally:
        win.timer.stop()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    sys.exit(code)


if __name__ == '__main__':
    main()
