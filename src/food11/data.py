
import os
import shutil

from PIL import Image

RAW_DIR = "data/food11_raw"
PROCESSED_DIR = "data/food11_processed"
MINI_DIR = "data/food11_processed_mini"

splits = ["training", "evaluation", "validation"]

CLASSES = [
    "Bread", "Dairy product", "Dessert", "Egg",
    "Fried food", "Meat", "Noodles-Pasta", "Rice",
    "Seafood", "Soup", "Vegetable-Fruit"
]

categories = {str(i): name for i, name in enumerate(CLASSES)}


def category_from_filename(filename: str) -> str:
    category_id = int(filename.split("_")[0])
    return CLASSES[category_id]


def resize_image(img: Image.Image, size: int = 128) -> Image.Image:
    return img.convert("RGB").resize((size, size))


def main():
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
                processed_path = os.path.join(
                    processed_folder, filename
                )

                with Image.open(source_path) as image:
                    image = resize_image(image)
                    image.save(processed_path)

                # Mini dataset: maximum 100 images per category
                if index < 100:
                    shutil.copy2(
                        processed_path,
                        os.path.join(mini_folder, filename)
                    )

    print("Food-11 preprocessing completed!")


if __name__ == "__main__":
    main()
