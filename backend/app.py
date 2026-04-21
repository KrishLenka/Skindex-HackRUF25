# app.py
import io
import os
import json
import ssl
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Tuple

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent / ".env")
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    import sys

    print(
        "Warning: python-dotenv is not installed; .env will not be loaded. "
        "Run: pip install python-dotenv",
        file=sys.stderr,
    )

from PIL import Image
import numpy as np

from flask import Flask, request, jsonify
from flask_cors import CORS
from auth import auth_bp, db

# TensorFlow / Keras (install tensorflow separately if needed)
try:
    import tensorflow as tf
except ImportError:
    tf = None

# PyTorch
import torch
import torch.nn.functional as F
import torchvision.transforms as T
import timm

# ONNX Runtime
import onnxruntime as ort

# ---------------------------
# CONFIG - update these paths
# ---------------------------
MODEL_DIR = Path(__file__).resolve().parent / "models"
TF_MODEL_PATH = MODEL_DIR / "tf_skin_model"    # either SavedModel dir or .h5
# Training writes pt_skin_model.pth; best_model.pth is the full checkpoint — use whichever exists
PYTORCH_MODEL_PATH = next(
    (MODEL_DIR / n for n in ("pt_skin_model.pth", "best_model.pth") if (MODEL_DIR / n).is_file()),
    MODEL_DIR / "pt_skin_model.pth",
)
ONNX_MODEL_PATH = MODEL_DIR / "skin_model.onnx"

# Load class names from training (will be auto-populated during training)
# Default classes for the 10-class skin condition dataset
CLASS_NAMES = [
    "ACNE",
    "GROWTH_OR_MOLE",
    "HAIR_LOSS",
    "LOOKS_HEALTHY",
    "NAIL_PROBLEM",
    "OTHER_HAIR_PROBLEM",
    "PIGMENTARY_PROBLEM",
    "RASH",
]
IMG_SIZE = 224
# Automatically detect best available device: NVIDIA CUDA > Apple Silicon MPS > CPU
if torch.cuda.is_available():
    DEVICE = "cuda"
elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
    DEVICE = "mps"
else:
    DEVICE = "cpu"
# ---------------------------

# DeepSeek — OpenAI-compatible chat API (https://api-docs.deepseek.com/)
DEEPSEEK_API_URL = os.environ.get(
    "DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions"
)
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "").strip()
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-me-before-deploying")
_DB_PATH = Path(__file__).parent / "instance" / "users.db"
_DB_PATH.parent.mkdir(exist_ok=True)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{_DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

CORS(
    app,
    resources={r"/*": {"origins": ["http://localhost:5173", "http://127.0.0.1:5173"]}},
    methods=["GET", "POST", "PUT", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

db.init_app(app)
app.register_blueprint(auth_bp)

with app.app_context():
    db.create_all()
    # Seed a demo user on first run so fresh clones are immediately usable
    from auth import User
    from werkzeug.security import generate_password_hash
    if not User.query.first():
        demo = User(
            name="Demo User",
            email="demo@dermai.com",
            password_hash=generate_password_hash("test1234"),
        )
        db.session.add(demo)
        db.session.commit()
        print("[seed] Created demo user: demo@dermai.com / test1234")

# ---------------------------
# Preprocessing helpers
# ---------------------------
IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)

def pil_to_numpy(img: Image.Image, size=IMG_SIZE) -> np.ndarray:
    """Resize and return HxWxC float32 image scaled to [0,1]."""
    img = img.convert("RGB")
    img = img.resize((size, size), Image.BILINEAR)
    arr = np.asarray(img).astype(np.float32) / 255.0
    return arr

def normalize_imagenet(img_np: np.ndarray) -> np.ndarray:
    """Normalize using ImageNet mean/std. Expects HWC float in [0,1]."""
    return (img_np - IMAGENET_MEAN) / IMAGENET_STD

def prepare_for_tf(img_np: np.ndarray) -> np.ndarray:
    """Return batched NHWC float32 for TF."""
    x = normalize_imagenet(img_np)
    x = np.expand_dims(x.astype(np.float32), axis=0)
    return x

def prepare_for_torch(img_np: np.ndarray) -> torch.Tensor:
    """Return batched NCHW torch tensor on DEVICE."""
    x = normalize_imagenet(img_np)
    x = np.transpose(x, (2,0,1))  # HWC -> CHW
    x = np.expand_dims(x, axis=0)
    t = torch.from_numpy(x.astype(np.float32)).to(DEVICE)
    return t

def prepare_for_onnx(img_np: np.ndarray) -> np.ndarray:
    """Return batched input for ONNX (NCHW) as float32 numpy."""
    x = normalize_imagenet(img_np)
    x = np.transpose(x, (2,0,1))  # CHW
    x = np.expand_dims(x, axis=0)
    return x.astype(np.float32)

# ---------------------------
# Model loaders
# ---------------------------
print("="*70)
print("INITIALIZING SKIN CONDITION CLASSIFIER API")
print("="*70)
print(f"Device: {DEVICE.upper()}")
if DEVICE == "cuda":
    print(f"GPU: {torch.cuda.get_device_name(0)}")
elif DEVICE == "mps":
    print(f"GPU: Apple Silicon (MPS)")
else:
    print(f"GPU: Not available - using CPU")
print("="*70)
print("\nLoading models...")

# 1) TensorFlow / Keras
tf_model = None
try:
    if TF_MODEL_PATH.suffix == ".h5":
        tf_model = tf.keras.models.load_model(str(TF_MODEL_PATH))
    else:
        tf_model = tf.keras.models.load_model(str(TF_MODEL_PATH))
    print("Loaded TensorFlow model.")
except Exception as e:
    print("Warning: TF model load failed:", e)
    tf_model = None

# 2) PyTorch model
pt_model = None
try:
    class PTWrapper(torch.nn.Module):
        def __init__(self, model_name="efficientnet_b0", n_classes=len(CLASS_NAMES), pretrained=False, dropout=0.3):
            super().__init__()
            self.backbone = timm.create_model(model_name, pretrained=pretrained, num_classes=0, global_pool='avg')
            feat = self.backbone.num_features
            self.head = torch.nn.Sequential(
                torch.nn.Linear(feat, 512),
                torch.nn.ReLU(inplace=True),
                torch.nn.Dropout(dropout),
                torch.nn.Linear(512, n_classes)
            )
        def forward(self, x):
            x = self.backbone(x)
            x = self.head(x)
            return x

    pt_model = PTWrapper(model_name="efficientnet_b0", n_classes=len(CLASS_NAMES), pretrained=False, dropout=0.3)
    state = torch.load(str(PYTORCH_MODEL_PATH), map_location=DEVICE)
    if isinstance(state, dict) and "model_state_dict" in state:
        state = state["model_state_dict"]
    pt_model.load_state_dict(state)
    pt_model.to(DEVICE)
    pt_model.eval()
    print("Loaded PyTorch model.")
except Exception as e:
    print("Warning: PyTorch model load failed:", e)
    pt_model = None

# 3) ONNX Runtime model
onnx_sess = None
try:
    onnx_sess = ort.InferenceSession(str(ONNX_MODEL_PATH), providers=["CPUExecutionProvider"])
    # if GPU available and onnxruntime-gpu installed:
    # onnx_sess = ort.InferenceSession(str(ONNX_MODEL_PATH), providers=["CUDAExecutionProvider"])
    print("Loaded ONNX model.")
except Exception as e:
    print("Warning: ONNX model load failed:", e)
    onnx_sess = None

AVAILABLE_MODELS = {
    "tf": tf_model is not None,
    "pt": pt_model is not None,
    "onnx": onnx_sess is not None
}
print("Available models:", AVAILABLE_MODELS)

# ---------------------------
# Inference wrappers
# ---------------------------
def predict_tf(img_np: np.ndarray) -> np.ndarray:
    """Run TF model => returning softmax probabilities as 1D numpy array."""
    if tf_model is None:
        raise RuntimeError("TF model not loaded")
    x = prepare_for_tf(img_np)  # NHWC
    probs = tf_model(x, training=False).numpy()
    probs = softmax_numpy(probs[0])
    return probs

def predict_pt(img_np: np.ndarray) -> np.ndarray:
    if pt_model is None:
        raise RuntimeError("PyTorch model not loaded")
    x = prepare_for_torch(img_np)  # NCHW torch tensor
    with torch.no_grad():
        outputs = pt_model(x)
        probs = F.softmax(outputs, dim=1).detach().cpu().numpy()[0]
    return probs

def predict_onnx(img_np: np.ndarray) -> np.ndarray:
    if onnx_sess is None:
        raise RuntimeError("ONNX model not loaded")
    x = prepare_for_onnx(img_np)  # NCHW numpy
    # find input name
    input_name = onnx_sess.get_inputs()[0].name
    out_name = onnx_sess.get_outputs()[0].name
    raw = onnx_sess.run([out_name], {input_name: x})
    logits = raw[0][0]
    probs = softmax_numpy(logits)
    return probs

def softmax_numpy(x: np.ndarray) -> np.ndarray:
    e = np.exp(x - np.max(x))
    return e / e.sum()

# ---------------------------
# Ensemble logic
# ---------------------------
def ensemble_predict(probs_list: List[np.ndarray], class_names: List[str]) -> Dict:
    """
    probs_list: list of 1D arrays from each model (length = n_classes)
    returns dict with per-model top predictions and ensemble summary.
    """
    # stack and check shapes
    probs_stack = np.vstack(probs_list)  # shape (n_models, n_classes)
    avg_probs = probs_stack.mean(axis=0)
    ensemble_class_idx = int(np.argmax(avg_probs))
    ensemble_class = class_names[ensemble_class_idx]
    ensemble_confidence = float(avg_probs[ensemble_class_idx])  # [0,1], average prob for predicted class

    # per-model top classes
    per_model_preds = []
    for probs in probs_list:
        idx = int(np.argmax(probs))
        per_model_preds.append({
            "class": class_names[idx],
            "class_idx": idx,
            "prob": float(probs[idx]),
            "all_probs": probs.tolist()
        })

    # agreement score: fraction of models that predicted the ensemble_class
    votes = [1 if p["class_idx"] == ensemble_class_idx else 0 for p in per_model_preds]
    agreement = float(sum(votes) / len(votes))

    # simple calibrated confidence combining agreement and avg_probs:
    # final_confidence = ensemble_confidence * (0.6 + 0.4 * agreement)
    final_confidence = float(ensemble_confidence * (0.6 + 0.4 * agreement))

    return {
        "ensemble_class": ensemble_class,
        "ensemble_class_idx": ensemble_class_idx,
        "ensemble_avg_probs": avg_probs.tolist(),
        "ensemble_confidence_raw": ensemble_confidence,
        "agreement": agreement,
        "final_confidence": final_confidence,
        "per_model": per_model_preds
    }

# ---------------------------
# Advice mapping for 8 SCIN classes
# ---------------------------
# Specific advice for the 8 SCIN skin condition classes
SPECIFIC_ADVICE = {
    "LOOKS_HEALTHY": {
        "short": "Skin appears healthy. Continue regular skin checks and use sun protection daily.",
        "urgency": "low",
        "recommendation": "Maintain good skin care routine and monitor for changes"
    },
    "ACNE": {
        "short": "Possible acne detected. Keep the area clean and avoid picking. Consider over-the-counter treatments.",
        "urgency": "low",
        "recommendation": "Try OTC benzoyl peroxide or salicylic acid; see a dermatologist if persistent"
    },
    "GROWTH_OR_MOLE": {
        "short": "Possible growth or mole detected. Have it evaluated by a dermatologist — some growths require biopsy.",
        "urgency": "high",
        "recommendation": "Schedule a dermatology appointment for evaluation and possible biopsy"
    },
    "RASH": {
        "short": "Possible rash detected. Avoid irritants and monitor for spreading. Seek medical advice if worsening.",
        "urgency": "medium",
        "recommendation": "See a doctor if rash spreads, worsens, or is accompanied by fever"
    },
    "PIGMENTARY_PROBLEM": {
        "short": "Pigmentation change detected (e.g., vitiligo or hyperpigmentation). Consult a dermatologist for treatment options.",
        "urgency": "low",
        "recommendation": "Schedule a dermatology appointment to discuss management options"
    },
    "HAIR_LOSS": {
        "short": "Hair loss detected. This may be alopecia or a related condition. Medical evaluation recommended.",
        "urgency": "medium",
        "recommendation": "See a dermatologist to determine the cause and explore treatment options"
    },
    "OTHER_HAIR_PROBLEM": {
        "short": "Hair or scalp condition detected. Evaluation by a dermatologist can determine the best treatment.",
        "urgency": "medium",
        "recommendation": "Schedule a dermatology appointment if symptoms persist or worsen"
    },
    "NAIL_PROBLEM": {
        "short": "Nail condition detected (possible fungal infection or nail disease). Medical evaluation recommended.",
        "urgency": "medium",
        "recommendation": "See a dermatologist or doctor for proper diagnosis and treatment"
    },
}

def get_advice(condition_name):
    """Fallback advice for any condition not covered by SPECIFIC_ADVICE."""
    return {
        "short": f"Possible {condition_name} detected. Consider consulting a dermatologist for proper diagnosis.",
        "urgency": "medium",
        "recommendation": "Schedule a dermatology appointment if symptoms persist or worsen"
    }

# ---------------------------
# Routes
# ---------------------------
@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"status": "ok", "models": AVAILABLE_MODELS})

@app.route("/predict", methods=["POST"])
def predict():
    """
    Accepts: multipart form with 'file' field containing the image.
    Returns JSON with per-model predictions and ensemble.
    """
    if "file" not in request.files:
        return jsonify({"error": "no file provided"}), 400
    file = request.files["file"]
    try:
        image = Image.open(io.BytesIO(file.read()))
    except Exception as e:
        return jsonify({"error": "invalid image", "detail": str(e)}), 400

    img_np = pil_to_numpy(image, size=IMG_SIZE)

    probs_list = []
    used_models = []
    errors = {}
    # Try TF
    try:
        if tf_model is not None:
            p = predict_tf(img_np)
            probs_list.append(p)
            used_models.append("tf")
    except Exception as e:
        errors["tf"] = str(e)
    # PyTorch
    try:
        if pt_model is not None:
            p = predict_pt(img_np)
            probs_list.append(p)
            used_models.append("pt")
    except Exception as e:
        errors["pt"] = str(e)
    # ONNX
    try:
        if onnx_sess is not None:
            p = predict_onnx(img_np)
            probs_list.append(p)
            used_models.append("onnx")
    except Exception as e:
        errors["onnx"] = str(e)

    if len(probs_list) == 0:
        return jsonify({"error": "no models available", "detail": errors}), 500

    # Build ensemble
    ensemble = ensemble_predict(probs_list, CLASS_NAMES)

    # Advice - use specific advice if available, otherwise generate intelligent advice
    label = ensemble["ensemble_class"]
    if label in SPECIFIC_ADVICE:
        advice = SPECIFIC_ADVICE[label]
    else:
        advice = get_advice(label)

    response = {
        "prediction": label,
        "prediction_idx": ensemble["ensemble_class_idx"],
        "final_confidence": ensemble["final_confidence"],
        "agreement": ensemble["agreement"],
        "ensemble_avg_probs": ensemble["ensemble_avg_probs"],
        "per_model_predictions": ensemble["per_model"],
        "advice": advice,
        "errors": errors
    }

    # Medical disclaimer (must be surfaced on client)
    response["disclaimer"] = ("This tool is for informational/demo purposes only. "
                              "Not a medical diagnosis. Seek a qualified clinician for medical advice.")

    return jsonify(response)


def _build_diagnosis_system_prompt(ctx: Dict[str, Any]) -> str:
    """Context from the client about the screening result (educational chat only)."""
    lines = [
        "You are a supportive health-education assistant. The user reviewed an AI-assisted "
        "skin image screening from a demo app — this is NOT a medical diagnosis.",
        "",
        "Screening context (background only):",
    ]
    if ctx.get("condition"):
        lines.append(f"- Condition label: {ctx['condition']}")
    if ctx.get("confidence") is not None:
        lines.append(f"- Model confidence: {ctx['confidence']}%")
    if ctx.get("severity"):
        lines.append(f"- Severity (UI): {ctx['severity']}")
    if ctx.get("description"):
        lines.append(f"- Summary: {ctx['description']}")
    recs = ctx.get("recommendations") or []
    if isinstance(recs, list) and recs:
        lines.append("- General tips already shown: " + "; ".join(str(r) for r in recs[:8]))
    dx = ctx.get("differentialDx") or []
    if isinstance(dx, list) and dx:
        lines.append("- Other possibilities mentioned: " + ", ".join(str(x) for x in dx[:6]))
    if ctx.get("bodyPart"):
        lines.append(f"- Body area (user): {ctx['bodyPart']}")
    syms = ctx.get("symptoms") or []
    if isinstance(syms, list) and syms:
        lines.append(f"- Symptoms (user): {', '.join(str(s) for s in syms)}")
    if ctx.get("notes"):
        lines.append(f"- Extra notes (user): {ctx['notes']}")
    lines.extend(
        [
            "",
            "Guidelines:",
            "- Explain in plain language; suggest general self-care and when to seek in-person care.",
            "- Never claim certainty or that this chat replaces a clinician; encourage dermatology for changing or worrying lesions.",
            "- If asked for a definitive diagnosis, say only a qualified professional can diagnose.",
            "- Keep answers concise and practical.",
        ]
    )
    return "\n".join(lines)


@app.route("/diagnosis-chat", methods=["POST"])
def diagnosis_chat():
    """Proxy to DeepSeek chat API; API key stays on the server."""
    if not DEEPSEEK_API_KEY:
        return jsonify(
            {
                "error": "Diagnosis chat is not configured. Set the DEEPSEEK_API_KEY environment variable on the server.",
            }
        ), 503

    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()
    if not user_message:
        return jsonify({"error": "message is required"}), 400
    if len(user_message) > 8000:
        return jsonify({"error": "message too long"}), 400

    history = data.get("history") or []
    if not isinstance(history, list):
        history = []
    trimmed: List[Dict[str, str]] = []
    for item in history[-24:]:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = (item.get("content") or "").strip()
        if role not in ("user", "assistant") or not content:
            continue
        if len(content) > 8000:
            content = content[:8000]
        trimmed.append({"role": role, "content": content})

    ctx = data.get("context")
    if not isinstance(ctx, dict):
        ctx = {}
    system_prompt = _build_diagnosis_system_prompt(ctx)

    messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]
    messages.extend(trimmed)
    messages.append({"role": "user", "content": user_message})

    payload = json.dumps(
        {
            "model": DEEPSEEK_MODEL,
            "messages": messages,
            "temperature": 0.6,
            "max_tokens": 1024,
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        DEEPSEEK_API_URL,
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120, context=ssl.create_default_context()) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        return jsonify({"error": "Chat provider error", "detail": err_body[:500]}), 502
    except urllib.error.URLError as e:
        return jsonify({"error": "Could not reach chat provider", "detail": str(e)}), 502

    try:
        parsed = json.loads(raw)
        reply = parsed["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as e:
        return jsonify({"error": "Unexpected response from chat provider", "detail": str(e)}), 502

    return jsonify({"reply": reply})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)


