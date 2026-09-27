#!/usr/bin/env python3
import sys
import rclpy
from nav2_simple_commander.robot_navigator import BasicNavigator
from geometry_msgs.msg import PoseStamped


def make_pose(navigator, x, y, yaw_w=1.0):
    pose = PoseStamped()
    pose.header.frame_id = 'map'
    pose.header.stamp = navigator.get_clock().now().to_msg()
    pose.pose.position.x = x
    pose.pose.position.y = y
    pose.pose.orientation.w = yaw_w
    return pose


# Position connue de départ (station de docking) - à ajuster avec tes vraies coordonnées
DOCK_POSE = {'x': 0.0, 'y': 0.0}

# Dictionnaire des tables - remplace par tes vraies coordonnées trouvées via Publish Point
TABLES = {
    'table1': {'x': 2.0, 'y': 1.0},
    'table2': {'x': 4.0, 'y': -1.5},
    'table3': {'x': 1.5, 'y': -3.0},
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in TABLES:
        print(f"Usage: python3 delivery_nav.py <{'|'.join(TABLES.keys())}>")
        sys.exit(1)

    target_name = sys.argv[1]
    target = TABLES[target_name]

    rclpy.init()
    navigator = BasicNavigator()

    dock_pose = make_pose(navigator, DOCK_POSE['x'], DOCK_POSE['y'])
    navigator.setInitialPose(dock_pose)

    navigator.waitUntilNav2Active()

    goal = make_pose(navigator, target['x'], target['y'])
    print(f"--> Navigation vers {target_name} (x={target['x']}, y={target['y']})")
    navigator.goToPose(goal)

    while not navigator.isTaskComplete():
        feedback = navigator.getFeedback()

    result = navigator.getResult()
    print(f"Arrivé à {target_name}. Résultat: {result}")

    rclpy.shutdown()


if __name__ == '__main__':
    main()

