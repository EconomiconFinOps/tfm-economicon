from pydantic import BaseModel


class BillingSummary(BaseModel):
    monthly_spend: int
    savings_identified: int
    open_ingestions: int
    currency: str

