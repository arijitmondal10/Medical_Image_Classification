
from flask import Flask, request, jsonify, render_template
from pathlib import Path
from werkzeug.utils import secure_filename
from uuid import uuid4

from model.predict import predict_image

from database.database import (
    initialize_database,
    save_image,
    save_prediction,
    get_prediction_history
)

app = Flask(__name__)

# Upload configuration
UPLOAD_FOLDER = Path(app.root_path) / "static" / "uploads"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024


# Initialize database when application starts
initialize_database()


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


@app.route("/")
def home():
    return render_template("index.html")


# AI prediction API
@app.route("/predict", methods=["POST"])
def predict():

    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files["image"]

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Unsupported image format"}), 400

    image_category = request.form.get("image_type", "chest_xray")

    original_name = secure_filename(file.filename)

    if not original_name:
        return jsonify({"error": "Invalid filename"}), 400

    extension = original_name.rsplit(".", 1)[1].lower()

    filename = f"{uuid4().hex}.{extension}"

    image_path = UPLOAD_FOLDER / filename

    try:

        # Save uploaded image
        file.save(image_path)

        # Save image information in database
        image_id = save_image(
            user_id=None,
            filename=filename,
            image_category=image_category
        )

        # Run ML model
        result = predict_image(str(image_path))

        prediction = result["prediction"]
        confidence = result["confidence"]

        # Save prediction result in database
        prediction_id = save_prediction(
            image_id=image_id,
            predicted_class=prediction,
            confidence_score=confidence,
            status="completed"
        )

        return jsonify({
            "success": True,
            "prediction": prediction,
            "confidence": confidence,
            "image_id": image_id,
            "prediction_id": prediction_id
        })

    except Exception:

        app.logger.exception("Image prediction failed")

        return jsonify({
            "error": "Unable to process this image. Please try another image."
        }), 500


# Retrieve prediction history
@app.route("/history", methods=["GET"])
def history():

    records = get_prediction_history()

    return jsonify({
        "success": True,
        "history": records
    })


@app.errorhandler(413)
def file_too_large(error):

    return jsonify({
        "error": "Image must be smaller than 10 MB."
    }), 413


if __name__ == "__main__":
    app.run(debug=True)
