from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import numpy as np
import os
import logging
from flask import send_from_directory


app = Flask(__name__)
CORS(app)


MODEL_PATH = os.path.join(os.path.dirname(__file__), "model", "crop_model.pkl")
LABEL_ENCODER_PATH = os.path.join(os.path.dirname(__file__), "model", "label_encoder.pkl")


if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")

model = joblib.load(MODEL_PATH)

# Try to load label encoder if available (used to map numeric classes back to names)
label_encoder = None
if os.path.exists(LABEL_ENCODER_PATH):
    try:
        label_encoder = joblib.load(LABEL_ENCODER_PATH)
    except Exception:
        label_encoder = None

logger = logging.getLogger('crop_api')
logger.setLevel(logging.INFO)


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})


@app.route('/predict', methods=['POST'])
def predict_crop():
    required = ['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Invalid or missing JSON body'}), 400

    # Validate presence of all required fields
    missing = [k for k in required if k not in data]
    if missing:
        return jsonify({'error': f'Missing fields: {missing}'}), 400

    # Build numeric input and validate types
    try:
        input_vector = [float(data[k]) for k in required]
    except Exception as e:
        return jsonify({'error': f'Invalid input types: {str(e)}'}), 400

    X = [input_vector]

    # Confidence cutoff: can be passed as a query param ?cutoff=0.85 for efficiency or defaults to 0
    try:
        cutoff = float(request.args.get('cutoff', 0)) 
    except Exception:
        cutoff = 0

    # Prediction: prefer predict_proba when available
    try:
        if hasattr(model, 'predict_proba'):
            probs = model.predict_proba(X)[0]
            # get top 3 predictions
            top_idx = np.argsort(probs)[::-1][:3] # return maximum 3 crop recommendation

            classes = model.classes_
            # If label encoder was saved and classes are encoded, map back to names
            if label_encoder is not None:
                try:
                    class_names = label_encoder.inverse_transform(classes.astype(int))
                except Exception:
                    # if classes are already strings, use them directly
                    class_names = classes
            else:
                class_names = classes

            results = []
            for i in top_idx:
                name = class_names[i] if i < len(class_names) else str(classes[i])
                conf = float(probs[i])
                if conf >= cutoff:
                    results.append({'crop': str(name), 'confidence': round(conf * 100, 2)})

            max_conf = float(probs.max())
            response = {'predictions': results, 'max_confidence': round(max_conf * 100, 2)}
            if len(results) == 0:
                response['low_confidence'] = True

            return jsonify(response)
        else:
            pred = model.predict(X)
            # map prediction to name if label encoder exists
            if label_encoder is not None:
                try:
                    pred_name = label_encoder.inverse_transform(pred.astype(int))[0]
                except Exception:
                    pred_name = str(pred[0])
            else:
                pred_name = str(pred[0])
            return jsonify({'predictions': [{'crop': pred_name, 'confidence': 100.0}]})
    except Exception as e:
        logger.exception('Prediction failed')
        return jsonify({'error': f'Prediction failed: {str(e)}'}), 500
@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static_files(path):
    return send_from_directory('.', path)


if __name__ == "__main__":
    # When running locally, enable debug. In production use a WSGI server.
    app.run(host='0.0.0.0', port=5000, debug=True)
