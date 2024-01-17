import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import json

class PokemonPicker:
    def __init__(self, root):
        # Initialize the main window and bind the mousewheel event
        self.root = root
        self.root.title("Regional Pokédex Maker")
        root.bind("<MouseWheel>", self.on_mousewheel)

        # Load data from JSON files
        self.pokemon_data = self.load_json_data("data/pokemon_data_sorted.json")
        self.ability_flavor_texts = self.load_json_data("data/abilities_flavor_text.json")
        self.evolution_chains = self.load_json_data("data/evolution_chains.json")

        # Set up initial state
        self.show_full_list = True
        self.selected_pokemons = []
        self.selected_pokemon = tk.StringVar()
        self.show_final_evolutions_only = False
        self.final_evolution_filter_query = ""
        self.final_evolutions = self.load_final_evolutions()
        # Create and style the widgets
        self.create_widgets()
        self.style_widgets()

    def load_json_data(self, filename):
        try:
            with open(filename, "r") as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"File not found: {filename}")
            return []
        except Exception as e:
            print(f"Error reading file {filename}: {e}")
            return []

    def generate_json(self):
        highlighted_pokemons_dict = {"highlighted_pokemons": self.selected_pokemons}
        json_data = json.dumps(highlighted_pokemons_dict, indent=2)

        try:
            with open("highlighted_pokemons.json", "w") as json_file:
                json_file.write(json_data)
        except Exception as e:
            print(f"Error saving JSON file: {e}")

    def generate_plain_list(self):
        plain_list = []
        for pokemon_name in self.selected_pokemons:
            # Find the Pokémon data in the loaded JSON data
            pokemon_data = next((pokemon for pokemon in self.pokemon_data if pokemon['name'] == pokemon_name), None)
            if pokemon_data:
                pokemon_types = ", ".join(pokemon_data['types'])
                plain_list.append(f"{pokemon_name} - Types: {pokemon_types}")
            else:
                plain_list.append(f"{pokemon_name} - Types: Unknown")

        try:
            with open("selected_pokemons.txt", "w") as txt_file:
                txt_file.write("\n".join(plain_list))
        except Exception as e:
            print(f"Error saving plain list file: {e}")


    def on_mousewheel(self, event):
        self.canvas.yview_scroll(-1 * (event.delta // 120), "units")
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))


    def pick_pokemon(self, selected_pokemon_name, label):
        already_selected = selected_pokemon_name in self.selected_pokemons
        if already_selected:
            self.selected_pokemons.remove(selected_pokemon_name)
        else:
            self.selected_pokemons.append(selected_pokemon_name)

        if self.show_final_evolutions_only:
            for base_form, evolution_info in self.evolution_chains.items():
                for evolution_detail in evolution_info.values():
                    if selected_pokemon_name in evolution_detail['full_chain']:
                        # Select or deselect all Pokémon in the evolution chain
                        for pokemon_name in evolution_detail['full_chain']:
                            if already_selected and pokemon_name in self.selected_pokemons:
                                self.selected_pokemons.remove(pokemon_name)
                            elif not already_selected and pokemon_name not in self.selected_pokemons:
                                self.selected_pokemons.append(pokemon_name)

        # Update UI for each Pokémon label
        for label in self.pokemon_labels:
            if label["text"].lower() in self.selected_pokemons:
                label.config(bd=3, relief="solid")
            else:
                label.config(bd=3, relief="flat")

        # Fetch details for the selected Pokémon and display them
        details, stats = self.fetch_pokemon_details(selected_pokemon_name)
        print(f"Details fetched for {selected_pokemon_name}: {details}")  # Debug print
        self.display_pokemon_details(details, stats)

        # Update the selected count
        self.update_selected_count()



    def process_evolution_chains(self, evolution_chains):
        final_evolutions = {}
        for chain in evolution_chains.values():
            for base_form, details in chain.items():
                # Add final forms for each Pokémon in the full chain
                for pokemon in details["full_chain"]:
                    final_evolutions[pokemon] = details["final_forms"]
        return final_evolutions




    def extract_final_forms(self, chain):
        if not chain:
            return []
        if isinstance(chain[0], list):
            final_forms = []
            for subchain in chain:
                final_forms.extend(self.extract_final_forms(subchain))
            return final_forms
        return [chain[0]]  # The first element is always the current evolution


    def update_selected_count(self):
        count = len(self.selected_pokemons)
        self.selected_count_label.config(text=f"Selected: {count}")

    def update_pokemon_icon(self, label):
        selected_pokemon_name = self.selected_pokemon.get().lower()
        index = next(
            (
                i
                for i, pokemon in enumerate(self.pokemon_data)
                if pokemon["name"].lower() == selected_pokemon_name
            ),
            None,
        )

        if index is not None:
            image_path = f"data/images/pokemons/{index + 1}.png"

            try:
                img = Image.open(image_path)
                img = img.resize((96, 96), resample=Image.LANCZOS)
                img = ImageTk.PhotoImage(img)

                self.pokemon_images.append(img)

            except FileNotFoundError:
                img = self.placeholder_img

            label.config(image=img)
            label.image = img

    def style_widgets(self):
        # Use a theme for ttk widgets that is available on your system
        style = ttk.Style()
        style.theme_use(
            "clam"
        )  # Example theme, 'clam', 'alt', 'default', 'classic' can also be used

        # Configure ttk Button style for uniformity
        style.configure("TButton", padding=6, relief="flat", background="#ccc")

        # Configure the ttk Entry style
        style.configure("TEntry", padding=6)

    def create_widgets(self):
        # Top frame for search and action buttons
        top_frame = tk.Frame(self.root)
        top_frame.pack(side=tk.TOP, fill=tk.X)

        # Search bar within the top frame
        self.search_entry = ttk.Entry(top_frame, width=50)
        self.search_entry.insert(0, "Search by name")
        self.search_entry.bind("<FocusIn>", self.on_search_focus)
        self.search_entry.bind("<KeyRelease>", self.filter_pokemon_list_view)
        self.search_entry.pack(side=tk.LEFT, padx=10, pady=5)

        # Action buttons within the top frame
        self.generate_button = ttk.Button(
            top_frame, text="Generate JSON", command=self.generate_json
        )
        self.generate_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.generate_plain_list_button = ttk.Button(
            top_frame, text="Generate Plain List", command=self.generate_plain_list
        )
        self.generate_plain_list_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.deselect_button = ttk.Button(
            top_frame, text="Deselect All", command=self.deselect_all
        )
        self.deselect_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.toggle_view_button = ttk.Button(
            top_frame, text="Show Picked Only", command=self.toggle_view
        )
        self.toggle_view_button.pack(side=tk.LEFT, padx=5, pady=5)

        # Bottom frame for the Pokémon selection and details display
        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        # Canvas and scrollbar within the bottom frame
        self.canvas = tk.Canvas(
            bottom_frame,
            width=120 * 10 + 20,
            height=100 * ((len(self.pokemon_data) - 1) // 10 + 1) + 20,
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(bottom_frame, command=self.canvas.yview)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        # Frame within the canvas for Pokémon images
        self.frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.frame, anchor="nw")

        # Details frame within the bottom frame
        self.details_frame = tk.Frame(bottom_frame, width=200)
        self.details_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10)
        self.details_frame.pack_propagate(False)

        # Details title and text widget within the details frame
        self.details_title = tk.Label(
            self.details_frame, text="Pokémon Details", font=("Arial", 16)
        )
        self.details_title.pack(pady=(5, 10))

        self.details_text = tk.Text(
            self.details_frame, wrap=tk.WORD, font=("Arial", 12), state=tk.DISABLED
        )
        self.details_text.pack(fill=tk.BOTH, expand=True)

        # Button to toggle final evolution view
        self.final_evo_button = ttk.Button(
            top_frame,
            text="Show Final Evolutions",
            command=self.toggle_final_evolutions,
        )
        self.final_evo_button.pack(side=tk.LEFT, padx=5, pady=5)

        # Pokémon image placeholders and labels
        self.pokemon_images = []
        self.pokemon_labels = []
        self.placeholder_img = ImageTk.PhotoImage(
            Image.new("RGBA", (96, 96), (255, 255, 255, 0))
        )

        for i, pokemon in enumerate(self.pokemon_data):
            image_path = f"data/images/pokemons/{i + 1}.png"
            try:
                img = Image.open(image_path)
                img = img.resize((96, 96), Image.LANCZOS)
                img = ImageTk.PhotoImage(img)
                self.pokemon_images.append(img)
            except FileNotFoundError:
                img = self.placeholder_img

            label = tk.Label(
                self.frame,
                image=img,
                text=pokemon["name"].capitalize(),
                compound="top",
                bd=0,
            )
            label.image = img  # Keep a reference to avoid garbage collection
            label.bind(
                "<Button-1>",
                lambda event, name=pokemon["name"], label=label: self.pick_pokemon(
                    name, label
                ),
            label.bind("<Enter>", lambda event, name=pokemon["name"]: self.display_pokemon_info_on_hover(name))
            )
            self.pokemon_labels.append(label)
            label.grid(row=i // 10, column=i % 10, padx=5, pady=5)

        # Counter label for selected Pokémons
        self.selected_count_label = ttk.Label(top_frame, text="Selected: 0")
        self.selected_count_label.pack(side=tk.RIGHT, padx=10, pady=5)

        # Update the scrollregion to encompass the inner frame
        self.canvas.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def on_search_focus(self, event):
        if self.search_entry.get() == "Search by name":
            self.search_entry.delete(0, tk.END)

    def deselect_all(self):
        self.selected_pokemons = []

        for label, original_image in zip(self.pokemon_labels, self.pokemon_images):
            if label["text"].lower() not in self.selected_pokemons:
                label.config(image=original_image, bd=3, relief="flat")
            else:
                self.update_pokemon_icon(label)
            # Update the counter
        self.update_selected_count()

    def update_icons(self):
        for label in self.pokemon_labels:
            self.update_pokemon_icon(label)

    def load_final_evolutions(self):
        try:
            with open("data/evolution_chains.json", "r") as file:
                all_chains = json.load(file)
                final_evolutions = {}
                for chain in all_chains.values():
                    for base_form, data in chain.items():
                        final_evolutions[base_form] = data['final_forms']
                return final_evolutions
        except FileNotFoundError:
            print("Evolution chains file not found.")
            return {}
        except Exception as e:
            print(f"Error reading evolution chains file: {e}")
            return {}

    def filter_pokemon_list_view(self, event=None):
        search_query = self.search_entry.get().lower()

        # Reset the view
        for label in self.pokemon_labels:
            label.grid_forget()

        if self.show_final_evolutions_only:
            # Filter for final evolutions and apply search query if it exists
            final_evo_names = {name for names in self.final_evolutions.values() for name in names}
            if search_query:
                filtered_labels = [label for label in self.pokemon_labels if label["text"].lower() in final_evo_names and search_query in label["text"].lower()]
            else:
                filtered_labels = [label for label in self.pokemon_labels if label["text"].lower() in final_evo_names]
        elif not self.show_full_list:
            # Filter within selected Pokémon and apply search query if it exists
            if search_query:
                filtered_labels = [label for label in self.pokemon_labels if label["text"].lower() in self.selected_pokemons and search_query in label["text"].lower()]
            else:
                filtered_labels = [label for label in self.pokemon_labels if label["text"].lower() in self.selected_pokemons]
        else:
            # Normal search in full list
            filtered_labels = [label for label in self.pokemon_labels if search_query in label["text"].lower()]

        # Display the filtered labels
        for i, label in enumerate(filtered_labels):
            row, col = divmod(i, 10)
            label.grid(row=row, column=col, padx=5, pady=5)

        # Update scroll region
        self.canvas.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))


    def extract_final_evolutions(self, chain):
        # If the chain is empty or has no further evolutions, it's a final form
        if not chain or 'evolves_to' not in chain[-1]:
            return [chain[-1]]

        # If there's a split, recursively extract final evolutions from each branch
        final_forms = []
        for next_step in chain[-1]['evolves_to']:
            final_forms.extend(self.extract_final_evolutions(chain + [next_step]))

        return final_forms



    def toggle_view(self):
        self.show_full_list = not self.show_full_list

        if self.show_full_list:
            if self.show_final_evolutions_only:
                # If Final Evolutions Only mode is active, show that view
                self.filter_pokemon_list_view()
            else:
                # Otherwise, show the full list
                self.show_full_list_view()
            self.toggle_view_button.config(text="Show Picked Only")
        else:
            # Show only the picked Pokémon
            self.show_picked_pokemon_view()
            self.toggle_view_button.config(text="Show All")

        # Reset vertical scroll position to the top
        self.canvas.yview_moveto(0)


    def show_full_list_view(self):
        for i, label in enumerate(self.pokemon_labels):
            col = i % 10
            row = i // 10
            label.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

    def toggle_final_evolutions(self):
        self.show_final_evolutions_only = not self.show_final_evolutions_only
        button_text = "Show All" if self.show_final_evolutions_only else "Show Final Evolutions"
        self.final_evo_button.config(text=button_text)

        # Call the filter function with an empty query to initialize the view
        self.search_entry.delete(0, tk.END)  # Clear any existing search text
        self.filter_pokemon_list_view()



    def show_picked_pokemon_view(self):
        # Determine if we should filter by final evolutions
        filter_final_evolutions = self.show_final_evolutions_only

        # Get the list of final evolution names if needed
        final_evolution_names = {name for names in self.final_evolutions.values() for name in names} if filter_final_evolutions else set()

        selected_labels = []
        for label in self.pokemon_labels:
            pokemon_name = label["text"].lower()
            if pokemon_name in self.selected_pokemons:
                # If we are filtering by final evolutions, check if the Pokémon is a final evolution
                if filter_final_evolutions and pokemon_name in final_evolution_names:
                    selected_labels.append(label)
                elif not filter_final_evolutions:
                    selected_labels.append(label)

        for label in self.pokemon_labels:
            if label in selected_labels:
                row, col = divmod(self.pokemon_labels.index(label), 10)
                label.grid(row=row, column=col, padx=5, pady=5)
            else:
                label.grid_forget()


    def fetch_pokemon_details(self, pokemon_name):
        # Search for the Pokémon in the cached data
        for pokemon in self.pokemon_data:
            if pokemon["name"].lower() == pokemon_name.lower():
                types = ", ".join(pokemon.get("types", []))

                # Formatting and fetching abilities with flavor texts
                abilities_info = ""
                for ability in pokemon.get("normal_abilities", []) + pokemon.get(
                    "hidden_abilities", []
                ):
                    formatted_ability = self.format_ability_name(ability)
                    flavor_text_en = self.ability_flavor_texts.get(ability, {}).get(
                        "en", "No description available."
                    )
                    abilities_info += f"{formatted_ability}: {flavor_text_en}\n"

                # Preparing stats
                stats = pokemon.get("stats", {})

                # Format the details for display
                details = f"{pokemon_name.capitalize()}\nTypes: {types}\n{abilities_info}"
                return details, stats

        return "Details not found.", {}

    def get_stat_color(self, stat):
        # Return a color based on the stat name
        colors = {
            "hp": "green",
            "attack": "red",
            "defense": "orange",
            "special-attack": "pink",
            "special-defense": "blue",
            "speed": "cyan",
        }
        return colors.get(stat.lower(), "grey")

    def load_ability_flavor_texts(self):
        try:
            with open("data/abilities_flavor_text.json", "r") as file:
                return json.load(file)
        except FileNotFoundError:
            print("Ability flavor text file not found.")
            return {}
        except Exception as e:
            print(f"Error reading ability flavor text file: {e}")
            return {}

    def format_ability_name(self, ability_name):
        return ability_name.replace("-", " ").capitalize()

    def display_pokemon_details(self, details, stats):
        # Clear the frame of previous details and bars
        for widget in self.details_frame.winfo_children():
            widget.destroy()

        # Set up font styles
        title_font = ("Arial", 14, "bold")
        content_font = ("Arial", 10)

        # Display the text details (name, types, etc.)
        details_text = tk.Text(self.details_frame, wrap=tk.WORD, bg=self.root.cget('bg'))
        details_text.pack(side=tk.TOP, fill=tk.BOTH, padx=5, pady=5)

        # Insert Pokémon name
        details_text.tag_configure("name", font=title_font)
        details_text.insert(tk.END, details.split('\n')[0] + '\n', "name")

        # Display the type icons
        types_frame = tk.Frame(self.details_frame)
        types_frame.pack(pady=5)

        pokemon_types = details.split('\n')[1].replace("Types: ", "").split(", ")
        for type_name in pokemon_types:
            type_img_path = f"data/images/types/{type_name.capitalize()}.png"
            try:
                type_img = Image.open(type_img_path)
                type_img = type_img.resize((80, 20), Image.LANCZOS)  # Adjust the size as needed
                type_photo = ImageTk.PhotoImage(type_img)
                type_label = tk.Label(types_frame, image=type_photo)
                type_label.image = type_photo  # Keep a reference
                type_label.pack(side=tk.LEFT, padx=2)
            except FileNotFoundError:
                print(f"Type icon not found: {type_img_path}")

        # Re-enable text widget, insert abilities info, and disable it again
        details_text.config(state=tk.NORMAL)
        abilities_info = details.split('\n')[2:]
        for info in abilities_info:
            details_text.insert(tk.END, info + '\n', "content")
        details_text.config(state=tk.DISABLED)  # Make the text widget read-only

        # Display the stat bars
        self.display_stat_bars(stats)





    def display_pokemon_info_on_hover(self, pokemon_name):
        details, stats = self.fetch_pokemon_details(pokemon_name)
        #print(f"Details fetched for {pokemon_name}: {details}")  # Debug print for verification
        self.display_pokemon_details(details, stats)

    def display_stat_bars(self, stats):
        # Clear out any existing widgets in the details_frame
        for widget in self.details_frame.winfo_children():
            if isinstance(widget, tk.Canvas) or isinstance(widget, tk.Label):
                widget.destroy()

        # Define abbreviations for stat names
        stat_abbreviations = {
            "hp": "HP",
            "attack": "ATK",
            "defense": "DEF",
            "special-attack": "SpATK",
            "special-defense": "SpDEF",
            "speed": "SPE",
        }

        # Calculate the total of all stats (BST)
        bst = sum(stats.values())

        # Define a maximum value for stats to normalize the bar length
        max_stat_value = 150

        for stat, value in stats.items():
            # Create a frame for each stat
            stat_frame = tk.Frame(self.details_frame)
            stat_frame.pack(fill=tk.X, padx=5, pady=2)

            # Use abbreviation for the stat name
            abbrev = stat_abbreviations.get(stat, stat).capitalize()

            # Create a label with the stat abbreviation
            tk.Label(stat_frame, text=abbrev, width=6, anchor="w").pack(side=tk.LEFT)

            # Create a label for the stat value
            value_label = tk.Label(stat_frame, text=f"{value}", width=4, anchor="e")
            value_label.pack(side=tk.RIGHT)

            # Create a canvas for the bar
            canvas = tk.Canvas(stat_frame, height=10, bg="white")
            canvas.pack(side=tk.LEFT, fill=tk.X, expand=True)
            canvas.update_idletasks()  # Refresh the UI to get updated dimensions

            # Draw the bar on the canvas
            bar_length = (value / max_stat_value) * canvas.winfo_width()
            canvas.create_rectangle(
                0, 0, bar_length, 10, fill=self.get_stat_color(stat), outline=""
            )

        # Display the Base Stat Total
        bst_frame = tk.Frame(self.details_frame)
        bst_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Label(bst_frame, text="Total", width=6, anchor="w").pack(side=tk.LEFT)
        tk.Label(bst_frame, text=f"{bst}", anchor="e").pack(side=tk.RIGHT)


if __name__ == "__main__":
    root = tk.Tk()
    app = PokemonPicker(root)
    root.mainloop()
