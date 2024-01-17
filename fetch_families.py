import requests
import json
import concurrent.futures

def fetch_evolution_chain(chain_id):
    try:
        response = requests.get(f"https://pokeapi.co/api/v2/evolution-chain/{chain_id}/")
        response.raise_for_status()
        data = response.json()

        def extract_chain(chain):
            names = [chain['species']['name']]
            for next_chain in chain['evolves_to']:
                names.extend(extract_chain(next_chain))
            return names

        full_chain = extract_chain(data['chain'])
        return full_chain

    except Exception as e:
        print(f"Error fetching evolution chain for ID {chain_id}: {e}")
        return None

def fetch_all_evolution_chains():
    # Fetching a large number of evolution chains
    chain_ids = range(1, 600)
    all_chains = {}

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(fetch_evolution_chain, chain_id) for chain_id in chain_ids]

        for future in concurrent.futures.as_completed(futures):
            chain_id = futures.index(future) + 1
            evolution_chain = future.result()
            if evolution_chain:
                all_chains[chain_id] = evolution_chain

    with open('evolution_chains.json', 'w') as f:
        json.dump(all_chains, f, indent=4)

    print("Fetched all evolution chains.")

if __name__ == "__main__":
    fetch_all_evolution_chains()
