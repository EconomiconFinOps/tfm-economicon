from datetime import date

from pydantic import BaseModel


class ReferenceDateInfo(BaseModel):
    reference_date: date
    simulated: bool
