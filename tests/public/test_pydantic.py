from pydantic import BaseModel
from pytest_verify import verify_snapshot

class Product(BaseModel):
    id: int
    name: str
    price: float
    in_stock: bool

@verify_snapshot(ignore_fields=["id"], abs_tol=1e-5, rel_tol=1e-5)
def test_pydantic_snapshot():
    """Tests Pydantic model snapshot with float tolerance."""
    return Product(id=999, name="Laptop", price=999.9999, in_stock=True)
