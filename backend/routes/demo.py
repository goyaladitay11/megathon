from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(tags=["Demo"])

class EchoRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)

@router.post("/echo")
def echo(data: EchoRequest) -> dict[str, str]:
    return {"message": data.message, "note": "Replace with hackathon-specific logic"}
