import shutil
import subprocess
from pathlib import Path


def open_ide(ide_executable: str, folder: Path) -> None:
    """
    Tries to open the IDE using the provided executable path.

    :param ide_executable: The executable path of the IDE.
    :return: None
    """
    try:
        executable = ide_executable.split()[0]
        if shutil.which(executable) is not None:
            subprocess.run(
                ide_executable.split() + [str(folder)], start_new_session=True
            )
        else:
            print(
                f"Error: Could not find executable '{executable}' in the system path."
            )
    except Exception as e:
        print(f"Error: Failed to open IDE. {str(e)}")
