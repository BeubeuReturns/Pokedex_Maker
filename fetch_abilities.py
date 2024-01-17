import requests
import json
import concurrent.futures

def fetch_all_abilities():
    url = "https://pokeapi.co/api/v2/ability?limit=10000"  # High limit to ensure fetching all abilities
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return [ability['name'] for ability in data['results']]
    return []

def fetch_ability_details(ability_name):
    response = requests.get(f"https://pokeapi.co/api/v2/ability/{ability_name}")
    if response.status_code == 200:
        data = response.json()
        flavor_texts = {}
        for flavor_text_entry in data["flavor_text_entries"]:
            language = flavor_text_entry["language"]["name"]
            flavor_text = flavor_text_entry["flavor_text"]
            flavor_texts[language] = flavor_text
        return flavor_texts
    return {}

def cache_abilities(abilities):
    ability_flavor_texts = {}
    for ability in abilities:
        flavor_texts = fetch_ability_details(ability)
        ability_flavor_texts[ability] = flavor_texts

    with open('abilities_flavor_text.json', 'w') as file:
        json.dump(ability_flavor_texts, file, indent=4)

def main():
    all_abilities = fetch_all_abilities()
    if all_abilities:
        cache_abilities(all_abilities)
    else:
        print("Failed to fetch abilities.")

if __name__ == "__main__":
    main()
