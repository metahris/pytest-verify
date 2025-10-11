from dataclasses import dataclass
from pytest_verify import verify_snapshot

@dataclass
class User:
    id: int
    name: str
    age: int
    country: str

@verify_snapshot(ignore_fields=["id"])
def test_dataclass_snapshot():
    """Ensures dataclass serialization and field ignoring works."""
    return User(id=123, name="Mohamed", age=27, country="Morocco")
