from fastapi import APIRouter, BackgroundTasks
from ..services.scheduler import trigger_now

router = APIRouter(prefix="/api/nudge", tags=["Nudge"])


@router.post("/trigger")
def manual_trigger(background_tasks: BackgroundTasks):
    """Manually trigger the nudge job from the admin dashboard."""
    background_tasks.add_task(trigger_now)
    return {"status": "ok", "message": "Nudge job queued in background"}
