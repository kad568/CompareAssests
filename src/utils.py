from pathlib import Path, PurePath

PATH_TO_SRC = Path(__file__).parent.resolve()

PATH_TO_HOME = str(PurePath(f"{PATH_TO_SRC}/.."))