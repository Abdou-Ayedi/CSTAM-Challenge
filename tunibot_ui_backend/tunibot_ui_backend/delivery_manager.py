"""Gestionnaire de livraisons : file FIFO + batterie simulee + retour au dock.
 
Etats robot : IDLE, DELIVERING, RETURNING (vers le dock), CHARGING
Statuts commande : PENDING, IN_PROGRESS, DELIVERED, FAILED, CANCELLED
"""
import json
import math
import os
import threading
from collections import deque
 
import yaml
from ament_index_python.packages import get_package_share_directory
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.parameter import Parameter
from sensor_msgs.msg import BatteryState
from std_msgs.msg import String
from builtin_interfaces.msg import Time
 
 
class DeliveryManager(Node):
    def __init__(self):
        super().__init__('delivery_manager')
        share = get_package_share_directory('tunibot_ui_backend')
        self.declare_parameter('locations_file', os.path.join(share, 'config', 'locations.yaml'))
        self.declare_parameter('low_battery', 20.0)        # % : declenche le retour au dock
        self.declare_parameter('resume_battery', 90.0)     # % : reprise des commandes si la file n'est pas vide
        self.declare_parameter('drain_moving', 0.4)        # % par seconde en deplacement
        self.declare_parameter('drain_idle', 0.02)         # % par seconde a l'arret
        self.declare_parameter('charge_rate', 2.0)         # % par seconde sur le dock
        self.declare_parameter('idle_return_s', 15.0)      # retour au dock apres N s sans commande
        self.declare_parameter('max_attempts', 2)
 
        self.low = self.get_parameter('low_battery').value
        self.resume = self.get_parameter('resume_battery').value
        self.drain_moving = self.get_parameter('drain_moving').value
        self.drain_idle = self.get_parameter('drain_idle').value
        self.charge_rate = self.get_parameter('charge_rate').value
        self.idle_return = self.get_parameter('idle_return_s').value
        self.max_attempts = self.get_parameter('max_attempts').value
 
        with open(self.get_parameter('locations_file').value) as f:
            data = yaml.safe_load(f)
        # accepte "locations: {...}" ou directement "{dock: ..., table_1: ...}"
        self.locations = data.get('locations', data)
        if 'dock' not in self.locations:
            self.get_logger().error("locations.yaml doit contenir une entree 'dock'")
 
        self.lock = threading.RLock()
        self.queue = deque()        # commandes PENDING, dans l'ordre d'arrivee (FIFO)
        self.orders = []            # toutes les commandes (historique affiche par le dashboard)
        self.current = None
        self.state = 'IDLE'
        self.reason = ''
        self.battery = 100.0
        self.at_dock = True
        self.pose = None
        self._handle = None
        self._next_id = 0
        self._seq = 0
        self._retry_until = 0.0
        self._last_t = self._now()
        self._idle_since = self._last_t
 
        self.nav = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self.battery_pub = self.create_publisher(BatteryState, '/battery_state', 10)
        self.status_pub = self.create_publisher(String, '/delivery_status', 10)
        self.create_subscription(PoseWithCovarianceStamped, 'amcl_pose', self._on_pose, 10)
        self.create_timer(0.5, self._tick)
        self.get_logger().info(f'Lieux charges : {list(self.locations)}')
 
    # ---------- API utilisee par le serveur web ----------
    def add_order(self, item, destination):
        with self.lock:
            if destination == 'dock' or destination not in self.locations:
                raise ValueError(f'Destination inconnue : {destination}')
            self._next_id += 1
            order = {'id': self._next_id, 'item': item, 'destination': destination,
                     'status': 'PENDING', 'attempts': 0}
            self.orders.append(order)
            if len(self.orders) > 200:
                del self.orders[0]
            self.queue.append(order)
            return dict(order)
 
    def recent_orders(self, n=50):
        with self.lock:
            return [dict(o) for o in self.orders[-n:]][::-1]      # les plus recentes d'abord
 
    def snapshot(self):
        with self.lock:
            return {
                'state': self.state,
                'reason': self.reason,
                'battery': round(self.battery, 1),
                'at_dock': self.at_dock,
                'pose': self.pose,
                'nav2_ready': self.nav.server_is_ready(),
                'current': dict(self.current) if self.current else None,
                'queue_length': len(self.queue),
            }
 
    def request_dock(self):
        """Retour manuel au dock (la livraison en cours est remise en tete de file)."""
        with self.lock:
            if self.state == 'RETURNING':
                return 'already_returning'
            if self.at_dock and self.state in ('IDLE', 'CHARGING'):
                return 'already_at_dock'
            self._retry_until = 0.0
            self._start_dock('manuel')
            return self.state.lower()
 
    def cancel(self):
        """Annule la mission en cours (livraison ou retour au dock)."""
        with self.lock:
            if self.state not in ('DELIVERING', 'RETURNING'):
                return 'nothing_to_cancel'
            self._seq += 1                       # les callbacks du goal annule seront ignores
            if self._handle is not None:
                self._handle.cancel_goal_async()
                self._handle = None
            if self.current:
                self.current['status'] = 'CANCELLED'
                self.current = None
            self.state = 'IDLE'
            self.reason = 'annule'
            self._idle_since = self._now()
            return 'cancelled'
 
    def set_battery(self, level):
        with self.lock:
            self.battery = max(0.0, min(100.0, float(level)))
 
    # ---------- boucle principale ----------
    def _now(self):
        return self.get_clock().now().nanoseconds / 1e9
 
    def _on_pose(self, msg):
        p = msg.pose.pose.position
        self.pose = {'x': round(p.x, 2), 'y': round(p.y, 2)}
 
    def _tick(self):
        with self.lock:
            now = self._now()
            dt = min(max(now - self._last_t, 0.0), 1.0)
            self._last_t = now
            self._update_battery(dt)
            self._publish()
            if now < self._retry_until:
                return
 
            if self.state in ('IDLE', 'DELIVERING') and self.battery <= self.low:
                self._start_dock('batterie faible')
                return
 
            if self.state == 'IDLE':
                if self.queue:
                    self._start_delivery(self.queue.popleft())
                elif not self.at_dock and now - self._idle_since >= self.idle_return:
                    self._start_dock('inactif')
            elif self.state == 'CHARGING':
                full = self.battery >= 100.0
                can_resume = bool(self.queue) and self.battery >= self.resume
                if full or can_resume:
                    self.state = 'IDLE'
                    self.reason = ''
                    self._idle_since = now
 
    def _update_battery(self, dt):
        if self.state in ('DELIVERING', 'RETURNING'):
            self.battery -= self.drain_moving * dt
        elif self.state == 'CHARGING':
            self.battery += self.charge_rate * dt
        else:
            self.battery -= self.drain_idle * dt
        self.battery = max(0.0, min(100.0, self.battery))
 
    def _publish(self):
        b = BatteryState()
        b.header.stamp = self.get_clock().now().to_msg()
        b.percentage = self.battery / 100.0
        b.present = True
        self.battery_pub.publish(b)
        self.status_pub.publish(String(data=json.dumps(
            {'state': self.state, 'battery': round(self.battery, 1)})))
 
    # ---------- transitions ----------
    def _start_delivery(self, order):
        order['attempts'] += 1
        order['status'] = 'IN_PROGRESS'
        if self._send_goal(order['destination'], 'delivery'):
            self.current = order
            self.state = 'DELIVERING'
            self.at_dock = False
        else:
            order['attempts'] -= 1
            order['status'] = 'PENDING'
            self.queue.appendleft(order)
            self._retry_until = self._now() + 3.0
 
    def _start_dock(self, reason):
        self.reason = reason
        if self.current:                      # la livraison en cours reprendra apres la charge
            self.current['status'] = 'PENDING'
            self.queue.appendleft(self.current)
            self.current = None
        self.state = 'IDLE'
        if self.at_dock:
            self.state = 'CHARGING'
            return
        # Ici : remplacer par l'auto-docking de ton coequipier si besoin.
        if self._send_goal('dock', 'dock'):
            self.state = 'RETURNING'
        else:
            self._retry_until = self._now() + 3.0
 
    def _send_goal(self, name, kind):
        if not self.nav.server_is_ready():
            self.get_logger().warn('Nav2 (navigate_to_pose) pas pret')
            return False
        loc = self.locations[name]
        yaw = float(loc.get('yaw', 0.0))
        goal = NavigateToPose.Goal()
        goal.pose = PoseStamped()
        goal.pose.header.frame_id = 'map'
        goal.pose.header.stamp = self.get_clock().now().to_msg()
        goal.pose.pose.position.x = float(loc['x'])
        goal.pose.pose.position.y = float(loc['y'])
        goal.pose.pose.orientation.z = math.sin(yaw / 2.0)
        goal.pose.pose.orientation.w = math.cos(yaw / 2.0)
        self._seq += 1
        seq = self._seq
        self._handle = None
        fut = self.nav.send_goal_async(goal)
        fut.add_done_callback(lambda f, s=seq, k=kind: self._on_accept(f, s, k))
        self.get_logger().info(f'Goal {kind} -> {name} ({loc["x"]}, {loc["y"]})')
        return True
 
    def _on_accept(self, fut, seq, kind):
        handle = fut.result()
        with self.lock:
            if seq != self._seq:              # goal annule ou remplace entre-temps
                if handle.accepted:
                    handle.cancel_goal_async()
                return
            if handle.accepted:
                self._handle = handle
        if not handle.accepted:
            self.get_logger().error('Goal refuse par Nav2')
            self._finish(seq, kind, False)
            return
        handle.get_result_async().add_done_callback(
            lambda rf, s=seq, k=kind: self._finish(
                s, k, rf.result().status == GoalStatus.STATUS_SUCCEEDED,
                rf.result().status))
    def _finish(self, seq, kind, ok, status=None):
        with self.lock:
            if seq != self._seq:
                return
            if not ok:
                self.get_logger().warn(f'Goal {kind} echoue (status={status})')
            self._handle = None
            now = self._now()
            if kind == 'delivery':
                o, self.current = self.current, None
                if o:
                    if ok:
                        o['status'] = 'DELIVERED'
                    elif o['attempts'] < self.max_attempts:
                        o['status'] = 'PENDING'
                        self.queue.appendleft(o)
                    else:
                        o['status'] = 'FAILED'
                self.state = 'IDLE'
                self._idle_since = now
                if not ok:
                    self._retry_until = now + 3.0
            else:                              # dock
                if ok:
                    self.at_dock = True
                    self.state = 'CHARGING'
                else:
                    self.state = 'IDLE'
                    self._retry_until = now + 5.0
 
