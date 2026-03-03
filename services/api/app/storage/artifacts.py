import os
from pathlib import Path
from fastapi import UploadFile

def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

def save_model_artifact(
    artifacts_root: str,
    model_id: str,
    version: int,
    file: UploadFile,
) -> str:
    root = Path(artifacts_root)
    version_dir = root / model_id / f"v{version}"
    ensure_dir(version_dir)

    # Keep name stable for simplicity
    filename = "model.pkl"
    if file.filename and file.filename.lower().endswith(".pkl"):
        filename = "model.pkl"
    elif file.filename:
        # If someone uploads a non-pkl name, still store as model.pkl for V1
        filename = "model.pkl"

    dest = version_dir / filename

    # Write file stream to disk
    with open(dest, "wb") as f:
        while True:
            chunk = file.file.read(1024 * 1024)  # 1MB chunks
            if not chunk:
                break
            f.write(chunk)

    return str(dest)