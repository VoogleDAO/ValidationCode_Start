from typing import Dict, Optional, Any

from pydantic import BaseModel


class ProofResponse(BaseModel):
    dlp_id: int
    valid: bool = False
    score: float = 0.0
    uniqueness: float = 0.0
    quality: float = 0.0
    ownership: float = 1.0
    authenticity: float = 1.0
    attributes: Dict[str, Any] = {}
