import tkinter as tk
from tkinter import ttk  # Import the themed tkinter
from PIL import Image, ImageTk
import requests
import json
import threading
from tkinter import messagebox  # For point 11

class PokemonPicker:
    def __init__(self, root):
        self.root = root
        self.root.title("Regional Pokédex Maker")
        root.bind("<MouseWheel>", self.on_mousewheel)

        self.pokemon_data = self.fetch_pokemon_data()
        self.show_full_list = True
        self.selected_pokemons = []
        self.selected_pokemon = tk.StringVar()

        self.create_widgets()
        self.style_widgets()

    def fetch_pokemon_data(self):
        api_url = "https://pokeapi.co/api/v2/pokemon?limit=1024"
        try:
            response = requests.get(api_url)
            response.raise_for_status()
            data = response.json()
            return data["results"]
        except requests.exceptions.RequestException as e:
            print(f"Error fetching Pokémon data: {e}")
            return []

    def fetch_pokemon_types(self, pokemon_name):
        api_url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}"
        try:
            response = requests.get(api_url)
            response.raise_for_status()
            data = response.json()
            types = [type_data["type"]["name"] for type_data in data["types"]]
            return types
        except requests.exceptions.RequestException as e:
            print(f"Error fetching types for {pokemon_name}: {e}")
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
            pokemon_types = self.fetch_pokemon_types(pokemon_name)
            plain_list.append(f"{pokemon_name} - Types: {', '.join(pokemon_types)}")

        try:
            with open("selected_pokemons.txt", "w") as txt_file:
                txt_file.write("\n".join(plain_list))
        except Exception as e:
            print(f"Error saving plain list file: {e}")

    def on_mousewheel(self, event):
        self.canvas.yview_scroll(-1 * (event.delta // 120), "units")
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def update_pokemon_icon(self, label):
        selected_pokemon_name = self.selected_pokemon.get().lower()
        index = next((i for i, pokemon in enumerate(self.pokemon_data) if pokemon["name"].lower() == selected_pokemon_name), None)

        if index is not None:
            image_path = f"images/{index + 1}.png"

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
        style.theme_use('clam')  # Example theme, 'clam', 'alt', 'default', 'classic' can also be used

        # Configure ttk Button style for uniformity
        style.configure('TButton', padding=6, relief="flat", background="#ccc")

        # Configure the ttk Entry style
        style.configure('TEntry', padding=6)

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
        self.generate_button = ttk.Button(top_frame, text="Generate JSON", command=self.generate_json)
        self.generate_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.generate_plain_list_button = ttk.Button(top_frame, text="Generate Plain List", command=self.generate_plain_list)
        self.generate_plain_list_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.deselect_button = ttk.Button(top_frame, text="Deselect All", command=self.deselect_all)
        self.deselect_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.toggle_view_button = ttk.Button(top_frame, text="Show Picked Only", command=self.toggle_view)
        self.toggle_view_button.pack(side=tk.LEFT, padx=5, pady=5)

        # Bottom frame for the Pokémon selection and details display
        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        # Canvas and scrollbar within the bottom frame
        self.canvas = tk.Canvas(bottom_frame, width=120 * 10 + 20, height=100 * ((len(self.pokemon_data) - 1) // 10 + 1) + 20)
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
        self.details_title = tk.Label(self.details_frame, text="Pokémon Details", font=("Arial",16))
        self.details_title.pack(pady=(5, 10))

        self.details_text = tk.Text(self.details_frame, wrap=tk.WORD, font=("Arial", 12), state=tk.DISABLED)
        self.details_text.pack(fill=tk.BOTH, expand=True)

        # Pokémon image placeholders and labels
        self.pokemon_images = []
        self.pokemon_labels = []
        self.placeholder_img = ImageTk.PhotoImage(Image.new("RGBA", (96, 96), (255, 255, 255, 0)))

        for i, pokemon in enumerate(self.pokemon_data):
            image_path = f"images/{i + 1}.png"
            try:
                img = Image.open(image_path)
                img = img.resize((96, 96), Image.LANCZOS)
                img = ImageTk.PhotoImage(img)
                self.pokemon_images.append(img)
            except FileNotFoundError:
                img = self.placeholder_img

            label = tk.Label(self.frame, image=img, text=pokemon["name"].capitalize(), compound='top', bd=0)
            label.image = img  # Keep a reference to avoid garbage collection
            label.bind("<Button-1>", lambda event, name=pokemon["name"], label=label: self.pick_pokemon(name, label))
            self.pokemon_labels.append(label)
            label.grid(row=i // 10, column=i % 10, padx=5, pady=5)

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

    def update_icons(self):
        for label in self.pokemon_labels:
            self.update_pokemon_icon(label)

    def pick_pokemon(self, selected_pokemon_name, label):
        if selected_pokemon_name in self.selected_pokemons:
            self.selected_pokemons.remove(selected_pokemon_name)
        else:
            self.selected_pokemons.append(selected_pokemon_name)

        self.selected_pokemon.set(selected_pokemon_name)
        self.update_pokemon_icon(label)

        for label in self.pokemon_labels:
            if label["text"].lower() in self.selected_pokemons:
                label.config(bd=3, relief="solid")
            else:
                label.config(bd=3, relief="flat")
        # Fetch details for the selected Pokémon and display them
        details, stats = self.fetch_pokemon_details(selected_pokemon_name)
        print(f"Details fetched for {selected_pokemon_name}: {details}")  # Debug print
        self.display_pokemon_details(details,stats)
        

    def toggle_view(self):
        # Toggle between full list and picked Pokémon only views
        self.show_full_list = not self.show_full_list

        if self.show_full_list:
            self.show_full_list_view()
            self.toggle_view_button.config(text="Show Picked Only")
        else:
            self.show_picked_pokemon_view()
            self.toggle_view_button.config(text="Show All")

        # Reset vertical scroll position to the top
        self.canvas.yview_moveto(0)

    def show_full_list_view(self):
        for i, label in enumerate(self.pokemon_labels):
            col = i % 10
            row = i // 10
            label.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

    def show_picked_pokemon_view(self):
        selected_labels = [label for label in self.pokemon_labels if label["text"].lower() in self.selected_pokemons]

        for i, label in enumerate(selected_labels):
            col = i % 10
            row = i // 10
            label.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

        for label in self.pokemon_labels:
            if label not in selected_labels:
                label.grid_forget()

    def filter_pokemon_list_view(self, event):
        search_query = self.search_entry.get().lower()

        # Forget all labels to clear the canvas
        for label in self.pokemon_labels:
            label.grid_forget()

        # Filter and create labels based on the search query
        selected_labels = [
            label
            for label in self.pokemon_labels
            if search_query in label["text"].lower()
        ]

        for i, label in enumerate(selected_labels):
            col = i % 10
            new_row = i // 10
            label.grid(row=new_row, column=col, padx=5, pady=5, sticky="nsew")

        # Update the scroll region after reorganizing labels
        self.canvas.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

        # Reset the scrollbar position to the top
        self.canvas.yview_moveto(0)


    def fetch_pokemon_details(self, pokemon_name):
        api_url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}"
        try:
            response = requests.get(api_url)
            response.raise_for_status()  # Check for HTTP errors

            # Parse the JSON response
            pokemon_data = response.json()

            # Extract types
            types = [type_info['type']['name'] for type_info in pokemon_data['types']]

            # Extract abilities
            abilities = [abilities_info['ability']['name'] for abilities_info in pokemon_data['abilities']]
            print(f"abilities of {pokemon_name.capitalize()} : {abilities}")

            # Extract stats
            stats = {stat_info['stat']['name']: stat_info['base_stat'] for stat_info in pokemon_data['stats']}

            # Format the details for display
            details = f"Name: {pokemon_name.capitalize()}\nTypes: {', '.join(types)}\n"

            return details, stats
        except requests.exceptions.RequestException as e:
            print(f"Error fetching details for {pokemon_name}: {e}")
            return "Failed to fetch details.", {}

        
    def display_stat_bars(self, stats):
        # Define a maximum value for stats to normalize the bar length
        max_stat_value = 150

        for stat, value in stats.items():
            # Create a frame for each stat
            stat_frame = tk.Frame(self.details_frame)
            stat_frame.pack(fill=tk.X, padx=5, pady=2)

            # Create a label with the stat name
            tk.Label(stat_frame, text=f"{stat.capitalize()}:").pack(side=tk.LEFT)

            # Create a canvas for the bar
            canvas = tk.Canvas(stat_frame, width=100, height=10)
            canvas.pack(side=tk.LEFT, fill=tk.X, expand=True)

            # Normalize the stat value to the canvas width
            bar_length = (value / max_stat_value) * (canvas.winfo_reqwidth())

            # Choose a color for the bar based on the stat type
            bar_color = self.get_stat_color(stat)

            # Draw the bar
            canvas.create_rectangle(10, 2, bar_length, 12, fill=bar_color, outline=bar_color)


    def get_stat_color(self, stat):
        # Return a color based on the stat name
        colors = {
            'hp': 'green',
            'attack': 'red',
            'defense': 'orange',
            'special-attack': 'pink',
            'special-defense': 'blue',
            'speed': 'cyan'
        }
        return colors.get(stat.lower(), 'grey')

    def display_pokemon_details(self, details, stats):
        # Make sure the text widget is in the normal state before inserting text
        self.details_text.config(state=tk.NORMAL)
        self.details_text.delete('1.0', tk.END)
        self.details_text.insert(tk.END, details)
        self.details_text.config(state=tk.DISABLED)

        # Display stat bars for each stat
        self.display_stat_bars(stats)

if __name__ == "__main__":
    root = tk.Tk()
    app = PokemonPicker(root)
    root.mainloop()
