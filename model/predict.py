
from pathlib import Path

import numpy as np
import tensorflow as tf
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input


# Model configuration
BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = BASE_DIR / "saved_models" / "medical_model.keras"

IMAGE_SIZE = (224, 224)

CLASS_NAMES = ["NORMAL", "PNEUMONIA"]


# Load trained model
model = tf.keras.models.load_model(MODEL_PATH)

print("MedVision model loaded successfully!")


def predict_image(image_path):

    # Load uploaded image
    image = tf.keras.utils.load_img(
        image_path,
        target_size=IMAGE_SIZE,
        color_mode="rgb"
    )

    # Convert image into array
    image_array = tf.keras.utils.img_to_array(image)

    # Add batch dimension
    image_array = np.expand_dims(image_array, axis=0)

    # Apply MobileNetV2 preprocessing
    image_array = preprocess_input(image_array)

    # Generate prediction
    prediction = model.predict(image_array, verbose=0)[0][0]

    # Convert probability to class
    predicted_index = 1 if prediction >= 0.5 else 0

    predicted_class = CLASS_NAMES[predicted_index]

    # Class probability
    confidence = (
        prediction * 100
        if predicted_index == 1
        else (1 - prediction) * 100
    )

    return {
        "prediction": predicted_class,
        "confidence": round(float(confidence), 2),
        "pneumonia_score": round(float(prediction), 4)
    }


# Test prediction independently
if __name__ == "__main__":

    test_image = input("Enter X-ray image path: ").strip().strip('"')

    if Path(test_image).is_file():

        result = predict_image(test_image)

        print("\n--- MedVision Prediction ---")
        print("Predicted class:", result["prediction"])
        print("Confidence:", result["confidence"], "%")

    else:
        print("Image file not found. Please check the path.")
