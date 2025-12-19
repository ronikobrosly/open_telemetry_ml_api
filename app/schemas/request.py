from pydantic import BaseModel, Field, field_validator
from typing import Optional

class SearchRequest(BaseModel):
    q: str = Field(..., min_length=1, max_length=500, description="Search query")
    user_id: str = Field(..., min_length=1, max_length=100, description="User identifier")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum results to return")

    @field_validator('q')
    @classmethod
    def validate_query(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Query cannot be empty or whitespace only")
        return v.strip()

class ChaosConfig(BaseModel):
    model_failure_rate: float = Field(default=0.05, ge=0.0, le=1.0)
    external_api_timeout_rate: float = Field(default=0.1, ge=0.0, le=1.0)
    slow_search_rate: float = Field(default=0.2, ge=0.0, le=1.0)
    external_api_failure_rate: float = Field(default=0.05, ge=0.0, le=1.0)
