import os
def ensure_dir(directory):
    """ Ensure that a directory exists on the filesystem. If the directory does not exist, it is created.

    Parameters:
    directory (str): The path of the directory to check or create. 
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created directory: {directory}")
    else:
        print(f"Directory already exists: {directory}")


def delete_file(file_path):
    """Deletes a file from the filesystem if it exists.

    Parameters:
    file_path (str): The path to the file that should be deleted.
    """
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"Deleted file: {file_path}")
    else:
        print(f"No file found at: {file_path}, nothing to delete.")