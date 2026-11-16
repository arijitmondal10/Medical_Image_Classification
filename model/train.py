import json
from pathlib import Path


import numpy as np
import tensorflow as tf
from tensorflow.keras import layers
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.callbacks import (
    EarlyStopping,
    ModelCheckpoint
)

from utils.preprocessing import load_datasets

# Configuration
IMAGE_SIZE = (224, 224)
EPOCHS = 10
LEARNING_RATE = 0.0001

MODEL_PATH = (
    Path(__file__).resolve().parent
    / "saved_models"
    / "medical_model.keras"
)

MODEL_PATH.parent.mkdir(
    parents=True,
    exist_ok=True
)

# Load datasets
train_ds, val_ds, test_ds = load_datasets()

# Calculate class weights using training labels
labels = np.concatenate([
    y.numpy().flatten()
    for _, y in train_ds
]).astype(int)

class_counts = np.bincount(labels, minlength=2)
total = class_counts.sum()

class_weights = {
    i: float(total / (2 * count))
    for i, count in enumerate(class_counts)
}

print("Training class counts:", class_counts)
print("Class weights:", class_weights)

# Load pretrained MobileNetV2
base_model = MobileNetV2(
    input_shape=(*IMAGE_SIZE, 3),
    include_top=False,
    weights="imagenet"
)

# Freeze pretrained layers
base_model.trainable = False

# Build model
inputs = tf.keras.Input(shape=(*IMAGE_SIZE, 3))

# Keep Batch Normalization layers in inference mode
x = base_model(inputs, training=False)

x = layers.GlobalAveragePooling2D()(x)
x = layers.Dropout(0.3)(x)

outputs = layers.Dense(
    1,
    activation="sigmoid"
)(x)

model = tf.keras.Model(
    inputs=inputs,
    outputs=outputs
)

# Compile model
model.compile(
    optimizer=tf.keras.optimizers.Adam(
        learning_rate=LEARNING_RATE
    ),
    loss="binary_crossentropy",
    metrics=[
        "accuracy",
        tf.keras.metrics.AUC(name="auc")
    ]
)

model.summary()

# Callbacks
early_stopping = EarlyStopping(
    monitor="val_loss",
    patience=3,
    restore_best_weights=True
)

checkpoint = ModelCheckpoint(
    filepath=str(MODEL_PATH),
    monitor="val_loss",
    save_best_only=True
)

reduce_lr = tf.keras.callbacks.ReduceLROnPlateau(
    monitor="val_loss",
    factor=0.2,
    patience=2,
    min_lr=0.000001
)

# Train model
history = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=EPOCHS,
    class_weight=class_weights,
    callbacks=[
        early_stopping,
        reduce_lr,
        checkpoint
    ]
)

# Save training history
history_path = Path(__file__).resolve().parent / "training_history.json"

with open(history_path, "w") as file:
    json.dump(
        {
            key: [float(value) for value in values]
            for key, values in history.history.items()
        },
        file,
        indent=4
    )

print("Training history saved:", history_path)

print("\nTraining completed!")
print("Best model saved to:", MODEL_PATH)
