from pathlib import Path


def get_unique_filename(directory: Path, filename: str) -> Path:
    """Get a unique filename by appending the next available number if the file already exists.

    Args:
        directory: The directory where the file should be created
        filename: The base filename (e.g., "physics_model.py")

    Returns:
        A unique Path that doesn't exist in the directory: eg: physics_model (1).py
    """
    base_path = directory / filename

    if not base_path.exists():
        return base_path

    name = base_path.stem
    extension = base_path.suffix

    # Find the next available number
    counter = 1
    while True:
        new_filename = f"{name} ({counter}){extension}"
        new_path = directory / new_filename
        if not new_path.exists():
            return new_path
        counter += 1
