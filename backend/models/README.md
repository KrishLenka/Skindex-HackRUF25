# Models Directory

This directory stores trained model files.

## Files Created During Training

After running `python train.py`, you'll find:

- **`pt_skin_model.pth`** - Best model (used by Flask API)
- **`pt_skin_model_final.pth`** - Final epoch model
- **`model_config.json`** - Model configuration and class names

## Note on Git

⚠️ Model files (`.pth`, `.h5`, `.onnx`) are **NOT tracked in git** because they're too large.

### To Transfer Models Between Computers

**Option 1: Manual Copy**
```bash
scp backend/models/pt_skin_model.pth user@other-computer:~/MTC-Hackathon/backend/models/
```

**Option 2: Cloud Storage**
Upload to Google Drive, Dropbox, etc., then download on the other computer.

**Option 3: Git LFS** (for teams)
```bash
git lfs track "*.pth"
git add .gitattributes
```

## Starting Fresh

If pulling the repo on a new computer, this directory will be empty.
Just run training and the models will be created here automatically.
