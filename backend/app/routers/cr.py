from fastapi import APIRouter

from ..services import cr_tracker

router = APIRouter(tags=["cyber-rescue"])


@router.get("/cr-tracker")
def cr_tracker_board(refresh: bool = False) -> dict:
    """Cyber Rescue's own account tracking: who hasn't been met, what's coming up,
    who is overdue. Read from a local spreadsheet that never enters the repository."""
    return cr_tracker.build(force=refresh)
