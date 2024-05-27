import os
import tomllib

def parse_toml(file_path):
    # check if file exists
    file_exists = os.path.exists(file_path)
    file_is_file = os.path.isfile(file_path)
    is_toml = file_path.endswith(".toml")

    valid_path = file_exists and file_is_file and is_toml
    if not valid_path:
        if not file_exists:
            print(f"File {file_path} does not exist")
        if not file_is_file:
            print(f"File {file_path} is not a file")
        if not is_toml:
            print(f"File {file_path} is not a TOML file")
        return None
    
    # actually parse toml
    with open(file_path, "rb") as f:
        try:
            return tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            print(f"Error decoding TOML: {e}")
            return None
    
if __name__ == "__main__":
    print(parse_toml("test.toml"))


