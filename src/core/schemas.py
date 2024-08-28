from pydantic import BaseModel, Field


class Pagination(BaseModel):
    offset: int = Field(default=0)
    limit: int = Field(default=100, gt=0, le=200)


class StarsTransactionPagination(BaseModel):
    offset: int = Field(default=0)
    limit: int = Field(default=100, gt=0, le=100)
