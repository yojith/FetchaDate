from openai import OpenAI
from flask import session
from typing import List, Optional
from models import Pet
from database import PetDatabase


def get_user_email() -> str:
    """
    Retrieves the user's email from the session
    """
    return session["user"]["userinfo"]["email"]


def get_user_pet(email: str) -> Optional[dict]:
    """
    Fetch the user's pet details from the database using their email.
    """
    user_data = PetDatabase.get_user_from_email(email)
    if user_data:
        return {
            "pet_name": user_data.get("pet_name"),
            "species_name": user_data.get("species_name"),
            "location": user_data.get("location"),
        }
    return None


def match_pets(client: OpenAI, user_pet: dict, pets: List[Pet]) -> List[Pet]:
    """
    Match pets based on their similarity to the user's pet.
    """
    system_prompt = f"""
    You are a pet matching assistant. The user's pet is:
    Name: {user_pet['pet_name']}
    Species: {user_pet['species_name']}
    Location: {user_pet['location']}
    
    Given this user's pet details and a list of other pets, 
    rate each pet's similarity to the user's pet on a scale of 0-100. 
    Higher scores indicate more similarity. Ensure no two pets receive the same score.

    Consider the following criteria:
    - Exact species matches should rank higher.
    - Pets from the same location should rank higher.
    - Use descriptions, species, and unique details to break ties.
    Return only the numerical score for each pet.
    """

    def get_similarity_score(pet: Pet) -> float:
        """Get the similarity score for a pet."""
        pet_info = f"""
        Name: {pet.name}
        Species: {pet.species}
        Location: {pet.location}
        Description: {pet.description}
        """
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": pet_info},
                ],
                temperature=0.3,
                max_tokens=100,
            )
            return float(response.choices[0].message.content.strip())
        except (ValueError, AttributeError):
            return 0.0

    scored_pets = [(get_similarity_score(pet), pet) for pet in pets]
    scored_pets.sort(reverse=True, key=lambda x: x[0])
    return [pet for _, pet in scored_pets]
