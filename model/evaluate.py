
import numpy as np
import tensorflow as tf

from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
    roc_auc_score
)

from utils.preprocessing import load_datasets

# 1. Load test dataset
train_ds, val_ds, test_ds = load_datasets()

# 2. Load trained model
MODEL_PATH = "model/saved_models/medical_model.keras"

model = tf.keras.models.load_model(MODEL_PATH)

print("\nModel loaded successfully!")

# 3. Get actual labels
y_true = np.concatenate([
    labels.numpy().flatten()
    for _, labels in test_ds
]).astype(int)

# 4. Generate predictions
predictions = model.predict(test_ds)

# Sigmoid output probabilities
y_prob = predictions.flatten()

# Convert probabilities to class labels
y_pred = (y_prob >= 0.5).astype(int)

# 5. Calculate accuracy
accuracy = accuracy_score(y_true, y_pred)

print("\nTest Accuracy:", round(accuracy * 100, 2), "%")

# 6. Classification report
print("\nClassification Report:")

print(
    classification_report(
        y_true,
        y_pred,
        labels=[0, 1],
        target_names=["NORMAL", "PNEUMONIA"],
        zero_division=0
    )
)

# 7. Confusion matrix
print("\nConfusion Matrix:")

cm = confusion_matrix(y_true, y_pred)

print(cm)

# 8. ROC-AUC
auc = roc_auc_score(y_true, y_prob)

print("\nROC-AUC:", round(auc, 4))

print("\nEvaluation completed!")
