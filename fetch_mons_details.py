import requests
import json
import concurrent.futures

def fetch_pokemon_data(pokemon_id):
    try:
        response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}")
        if response.status_code == 200:
            pokemon = response.json()
            normal_abilities = [ability['ability']['name'] for ability in pokemon['abilities'] if not ability['is_hidden']]
            hidden_abilities = [ability['ability']['name'] for ability in pokemon['abilities'] if ability['is_hidden']]

            pokemon_data = {
                "name": pokemon['name'],
                "types": [ptype['type']['name'] for ptype in pokemon['types']],
                "normal_abilities": normal_abilities,
                "hidden_abilities": hidden_abilities,
                "stats": {stat['stat']['name']: stat['base_stat'] for stat in pokemon['stats']}
            }
            return pokemon_data
        else:
            print(f"Error fetching data for Pokémon ID {pokemon_id}: HTTP Status {response.status_code}")
            return None
    except Exception as e:
        print(f"Exception fetching data for Pokémon ID {pokemon_id}: {e}")
        return None


def main():
    total_pokemon = 1025  # Adjust this number based on the total count of Pokémon
    pokemon_data_dict = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(fetch_pokemon_data, i): i for i in range(1, total_pokemon + 1)}
        for future in concurrent.futures.as_completed(futures):
            pokemon_id = futures[future]
            pokemon_data = future.result()
            if pokemon_data:
                pokemon_data_dict[pokemon_id] = pokemon_data

    # Sort the data by National Pokédex number (which is the key in the dictionary)
    sorted_pokemon_list = [pokemon_data_dict[id] for id in sorted(pokemon_data_dict)]

    # Save the data to a JSON file
    with open('pokemon_data_sorted.json', 'w') as file:
        json.dump(sorted_pokemon_list, file)

    print("Data fetching complete and saved to pokemon_data_sorted.json")

if __name__ == "__main__":
    main()

