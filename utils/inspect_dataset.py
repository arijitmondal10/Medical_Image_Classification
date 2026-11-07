from pathlib import Path

# Locate the raw dataset folder
DATASET_PATH = Path(__file__).resolve().parent.parent / "dataset" / "raw"
print("Looking for dataset at:", DATASET_PATH)
print("Does this folder exist?", DATASET_PATH.exists())

# Supported image formats
IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"
}

print("\n========== MEDVISION DATASET INSPECTION ==========\n")

if not DATASET_PATH.exists():
    print("Dataset folder not found!")
else:
    for folder in sorted(DATASET_PATH.iterdir()):

        if folder.is_dir():

            print(f"\nDATASET: {folder.name}")
            print("-" * 40)

            for subfolder in sorted(folder.rglob("*")):

                if subfolder.is_dir():

                    image_count = sum(
                        1 for file in subfolder.iterdir()
                        if file.is_file()
                        and file.suffix.lower() in IMAGE_EXTENSIONS
                    )

                    if image_count > 0:
                        print(
                            f"{subfolder.relative_to(folder)}: "
                            f"{image_count} images"
                        )

print("\n========== INSPECTION COMPLETE ==========\n")