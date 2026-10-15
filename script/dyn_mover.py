#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

class Mover(Node):
    def __init__(self):
        super().__init__('dyn_mover')
        self.pub = self.create_publisher(Twist, '/dyn_box/cmd_vel', 10)
        self.t = 0.0
        self.create_timer(0.1, self.tick)

    def tick(self):
        self.t += 0.1
        msg = Twist()
        msg.linear.x = 0.3 if int(self.t / 6) % 2 == 0 else -0.3  # 6 s dhahab, 6 s jey
        self.pub.publish(msg)

def main():
    rclpy.init()
    rclpy.spin(Mover())

if __name__ == '__main__':
    main()