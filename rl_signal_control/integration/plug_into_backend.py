"""
Integration Plugin: Connects RL module into the existing AI Traffic Cop backend.

This file shows exactly how to wire everything together.
Add these lines to backend/app/main.py to activate RL control.
"""

# =====================================================================
# INTEGRATION INSTRUCTIONS
# =====================================================================
#
# Add the following to backend/app/main.py:
#
# 1. At the top (imports):
#
#     from rl_signal_control.integration.api_routes import rl_router
#     from rl_signal_control.integration.live_environment import LiveTrafficEnv, LiveEnvConfig
#
# 2. After app creation (routes):
#
#     app.include_router(rl_router, prefix="/api/rl", tags=["RL Signal Control"])
#
# 3. In the startup() event, after AI Gateway init:
#
#     # Initialize RL Signal Control
#     from rl_signal_control.integration import setup_rl_integration
#     setup_rl_integration(app, ai_gateway, broadcast)
#
# =====================================================================


def setup_rl_integration(app, ai_gateway=None, broadcast_fn=None):
    """
    Wire RL signal control into the existing backend.
    
    This function:
    1. Creates the LiveTrafficEnv
    2. Connects it to the existing YOLO detector and tracker
    3. Hooks into the video processing pipeline
    4. Sets up WebSocket broadcasting for RL events
    
    Args:
        app: FastAPI application instance
        ai_gateway: Existing AIGateway instance (has detector, tracker)
        broadcast_fn: Async broadcast function for WebSocket
    """
    from rl_signal_control.integration.live_environment import LiveTrafficEnv, LiveEnvConfig
    from rl_signal_control.integration.api_routes import get_live_env
    import logging
    
    logger = logging.getLogger("rl_integration")
    
    # Get or create the live environment
    live_env = get_live_env()
    
    # Connect to existing AI components
    if ai_gateway:
        try:
            # Connect YOLO detector
            detector = getattr(ai_gateway, 'detector', None)
            if detector:
                live_env.set_detector(detector)
                logger.info("✅ RL connected to YOLO detector")
            
            # Connect tracker
            tracker = getattr(ai_gateway, 'tracker', None)
            if tracker:
                live_env.set_tracker(tracker)
                logger.info("✅ RL connected to object tracker")
            
            # Connect speed estimator
            speed_est = getattr(ai_gateway, 'speed_estimator', None)
            if speed_est:
                live_env.set_speed_estimator(speed_est)
                logger.info("✅ RL connected to speed estimator")
                
        except Exception as e:
            logger.warning(f"⚠️ Partial RL integration: {e}")
    
    # Connect WebSocket broadcast
    if broadcast_fn:
        import asyncio
        loop = asyncio.get_event_loop()
        
        def sync_broadcast(event):
            """Bridge sync callback to async broadcast."""
            loop.call_soon_threadsafe(
                asyncio.ensure_future, broadcast_fn(event)
            )
        
        live_env.set_event_callback(sync_broadcast)
        logger.info("✅ RL connected to WebSocket broadcast")
    
    # Hook into video processor frame pipeline
    # The existing VideoProcessor calls process_frame() on each frame
    # We intercept to also feed frames to RL
    _hook_video_processor(app, live_env)
    
    logger.info("🚦 RL Signal Control integration complete")
    return live_env


def _hook_video_processor(app, live_env):
    """
    Hook into existing video processing pipeline.
    
    The existing system processes frames like:
        frame → detect → track → annotate → stream
    
    We add:
        frame → detect → track → annotate → stream
                                    ↓
                            RL process_frame()
                                    ↓
                            signal decision
    """
    import logging
    logger = logging.getLogger("rl_integration")
    
    # Store reference on app for the video processor to access
    app.state.rl_live_env = live_env
    
    logger.info("  RL frame hook registered on app.state.rl_live_env")
    logger.info("  VideoProcessor should call: app.state.rl_live_env.process_frame(frame)")
