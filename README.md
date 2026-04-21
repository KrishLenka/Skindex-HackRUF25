# Skindex -- Skin condition classification (SCIN)

PyTorch training pipeline, Flask REST API, and React frontend for AI-powered skin-image classification using the **[SCIN](https://github.com/google-research-datasets/scin)** public dataset.

---

## Features

- **AI skin analysis** -- upload or photograph a skin area and get a condition classification with severity rating and recommendations
- **User authentication** -- JWT-based register / login / logout
- **Demographic health profile** -- age group, sex at birth, Fitzpatrick skin type, ethnicity, skin texture
- **Scan history** -- every analysis is saved per user; view past scans with full image, context, and AI advice; delete scans
- **Scan context** -- body part, symptoms, and free-text description captured at upload time
- **Profile gate** -- image analysis requires a completed profile (age group + sex at birth minimum) and login

---

## Quick start (cross-machine)

### 1. Clone & install backend

```bash
git clone https://github.com/KrishLenka/Skindex-HackRUF25.git
cd Skindex-HackRUF25/backend
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r ../requirements.txt
pip install torch torchvision timm onnxruntime   # large packages, install separately
```

> **TensorFlow is optional.** It is commented out in `requirements.txt`. `app.py` handles the missing import gracefully.

### 2. Run the backend

```bash
# from backend/
.venv/bin/python3 app.py
```

On first boot the server:
- Creates `backend/instance/users.db` (SQLite, gitignored)
- Seeds a demo account: **`demo@dermai.com` / `test1234`**
- Starts on `http://localhost:8000`

Expected warnings on fresh clone (safe to ignore -- no model files yet):
```
Warning: PyTorch model load failed: No such file or directory: 'models/pt_skin_model.pth'
Warning: ONNX model load failed: ...
```

### 3. Run the frontend

```bash
cd frontend-vite
npm install
npm run dev
# -> http://localhost:5173
```

Vite proxies `/api/*` to `http://localhost:8000` (strips `/api` prefix).

---

## Auth API

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/register` | -- | Create account (`name`, `email`, `password`) |
| POST | `/auth/login` | -- | Authenticate, returns JWT |
| GET | `/auth/me` | Bearer | Current user info |
| PUT | `/auth/profile` | Bearer | Update demographic profile |
| POST | `/scans` | Bearer | Save a scan result |
| GET | `/scans` | Bearer | List user's scans (summary, no images) |
| GET | `/scans/<id>` | Bearer | Full scan detail including image |
| DELETE | `/scans/<id>` | Bearer | Delete a scan |

Include `Authorization: Bearer <token>` for protected routes. Tokens expire after 7 days.

---

## ML model setup

### Download SCIN dataset (one-time, ~12 GB)

Requires [Google Cloud SDK](https://cloud.google.com/sdk/docs/install):

```bash
mkdir -p scin_data
gsutil -m cp -r gs://dx-scin-public-data/dataset scin_data/
```

### Prepare training splits

```bash
cd backend
python prepare_scin_data.py --scin_root ../scin_data --target_dir data_scin
# Optional flags: --max_classes 10  --symlink
```

### Train

```bash
python train.py --data_dir data_scin
# Output: backend/models/pt_skin_model.pth
```

### Export to ONNX (optional)

```bash
python export_to_onnx.py --model models/pt_skin_model.pth --output models/skin_model.onnx
```

---

## Dataset — SCIN (Google & Stanford, 2024)

**Source:** [google/scin on HuggingFace](https://huggingface.co/datasets/google/scin)

- ~5,000 cases, ~10,000 images
- Real smartphone photos submitted by volunteers
- Labeled by board-certified dermatologists
- Diverse skin tones (Fitzpatrick I–VI)
- License: CC BY-NC-4.0 (non-commercial research)

**8 classes:**

| Class | Description |
|---|---|
| `ACNE` | Acne vulgaris, rosacea |
| `GROWTH_OR_MOLE` | Moles, lesions, suspicious growths |
| `HAIR_LOSS` | Alopecia and related conditions |
| `LOOKS_HEALTHY` | No apparent condition |
| `NAIL_PROBLEM` | Fungal infections, nail disease |
| `OTHER_HAIR_PROBLEM` | Other hair/scalp conditions |
| `PIGMENTARY_PROBLEM` | Vitiligo, hyperpigmentation |
| `RASH` | Allergic reactions, eczema, dermatitis, psoriasis |

---

## Model performance

Evaluated on the SCIN test set (7,408 images, 926 per class):

| Class | Precision | Recall | F1-Score |
|---|---|---|---|
| ACNE | 0.9872 | 1.0000 | 0.9936 |
| GROWTH_OR_MOLE | 0.9914 | 1.0000 | 0.9957 |
| HAIR_LOSS | 0.9968 | 1.0000 | 0.9984 |
| LOOKS_HEALTHY | 0.9572 | 0.9903 | 0.9735 |
| NAIL_PROBLEM | 0.9968 | 1.0000 | 0.9984 |
| OTHER_HAIR_PROBLEM | 1.0000 | 1.0000 | 1.0000 |
| PIGMENTARY_PROBLEM | 0.9989 | 1.0000 | 0.9995 |
| RASH | 0.9896 | 0.9266 | 0.9571 |
| **Overall accuracy** | | | **0.9896** |
| Macro avg | 0.9897 | 0.9896 | 0.9895 |

> **Training environment:** Google Colab Pro with an NVIDIA A100 GPU.

> **Dataset size note:** SCIN is a relatively small dataset (~5,000 cases, 8 classes). While our model achieves strong results on this data, performance on real-world images may vary. Future work aims to train on larger, more diverse datasets to expand coverage to a wider range of skin diseases and improve generalization across skin tones and conditions.

---

## Repository layout

```
Skindex-HackRUF25/
├── backend/
│   ├── app.py                  # Flask API -- inference + auth wiring
│   ├── auth.py                 # Auth blueprint -- User & Scan models, JWT, all endpoints
│   ├── prepare_scin_data.py    # CSVs + images -> train/val/test folders
│   ├── train.py
│   ├── evaluate.py
│   ├── export_to_onnx.py
│   ├── models/
│   │   └── pt_skin_model.pth   # Trained EfficientNet-B0 weights (committed, 18 MB)
│   ├── instance/               # SQLite DB at runtime (gitignored)
│   └── data_scin/              # Prepared splits (gitignored)
├── frontend-vite/
│   └── src/
│       ├── components/
│       │   ├── home.jsx         # Landing page
│       │   ├── ImageUpload.jsx  # Scan upload + context form + results
│       │   ├── AIAssistant.jsx  # AI chat assistant interface
│       │   ├── Profile.jsx      # Demographics + scan history with delete
│       │   ├── Login.jsx        # Register / sign-in form
│       │   └── ComponentLibrary.jsx  # Shared UI component library
│       └── context/
│           └── AuthContext.jsx  # JWT auth state + API helpers
├── requirements.txt
├── requirements-training.txt
└── scin_demo.ipynb
```

---

## Notes

- **Database is local per machine** -- `backend/instance/users.db` is not committed or shared. The demo user (`demo@dermai.com` / `test1234`) is auto-created on each machine's first backend boot. To share accounts across machines, set the `DATABASE_URL` environment variable to a hosted PostgreSQL connection string (e.g. Supabase, Railway, Render).
- **Model weights** -- `pt_skin_model.pth` (18 MB, EfficientNet-B0 trained on SCIN) is committed to this repo. `skin_model.onnx` remains gitignored; generate it with `export_to_onnx.py` if needed.
- **TensorFlow is optional** -- commented out in `requirements.txt`; only PyTorch and ONNX inference paths are active by default.

---

## Disclaimer

Models are for **research/demo** use only, not a medical device. Always consult a qualified clinician.
