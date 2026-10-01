from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped
import math

# dans __init__ du nœud
self._nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')

def send_goal(self, x, y, yaw=0.0):
    if not self._nav_client.wait_for_server(timeout_sec=3.0):
        self.get_logger().error('Serveur Nav2 introuvable')
        return False

    goal = NavigateToPose.Goal()
    goal.pose = PoseStamped()
    goal.pose.header.frame_id = 'map'
    goal.pose.header.stamp = self.get_clock().now().to_msg()
    goal.pose.pose.position.x = float(x)
    goal.pose.pose.position.y = float(y)
    goal.pose.pose.orientation.z = math.sin(yaw / 2.0)
    goal.pose.pose.orientation.w = math.cos(yaw / 2.0)

    future = self._nav_client.send_goal_async(goal, feedback_callback=self._on_feedback)
    future.add_done_callback(self._on_goal_response)
    return True

def _on_goal_response(self, future):
    handle = future.result()
    if not handle.accepted:
        self.get_logger().error('Goal REFUSE par Nav2')
        return
    handle.get_result_async().add_done_callback(self._on_result)

def _on_result(self, future):
    self.get_logger().info(f'Statut final : {future.result().status}')