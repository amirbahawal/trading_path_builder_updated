"""
WebSocket Router
Handles WebSocket connections for real-time updates (e.g., plan unlock status)
"""

from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from typing import Dict, Set
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Store active WebSocket connections
# Key: plan_id, Value: Set of WebSocket connections
active_connections: Dict[str, Set[WebSocket]] = {}


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates
    Handles plan unlock status updates and other real-time events
    """
    await websocket.accept()
    logger.info("[WebSocket] New connection established")
    
    plan_id = None
    
    try:
        # Wait for initial subscription message
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                if message_type == "subscribe":
                    # Subscribe to plan updates
                    plan_id = message.get("plan_id")
                    if plan_id:
                        if plan_id not in active_connections:
                            active_connections[plan_id] = set()
                        active_connections[plan_id].add(websocket)
                        logger.info(f"[WebSocket] Subscribed to plan_id: {plan_id}")
                        
                        # Send confirmation
                        await websocket.send_text(json.dumps({
                            "type": "subscribed",
                            "plan_id": plan_id,
                            "message": "Subscribed to plan updates"
                        }))
                    else:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": "plan_id is required for subscription"
                        }))
                
                elif message_type == "unsubscribe":
                    # Unsubscribe from plan updates
                    plan_id = message.get("plan_id")
                    if plan_id and plan_id in active_connections:
                        active_connections[plan_id].discard(websocket)
                        if not active_connections[plan_id]:
                            del active_connections[plan_id]
                        logger.info(f"[WebSocket] Unsubscribed from plan_id: {plan_id}")
                
                elif message_type == "ping":
                    # Heartbeat/ping message
                    await websocket.send_text(json.dumps({
                        "type": "pong"
                    }))
                
                else:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": f"Unknown message type: {message_type}"
                    }))
            
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
            except Exception as e:
                logger.error(f"[WebSocket] Error processing message: {e}", exc_info=True)
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": str(e)
                }))
    
    except WebSocketDisconnect:
        logger.info(f"[WebSocket] Client disconnected")
    except Exception as e:
        logger.error(f"[WebSocket] Connection error: {e}", exc_info=True)
    finally:
        # Clean up connection
        if plan_id and plan_id in active_connections:
            active_connections[plan_id].discard(websocket)
            if not active_connections[plan_id]:
                del active_connections[plan_id]
        logger.info(f"[WebSocket] Connection cleaned up")


async def broadcast_plan_unlock(plan_id: str, user_id: str = None):
    """
    Broadcast plan unlock event to all connected clients subscribed to this plan
    """
    if plan_id not in active_connections:
        return
    
    message = {
        "type": "plan_unlocked",
        "plan_id": plan_id,
        "user_id": user_id,
        "tier": "pro",
        "message": "Plan unlocked successfully"
    }
    
    message_json = json.dumps(message)
    disconnected = set()
    
    for connection in active_connections[plan_id]:
        try:
            await connection.send_text(message_json)
        except Exception as e:
            logger.error(f"[WebSocket] Error sending message: {e}")
            disconnected.add(connection)
    
    # Remove disconnected connections
    for connection in disconnected:
        active_connections[plan_id].discard(connection)
    
    if not active_connections[plan_id]:
        del active_connections[plan_id]


async def broadcast_plan_update(plan_id: str, update_data: dict):
    """
    Broadcast plan update event to all connected clients subscribed to this plan
    """
    if plan_id not in active_connections:
        return
    
    message = {
        "type": "plan_updated",
        "plan_id": plan_id,
        **update_data
    }
    
    message_json = json.dumps(message)
    disconnected = set()
    
    for connection in active_connections[plan_id]:
        try:
            await connection.send_text(message_json)
        except Exception as e:
            logger.error(f"[WebSocket] Error sending message: {e}")
            disconnected.add(connection)
    
    # Remove disconnected connections
    for connection in disconnected:
        active_connections[plan_id].discard(connection)
    
    if not active_connections[plan_id]:
        del active_connections[plan_id]

