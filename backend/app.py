from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import asyncio
import socketio
from datetime import timedelta
import time

from .core.database import initialize_db, save_session_snapshot
from .core.monitor import get_system_metrics
from .core.analyzer import get_health_status
from .routes.auth_routes import auth_router, get_current_user
from .config import ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, ALGORITHM

# --- 1. FastAPI Setup ---
app = FastAPI(title="Kernel Health Monitor API")

# --- 2. WebSocket Setup (using python-socketio) ---
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)

# --- 3. CORS Middleware (Essential for connecting Frontend) ---
origins = [
    "http://localhost:3000", # Default React development port
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 4. Include Authentication Router ---
app.include_router(auth_router, prefix="/auth")

# --- GLOBAL STATE/CONTEXT ---
# We use this to track which user is currently running the monitoring session
active_sessions = {} # {user_id: True/False} 
session_data_cache = {} # {user_id: [list of metrics snapshots]}

# --- 5. Background Task: The 2-Second Monitoring Loop ---

async def monitoring_loop():
    """Fetches, analyzes, and broadcasts metrics every 2 seconds."""
    while True:
        # --- REMOVED THE SESSION CHECK (if active_sessions...) ---
        # Now it will always run and send data!
        
        try:
            # --- FETCH & ANALYZE ---
            current_metrics = get_system_metrics()
            analysis_result = get_health_status(current_metrics)
            
            full_data = {
                "metrics": current_metrics,
                "analysis": analysis_result
            }

            # --- BROADCAST ---
            # Send data to all connected socket clients immediately
            await sio.emit('metrics_update', full_data)
            
            # Print to terminal so you can see it working
            # print(f"Sent metrics: CPU {current_metrics['cpu']['usage_percent']}%") 

        except Exception as e:
            print(f"Error in monitoring loop: {e}")

        await asyncio.sleep(2) # Wait exactly 2 seconds
# --- 6. Startup/Shutdown Events ---

@app.on_event("startup")
async def startup_event():
    """Runs when the server starts."""
    print("Initializing Database...")
    initialize_db()
    # Start the monitoring task in the background
    asyncio.create_task(monitoring_loop())
    print("Monitoring loop started.")

@app.on_event("shutdown")
def shutdown_event():
    print("Application shutting down.")


# --- 7. Protected Session Control Endpoints (FastAPI) ---

@app.post("/session/start")
async def start_session(current_user: dict = Depends(get_current_user)):
    """Starts the monitoring session for the current user."""
    user_id = current_user['user_id']
    active_sessions[user_id] = True
    print(f"Session started for User ID: {user_id}")
    return {"message": "Monitoring started", "user_id": user_id}

@app.post("/session/stop")
async def stop_session(current_user: dict = Depends(get_current_user)):
    """Stops the monitoring session for the current user and clears cache."""
    user_id = current_user['user_id']
    active_sessions[user_id] = False
    print(f"Session stopped for User ID: {user_id}")
    
    # Optional: Logic to trigger a final save or aggregation could go here.

    return {"message": "Monitoring stopped", "user_id": user_id}

# --- 8. WebSocket Connection (Socket.IO) ---

@sio.on('connect')
async def handle_connect(sid, environ):
    # This is for debugging purposes
    print(f"Socket connected: {sid}")

@sio.on('disconnect')
async def handle_disconnect(sid):
    # This is for debugging purposes
    print(f"Socket disconnected: {sid}")

# --- 9. History Retrieval (Protected) ---

@app.get("/history")
async def get_user_data(current_user: dict = Depends(get_current_user)):
    """Retrieves saved history snapshots for the current user."""
    from .core.database import get_user_history # Local import to avoid circular dependency
    
    user_id = current_user['user_id']
    history_data = get_user_history(user_id, limit=50) # Get last 50 snapshots
    
    if not history_data:
        raise HTTPException(status_code=404, detail="No history found for this user.")
        
    return JSONResponse(content=history_data)
# --- Remove the 'Depends(get_current_user)' part to make it public ---
@app.get("/system/specs")
async def get_specs(): 
    """Returns static hardware details."""
    from .core.monitor import get_static_info
    return get_static_info()
# --- 10. Run Command for Development ---
if __name__ == "__main__":
    # Note: We must run the socket_app wrapper, not the original app
    # The --reload option is great for development, but remove for production
    uvicorn.run(socket_app, host="0.0.0.0", port=8000, log_level="info")