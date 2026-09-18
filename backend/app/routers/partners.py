from fastapi import APIRouter

from ..services import partner_fit

router = APIRouter(tags=["partners"])


@router.get("/partner-fit")
def partner_fit_board() -> dict:
    """Customers ranked by how ready they look for a partner product, with the reason
    behind each ranking and the rules that produced it."""
    return partner_fit.build_partner_fit()
