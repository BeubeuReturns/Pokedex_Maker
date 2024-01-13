import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import requests
import json
import threading

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

    def create_widgets(self):
        self.canvas = tk.Canvas(self.root, width=120 * 10 + 20, height=100 * ((len(self.pokemon_data) - 1) // 10 + 1) + 20)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(self.root, command=self.canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.frame, anchor="nw")

        self.pokemon_images = []
        self.pokemon_labels = []

        self.placeholder_img = Image.new("RGBA", (96, 96), (255, 255, 255, 0))
        self.placeholder_img = ImageTk.PhotoImage(self.placeholder_img)

        placeholder_img = Image.new("RGBA", (96, 96), (255, 255, 255, 0))
        placeholder_img = ImageTk.PhotoImage(placeholder_img)

        for i, pokemon in enumerate(self.pokemon_data):
            image_path = f"images/{i + 1}.png"

            try:
                img = Image.open(image_path)
                img = img.resize((96, 96), resample=Image.LANCZOS)
                img = ImageTk.PhotoImage(img)

                self.pokemon_images.append(img)

            except FileNotFoundError:
                img = placeholder_img

            label = tk.Label(
                self.frame,
                image=img,
                text=pokemon["name"].capitalize(),
                bd=0,
            )
            label.image = img
            label.bind("<Button-1>", lambda event, name=pokemon["name"], label=label: self.pick_pokemon(name, label))
            self.pokemon_labels.append(label)

            col = i % 10
            row = i // 10
            label.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

        generate_button = tk.Button(self.root, text="Generate JSON", command=self.generate_json)
        generate_button.pack()

        generate_plain_list_button = tk.Button(self.root, text="Generate Plain List", command=self.generate_plain_list)
        generate_plain_list_button.pack(side=tk.TOP)

        deselect_button = tk.Button(self.root, text="Deselect All", command=self.deselect_all)
        deselect_button.pack(side=tk.TOP)

        # Create the search bar
        self.search_entry = tk.Entry(self.root, width=25)
        self.search_entry.insert(0, "Search by name")
        self.search_entry.bind("<FocusIn>", self.on_search_focus)  # Bind focus event
        self.search_entry.pack(side=tk.TOP, padx=2, pady=5)
        self.search_entry.bind("<KeyRelease>", self.filter_pokemon_list_view)

                # Create the "Toggle View" button
        self.toggle_view_button = tk.Button(self.root, text="Show Picked Only", command=self.toggle_view)
        self.toggle_view_button.pack(side=tk.TOP)

        self.pokemon_icon_label = tk.Label(self.root, width=96, height=96)
        self.pokemon_icon_label.pack()

        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.canvas.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        self.show_full_list_view()


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

    def on_search_focus(self, event):
        if self.search_entry.get() == "Search by name":
            self.search_entry.delete(0, tk.END) 


if __name__ == "__main__":
    root = tk.Tk()
    app = PokemonPicker(root)
    root.mainloop()
