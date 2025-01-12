from dataclasses import dataclass
from typing import Optional

@dataclass
class Pet:
    name: str
    species: str
    description: str
    location: str
    email: str
    image: Optional[str] = None
