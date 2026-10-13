#!/usr/bin/env python3
"""Simulated 2-floor elevator for my_cafe_2floors.world.

Command :  ros2 topic pub --once /elevator/go_to std_msgs/msg/Int32 "{data: 2}"
Status  :  ros2 topic echo /elevator/status      ->  "floor=1 state=IDLE"

How it works (it is a *simulated* lift, not a physics lift):
  * if the robot is inside the cabin zone, doors close, the robot is lifted smoothly
    inside the shaft, then placed on the other floor at the same x,y, doors open;
  * if the robot is not inside, only the (empty) car moves to the requested floor.
Because both floors share the same x,y, the same map / AMCL pose stay valid.
"""
import time

import rclpy
from gazebo_msgs.msg import EntityState
from gazebo_msgs.srv import GetEntityState, SetEntityState
from geometry_msgs.msg import Twist
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile
from std_msgs.msg import Int32, String

IDLE, CLOSING, MOVING, OPENING = 'IDLE', 'CLOSING', 'MOVING', 'OPENING'


def smoothstep(a):
    a = max(0.0, min(1.0, a))
    return a * a * (3.0 - 2.0 * a)


class Elevator(Node):
    def __init__(self):
        super().__init__('elevator')
        d = self.declare_parameter
        d('robot_name', 'my_robot')
        d('floor_height', 3.0)       # must match H in the world file
        d('ride_height', 2.2)        # how high the robot rises before it is placed on floor 2
        d('door_time', 1.5)          # s
        d('travel_time', 5.0)        # s
        # zone (world frame, floor-1 coordinates) where the robot counts as "inside the cabin"
        d('zone_x_min', -4.25)
        d('zone_x_max', -3.35)
        d('zone_y_min', 5.55)
        d('zone_y_max', 7.05)
        # door geometry (must match the world file)
        d('door_y', 5.05)
        d('door_z', 1.34)            # door centre height on floor 1
        d('door_closed_left_x', -4.15)
        d('door_closed_right_x', -3.45)
        d('door_slide', 0.45)
        d('cmd_vel_topic', '/rav_bot/cmd_vel')
        d('get_state_service', '/get_entity_state')
        d('set_state_service', '/set_entity_state')

        self.get_cli = self.create_client(GetEntityState, self.p('get_state_service'))
        self.set_cli = self.create_client(SetEntityState, self.p('set_state_service'))
        self.cmd_pub = self.create_publisher(Twist, self.p('cmd_vel_topic'), 10)
        latched = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.status_pub = self.create_publisher(String, '/elevator/status', latched)
        self.create_subscription(Int32, '/elevator/go_to', self.on_request, 10)

        self.car_floor = 1
        self.target = 1
        self.phase = IDLE
        self.t0 = 0.0
        self.carrying = False
        self.ride = None
        self.robot_pose = None
        self.robot_stamp = 0.0
        self.poll_pending = False
        self.init_done = False

        self.create_timer(0.05, self.tick)        # 20 Hz animation
        self.create_timer(0.2, self.poll_robot)   # 5 Hz robot pose
        self.create_timer(1.0, self.publish_status)
        self.get_logger().info('Elevator node started (car on floor 1). '
                               'Send floor numbers to /elevator/go_to')

    # ------------------------------------------------------------ helpers
    def p(self, name):
        return self.get_parameter(name).value

    def floor_of(self, z):
        return 1 if z < self.p('floor_height') / 2.0 else 2

    def publish_status(self):
        msg = String()
        msg.data = f'floor={self.car_floor} state={self.phase}'
        self.status_pub.publish(msg)

    def zero_cmd(self):
        self.cmd_pub.publish(Twist())

    # ------------------------------------------------------------ gazebo I/O
    def poll_robot(self):
        if self.poll_pending or not self.get_cli.service_is_ready():
            return
        req = GetEntityState.Request()
        req.name = self.p('robot_name')
        req.reference_frame = 'world'
        self.poll_pending = True
        self.get_cli.call_async(req).add_done_callback(self.on_robot)

    def on_robot(self, fut):
        self.poll_pending = False
        try:
            res = fut.result()
        except Exception:
            return
        if res is not None and res.success:
            self.robot_pose = res.state.pose
            self.robot_stamp = time.monotonic()

    def set_model(self, name, x, y, z, q=(0.0, 0.0, 0.0, 1.0)):
        if not self.set_cli.service_is_ready():
            return
        st = EntityState()
        st.name = name
        st.reference_frame = 'world'
        st.pose.position.x = float(x)
        st.pose.position.y = float(y)
        st.pose.position.z = float(z)
        st.pose.orientation.x, st.pose.orientation.y = q[0], q[1]
        st.pose.orientation.z, st.pose.orientation.w = q[2], q[3]
        req = SetEntityState.Request()
        req.state = st
        self.set_cli.call_async(req).add_done_callback(self.on_set)

    def on_set(self, fut):
        try:
            res = fut.result()
        except Exception:
            return
        if res is not None and not res.success:
            self.get_logger().warn(f'set_entity_state failed: {res.status_message}',
                                   throttle_duration_sec=5.0)

    def set_doors(self, floor, openness):
        s = self.p('door_slide') * openness
        z = self.p('door_z') + (floor - 1) * self.p('floor_height')
        y = self.p('door_y')
        self.set_model(f'elev_door_f{floor}_L', self.p('door_closed_left_x') - s, y, z)
        self.set_model(f'elev_door_f{floor}_R', self.p('door_closed_right_x') + s, y, z)

    def set_robot(self, z):
        r = self.ride
        self.set_model(self.p('robot_name'), r['x'], r['y'], z, r['q'])

    # ------------------------------------------------------------ logic
    def robot_inside(self):
        if self.robot_pose is None or time.monotonic() - self.robot_stamp > 1.0:
            return False
        pos = self.robot_pose.position
        return (self.floor_of(pos.z) == self.car_floor
                and self.p('zone_x_min') <= pos.x <= self.p('zone_x_max')
                and self.p('zone_y_min') <= pos.y <= self.p('zone_y_max'))

    def on_request(self, msg):
        f = int(msg.data)
        if f not in (1, 2):
            self.get_logger().warn(f'Floor {f} does not exist (1 or 2)')
            return
        if self.phase != IDLE:
            self.get_logger().warn('Elevator is busy, request ignored')
            return
        if f == self.car_floor:
            self.get_logger().info(f'Elevator already on floor {f}')
            return
        self.target = f
        self.carrying = self.robot_inside()
        who = 'carrying the robot' if self.carrying else 'empty (robot not inside the cabin)'
        self.get_logger().info(f'Going {self.car_floor} -> {f}, {who}')
        self.phase = CLOSING
        self.t0 = time.monotonic()
        self.publish_status()

    def begin_move(self, now):
        self.phase = MOVING
        self.t0 = now
        self.zero_cmd()
        self.publish_status()
        if not self.carrying:
            return
        pos, o = self.robot_pose.position, self.robot_pose.orientation
        H, rh = self.p('floor_height'), self.p('ride_height')
        self.ride = {'x': pos.x, 'y': pos.y, 'q': (o.x, o.y, o.z, o.w), 'z0': pos.z}
        if self.target > self.car_floor:          # going up: rise first, jump to floor 2 at the end
            self.z_from, self.z_to = pos.z, pos.z + rh
        else:                                     # going down: appear high in the shaft, then descend
            base = pos.z - H
            self.z_from, self.z_to = base + rh, base + 0.02
            self.set_robot(self.z_from)

    def finish_move(self, now):
        if self.carrying and self.target > self.car_floor:
            self.set_robot(self.ride['z0'] + self.p('floor_height') + 0.02)
        self.car_floor = self.target
        self.zero_cmd()
        self.phase = OPENING
        self.t0 = now
        self.publish_status()

    def tick(self):
        now = time.monotonic()
        if not self.init_done:
            if self.set_cli.service_is_ready():
                self.set_doors(1, 1.0)
                self.set_doors(2, 0.0)
                self.init_done = True
            return
        if self.phase == IDLE:
            return
        t = now - self.t0
        if self.phase == CLOSING:
            a = min(t / self.p('door_time'), 1.0)
            self.set_doors(self.car_floor, 1.0 - a)
            if a >= 1.0:
                self.begin_move(now)
        elif self.phase == MOVING:
            a = min(t / self.p('travel_time'), 1.0)
            if self.carrying:
                self.set_robot(self.z_from + (self.z_to - self.z_from) * smoothstep(a))
            if a >= 1.0:
                self.finish_move(now)
        elif self.phase == OPENING:
            a = min(t / self.p('door_time'), 1.0)
            self.set_doors(self.car_floor, a)
            if a >= 1.0:
                self.phase = IDLE
                self.get_logger().info(f'Arrived at floor {self.car_floor}, doors open')
                self.publish_status()


def main():
    rclpy.init()
    node = Elevator()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
