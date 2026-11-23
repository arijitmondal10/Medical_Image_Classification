
import os
import tensorflow as tf
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input

# Dataset location
DATASET_PATH = r"C:\Users\ARIJIT MONDAL\OneDrive\Desktop\MedVision_Dataset\dataset\raw\chest_xray"

# Image configuration
IMAGE_SIZE = (224, 224)
BATCH_SIZE = 32
SEED = 42

def load_datasets():

    train_path = os.path.join(DATASET_PATH, "train")
    test_path = os.path.join(DATASET_PATH, "test")

    # Create training dataset
    train_dataset = tf.keras.utils.image_dataset_from_directory(
    train_path,
    validation_split=0.20,
    subset="training",
    seed=SEED,
    image_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE,
    label_mode="binary"
    )

    class_names = sorted(os.listdir(train_path))

    class_names = [
        name for name in class_names
        if os.path.isdir(os.path.join(train_path, name))
    ]

    print("Class order:", class_names)

    # Create validation dataset
    val_dataset = tf.keras.utils.image_dataset_from_directory(
        train_path,
        validation_split=0.20,
        subset="validation",
        seed=SEED,
        image_size=IMAGE_SIZE,
        batch_size=BATCH_SIZE,
        label_mode="binary"
    )

    # Load original test dataset
    test_dataset = tf.keras.utils.image_dataset_from_directory(
        test_path,
        image_size=IMAGE_SIZE,
        batch_size=BATCH_SIZE,
        label_mode="binary",
        shuffle=False
    )

    # Apply MobileNetV2 preprocessing
    def prepare_images(images, labels):
        images = preprocess_input(images)
        return images, labels

    train_dataset = train_dataset.map(prepare_images)
    val_dataset = val_dataset.map(prepare_images)
    test_dataset = test_dataset.map(prepare_images)

    return train_dataset, val_dataset, test_dataset


if __name__ == "__main__":

    train_ds, val_ds, test_ds = load_datasets()

    print("\nDataset loaded successfully!")

    print("Training batches:", len(train_ds))
    print("Validation batches:", len(val_ds))
    print("Testing batches:", len(test_ds))
