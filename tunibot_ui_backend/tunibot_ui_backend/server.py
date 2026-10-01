"""FastAPI (REST + WebSocket) + sert le dashboard. Compatible avec le index.html existant."""
import asyncio
import os
import threading
 
import rclpy
import uvicorn
from ament_index_python.packages import get_package_share_directory
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from rclpy.executors import SingleThreadedExecutor
 
from .delivery_manager import DeliveryManager
 
SHARE = get_package_share_directory('tunibot_ui_backend')
 
app = FastAPI(title='Tunibot UI Backend')
app.add_middleware(CORSMiddleware, allow_origins=['*'],
                   allow_methods=['*'], allow_headers=['*'])
node = None
 
 
class OrderIn(BaseModel):
    item: str
    destination: str
 
 
class BatteryIn(BaseModel):
    level: float
 
 
@app.get('/')
def dashboard():
    return FileResponse(os.path.join(SHARE, 'dashboard', 'index.html'))
 
 
@app.get('/locations')
def locations():
    # tout sauf le dock : la cuisine et les tables peuvent etre commandees
    return {'locations': [k for k in node.locations if k != 'dock']}
 
 
@app.post('/orders')
def create_order(body: OrderIn):
    try:
        return node.add_order(body.item, body.destination)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
 
 
@app.get('/orders')
def list_orders():
    return node.recent_orders(50)
 
 
@app.get('/robot/status')
def status():
    return node.snapshot()
 
 
@app.post('/robot/dock')
def dock():
    return {'result': node.request_dock()}
 
 
@app.post('/robot/cancel')
def cancel():
    return {'result': node.cancel()}
 
 
@app.post('/debug/battery')                  # pour la demo : forcer un niveau de batterie
def debug_battery(b: BatteryIn):
    node.set_battery(b.level)
    return {'battery': b.level}
 
 
@app.websocket('/ws/status')
async def ws_status(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            await ws.send_json({**node.snapshot(), 'orders': node.recent_orders(10)})
            await asyncio.sleep(1.0)
    except (WebSocketDisconnect, RuntimeError):
        pass
 
 
def main():
    global node
    rclpy.init()
    node = DeliveryManager()
    executor = SingleThreadedExecutor()
    executor.add_node(node)
    threading.Thread(target=executor.spin, daemon=True).start()
    try:
        uvicorn.run(app, host='0.0.0.0', port=8000, log_level='info')
    finally:
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()
 
 
if __name__ == '__main__':
    main()
 
