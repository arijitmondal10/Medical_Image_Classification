
import json
import matplotlib.pyplot as plt
from pathlib import Path

# Locate training history
BASE_DIR = Path(__file__).resolve().parent
HISTORY_PATH = BASE_DIR / "training_history.json"

# Load history
with open(HISTORY_PATH, "r") as file:
    history = json.load(file)

epochs = range(1, len(history["accuracy"]) + 1)

# Accuracy graph
plt.figure(figsize=(9, 5))

plt.plot(epochs, history["accuracy"], marker="o", label="Training Accuracy")
plt.plot(epochs, history["val_accuracy"], marker="o", label="Validation Accuracy")

plt.title("MobileNetV2 - Training and Validation Accuracy")
plt.xlabel("Epochs")
plt.ylabel("Accuracy")
plt.xticks(list(epochs))
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()

accuracy_path = BASE_DIR / "accuracy_graph.png"
plt.savefig(accuracy_path, dpi=300)
plt.show()

# Loss graph
plt.figure(figsize=(9, 5))

plt.plot(epochs, history["loss"], marker="o", label="Training Loss")
plt.plot(epochs, history["val_loss"], marker="o", label="Validation Loss")

plt.title("MobileNetV2 - Training and Validation Loss")
plt.xlabel("Epochs")
plt.ylabel("Loss")
plt.xticks(list(epochs))
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()

loss_path = BASE_DIR / "loss_graph.png"
plt.savefig(loss_path, dpi=300)
plt.show()

print("Graphs generated successfully!")
print("Accuracy graph:", accuracy_path)
print("Loss graph:", loss_path)
