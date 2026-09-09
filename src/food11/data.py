import os
import shutil
from PIL import Image

RAW_DIR = "data/food11_raw"
PROCESSED_DIR = "data/food11_processed"
MINI_DIR = "data/food11_processed_mini"

splits = ["training", "evaluation", "validation"]

categories = {
    "0": "Bread",
    "1": "Dairy product",
    "2": "Dessert",
    "3": "Egg",
    "4": "Fried food",
    "5": "Meat",
    "6": "Noodles-Pasta",
    "7": "Rice",
    "8": "Seafood",
    "9": "Soup",
    "10": "Vegetable-Fruit"
}

for split in splits:
    source_folder = os.path.join(RAW_DIR, split)

    for category_id, category_name in categories.items():

        processed_folder = os.path.join(
            PROCESSED_DIR, split, category_name
        )

        mini_folder = os.path.join(
            MINI_DIR, split, category_name
        )

        os.makedirs(processed_folder, exist_ok=True)
        os.makedirs(mini_folder, exist_ok=True)

        images = [
            filename for filename in os.listdir(source_folder)
            if filename.startswith(category_id + "_")
            and filename.lower().endswith(".jpg")
        ]

        for index, filename in enumerate(images):
            source_path = os.path.join(source_folder, filename)
            processed_path = os.path.join(processed_folder, filename)

            with Image.open(source_path) as image:
                image = image.convert("RGB")
                image = image.resize((128, 128))
                image.save(processed_path)

            # Mini dataset: maximum 100 images per category
            if index < 100:
                shutil.copy2(
                    processed_path,
                    os.path.join(mini_folder, filename)
                )

print("Food-11 preprocessing completed!")