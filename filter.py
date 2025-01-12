from typing import List, Optional
from models import Pet
from database import PetDatabase


class PetFilter:
    def __init__(self, pets: List[Pet]):
        self.pets = pets
        self.filters = {"species": None, "location": None}

    def set_filter(self, filter_type: str, value: Optional[str]):
        """
        Set a filter for a specific attribute (species or location)
        """
        if filter_type in self.filters:
            self.filters[filter_type] = value.lower() if value else None

    def filter(self) -> List[Pet]:
        """
        Apply active filters to the pet list
        """
        return [
            pet for pet in self.pets
            if all(
                getattr(pet, key).lower() == value
                for key, value in self.filters.items()
                if value
            )
        ]


def fetch_pets_from_db() -> List[Pet]:
    """
    Fetch all pets from the database and convert them to Pet objects
    """
    pets_data = PetDatabase.get_pets_from_query({})
    return [
        Pet(
            name=pet_data.get("pet_name"),
            species=pet_data.get("species_name"),
            description=pet_data.get("description", ""),
            location=pet_data.get("location"),
        )
        for pet_data in pets_data
    ]
