import math

import rclpy
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from nav_msgs.msg import Odometry
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.time import Time
from sensor_msgs.msg import BatteryState
from tf2_ros import Buffer, TransformException, TransformListener

WORKING, DOCKING, CHARGING = 'WORKING', 'DOCKING', 'CHARGING'


class AutoDocking(Node):
    def __init__(self):
        super().__init__('auto_docking')

        # ---------------- parameters ----------------
        self.declare_parameter('dock_x', 0.0)
        self.declare_parameter('dock_y', 0.0)
        self.declare_parameter('dock_yaw', 0.0)
        self.declare_parameter('dock_tolerance', 0.35)   # m, "am I at the dock?"
        self.declare_parameter('low_battery', 20.0)      # %
        self.declare_parameter('full_battery', 100.0)    # %
        self.declare_parameter('idle_timeout', 20.0)     # s
        self.declare_parameter('drain_moving', 0.5)      # % per second
        self.declare_parameter('drain_idle', 0.02)       # % per second
        self.declare_parameter('charge_rate', 2.0)       # % per second
        self.declare_parameter('retry_delay', 5.0)       # s
        self.declare_parameter('odom_topic', '/rav_bot/odom')

        # ---------------- state ----------------
        self.battery = 100.0
        self.state = WORKING
        self.moving = False
        self.last_motion = self.now()
        self.next_attempt = 0.0

        # ---------------- ROS interfaces ----------------
        self.nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.create_subscription(Odometry, self.p('odom_topic'), self.odom_cb, 10)
        self.batt_pub = self.create_publisher(BatteryState, '/battery_state', 10)
        self.create_timer(1.0, self.loop)  # 1 Hz, dt = 1 s

        self.get_logger().info('Auto-docking node started')

    # ---------------- helpers ----------------
    def p(self, name):
        return self.get_parameter(name).value

    def now(self):
        return self.get_clock().now().nanoseconds * 1e-9

    def odom_cb(self, msg):
        v = msg.twist.twist.linear.x
        w = msg.twist.twist.angular.z
        self.moving = abs(v) > 0.02 or abs(w) > 0.05
        if self.moving:
            self.last_motion = self.now()

    def dist_to_dock(self):
        try:
            t = self.tf_buffer.lookup_transform('map', 'base_link', Time())
        except TransformException:
            return None
        dx = t.transform.translation.x - self.p('dock_x')
        dy = t.transform.translation.y - self.p('dock_y')
        return math.hypot(dx, dy)

    def publish_battery(self):
        msg = BatteryState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.percentage = self.battery / 100.0
        msg.present = True
        msg.power_supply_status = (
            BatteryState.POWER_SUPPLY_STATUS_CHARGING
            if self.state == CHARGING
            else BatteryState.POWER_SUPPLY_STATUS_DISCHARGING)
        self.batt_pub.publish(msg)

    # ---------------- main loop ----------------
    def loop(self):
        dt = 1.0

        # 1) simulated battery
        if self.state == CHARGING:
            self.battery += self.p('charge_rate') * dt
        elif self.moving:
            self.battery -= self.p('drain_moving') * dt
        else:
            self.battery -= self.p('drain_idle') * dt
        self.battery = max(0.0, min(100.0, self.battery))
        self.publish_battery()

        self.get_logger().info(
            f'[{self.state}] battery: {self.battery:.1f}%', throttle_duration_sec=5.0)

        # 2) where are we?
        dist = self.dist_to_dock()
        if dist is None:
            self.get_logger().warn(
                'No map->base_link transform yet (set the 2D Pose Estimate in RViz)',
                throttle_duration_sec=5.0)
            return
        at_dock = dist <= self.p('dock_tolerance')
        idle_for = self.now() - self.last_motion

        # 3) state machine (DOCKING is handled by the Nav2 goal callbacks)
        if self.state == CHARGING:
            if not at_dock:
                self.state = WORKING
            elif self.battery >= self.p('full_battery'):
                self.get_logger().info('Fully charged, back to WORKING')
                self.state = WORKING

        elif self.state == WORKING:
            if at_dock:
                if not self.moving and self.battery < self.p('full_battery'):
                    self.get_logger().info('At dock, start charging')
                    self.state = CHARGING
            elif self.now() >= self.next_attempt:
                if self.battery <= self.p('low_battery'):
                    self.start_docking(f'battery low ({self.battery:.1f}%)')
                elif idle_for >= self.p('idle_timeout'):
                    self.start_docking(f'idle for {idle_for:.0f}s')

    # ---------------- docking via Nav2 ----------------
    def start_docking(self, reason):
        if not self.nav_client.server_is_ready():
            self.get_logger().warn('Nav2 navigate_to_pose not ready yet',
                                   throttle_duration_sec=5.0)
            self.next_attempt = self.now() + self.p('retry_delay')
            return

        self.get_logger().info(f'Returning to dock: {reason}')
        self.state = DOCKING

        yaw = self.p('dock_yaw')
        goal = NavigateToPose.Goal()
        goal.pose = PoseStamped()
        goal.pose.header.frame_id = 'map'
        #goal.pose.header.stamp = self.get_clock().now().to_msg()
        goal.pose.header.stamp = Time().to_msg()
        goal.pose.pose.position.x = self.p('dock_x')
        goal.pose.pose.position.y = self.p('dock_y')
        goal.pose.pose.orientation.z = math.sin(yaw / 2.0)
        goal.pose.pose.orientation.w = math.cos(yaw / 2.0)

        self.nav_client.send_goal_async(goal).add_done_callback(self.goal_response_cb)

    def goal_response_cb(self, future):
        handle = future.result()
        if not handle.accepted:
            self.get_logger().warn('Dock goal rejected by Nav2')
            self.state = WORKING
            self.next_attempt = self.now() + self.p('retry_delay')
            return
        handle.get_result_async().add_done_callback(self.result_cb)

    def result_cb(self, future):
        status = future.result().status
        if status == GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().info('Docked successfully, charging...')
            self.state = CHARGING
        else:
            self.get_logger().warn(
                f'Docking goal ended with status {status}, will retry')
            self.state = WORKING
            self.next_attempt = self.now() + self.p('retry_delay')


def main():
    rclpy.init()
    node = AutoDocking()
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