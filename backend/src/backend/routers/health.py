from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from ..db.mongo import ensure_connection

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check endpoint that pings MongoDB"""
    try:
        db = await ensure_connection()
        await db.command('ping')
        return {"status": "healthy"}
    except Exception:
        return {"status": "degraded"}


@router.get("/health/websocket")
def websocket_health_check():
    """WebSocket service health check"""
    try:
        from ..services.ws_manager import manager
        connection_info = manager.get_connection_info()
        return JSONResponse({
            'status': 'healthy',
            'websocket_service': 'running',
            'active_connections': connection_info['total_connections'],
            'connections': connection_info['connections']
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"WebSocket service unhealthy: {str(e)}")


@router.get("/health/detailed")
async def detailed_health_check():
    """Comprehensive health check including all services"""
    try:
        from ..services.ws_manager import manager
        
        # Check WebSocket service
        ws_status = "healthy"
        ws_connections = 0
        try:
            connection_info = manager.get_connection_info()
            ws_connections = connection_info['total_connections']
        except Exception as e:
            ws_status = f"unhealthy: {str(e)}"
        
        # Check database connection (async check using ensure_connection)
        db_status = "healthy"
        try:
            db = await ensure_connection()
            await db.command('ping')
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"
        
        return JSONResponse({
            'status': 'healthy',
            'services': {
                'websocket': {
                    'status': ws_status,
                    'active_connections': ws_connections
                },
                'database': {
                    'status': db_status
                }
            }
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")