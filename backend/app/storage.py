import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from . import config
from .models import Customer, CustomerCreate, CustomerUpdate, DecisionMakerRecord, DecisionMaker


def _ensure_data_dir() -> None:
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    config.DECISION_MAKERS_DIR.mkdir(parents=True, exist_ok=True)


def load_customers() -> List[Customer]:
    _ensure_data_dir()
    if not config.CUSTOMERS_FILE.exists():
        return []
    raw = json.loads(config.CUSTOMERS_FILE.read_text(encoding="utf-8"))
    return [Customer(**row) for row in raw]


def save_customers(customers: List[Customer]) -> None:
    _ensure_data_dir()
    config.CUSTOMERS_FILE.write_text(
        json.dumps([c.model_dump() for c in customers], indent=2),
        encoding="utf-8",
    )


def get_customer(customer_id: str) -> Optional[Customer]:
    for c in load_customers():
        if c.id == customer_id:
            return c
    return None


def create_customer(payload: CustomerCreate) -> Customer:
    customers = load_customers()
    customer = Customer(id=uuid.uuid4().hex[:10], **payload.model_dump())
    customers.append(customer)
    save_customers(customers)
    return customer


def update_customer(customer_id: str, payload: CustomerUpdate) -> Optional[Customer]:
    customers = load_customers()
    updated = None
    for i, c in enumerate(customers):
        if c.id == customer_id:
            data = c.model_dump()
            data.update({k: v for k, v in payload.model_dump().items() if v is not None})
            updated = Customer(**data)
            customers[i] = updated
            break
    if updated is not None:
        save_customers(customers)
    return updated


def delete_customer(customer_id: str) -> bool:
    customers = load_customers()
    remaining = [c for c in customers if c.id != customer_id]
    if len(remaining) == len(customers):
        return False
    save_customers(remaining)
    return True


def _dm_file(domain: str):
    safe = domain.replace("/", "_")
    return config.DECISION_MAKERS_DIR / f"{safe}.json"


def load_decision_makers(domain: str) -> Optional[DecisionMakerRecord]:
    _ensure_data_dir()
    path = _dm_file(domain)
    if not path.exists():
        return None
    return DecisionMakerRecord(**json.loads(path.read_text(encoding="utf-8")))


def save_decision_makers(domain: str, people: List[DecisionMaker]) -> DecisionMakerRecord:
    _ensure_data_dir()
    record = DecisionMakerRecord(
        domain=domain,
        imported_at=datetime.now(timezone.utc).isoformat(),
        people=people,
    )
    _dm_file(domain).write_text(record.model_dump_json(indent=2), encoding="utf-8")
    return record
