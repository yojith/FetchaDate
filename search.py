from openai import OpenAI
from typing import List
from models import Pet


def initialize_openai() -> OpenAI:
    """Initialize the OpenAI client."""
    with open("OpenAI_key.txt", "r") as file:
        openai_api_key = file.read().strip()
        return OpenAI(api_key=openai_api_key)


def search_pets(client: OpenAI, pets: List[Pet], search_query: str) -> List[Pet]:
    """
    Search for pets based on their relevance to the search query.
    """
    system_prompt = """
    You are a pet matching assistant. Given a search query and pet details, 
    rate each pet's relevance to the search query on a scale of 0-100. 
    Higher scores indicate better matches. Ensure no two pets receive the same score.
    
    Consider the following criteria:
    - Exact matches of the search word in descriptions should rank higher.
    - Pets from the same location should rank slightly higher.
    - Use species, descriptions, and unique details to break ties.
    Return only the numerical score for each pet.
    """

    def get_relevance_score(pet: Pet) -> float:
        """Get the relevance score for a pet."""
        pet_info = f"""
        Name: {pet.name}
        Species: {pet.species}
        Location: {pet.location}
        Description: {pet.description}
        Search Query: {search_query}
        Rate relevance and return only a score between 0-100.
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

    scored_pets = [(get_relevance_score(pet), pet) for pet in pets]
    scored_pets.sort(reverse=True, key=lambda x: x[0])
    return [pet for _, pet in scored_pets]

    scored_pets = [(get_relevance_score(pet), pet) for pet in pets]
    scored_pets.sort(reverse=True, key=lambda x: x[0])
    return [pet for _, pet in scored_pets]
