
import os

DATASET_PATH = r"C:\Users\ARIJIT MONDAL\OneDrive\Desktop\MedVision_Dataset\dataset\raw\chest_xray"

folders = ["train", "val", "test"]

for folder in folders:

    folder_path = os.path.join(DATASET_PATH, folder)

    print(f"\n--- {folder.upper()} ---")

    if not os.path.exists(folder_path):
        print("Folder not found!")
        continue

    for category in os.listdir(folder_path):

        category_path = os.path.join(folder_path, category)

        if os.path.isdir(category_path):

            images = [
                file for file in os.listdir(category_path)
                if file.lower().endswith((".jpg", ".jpeg", ".png"))
            ]

            print(f"{category}: {len(images)} images")