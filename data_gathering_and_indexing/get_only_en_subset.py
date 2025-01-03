import os
import json

json_dir = 'json_files'
downloaded_files_dir = 'downloaded_files'

all_json_files = [f for f in os.listdir(json_dir) if f.endswith('.json')]

en_json_files = set(f for f in all_json_files if f.startswith('en'))

files_to_keep = set()
linked_to_any_file = set()
non_json_links = set()

files_to_keep.update(en_json_files)

for filename in en_json_files:
    filepath = os.path.join(json_dir, filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)
            linked_files = data.get('links', [])
            for linked_file in linked_files:
                if linked_file.endswith('.html'):
                    linked_json_filename = os.path.splitext(linked_file)[0] + '.json'
                    files_to_keep.add(linked_json_filename)
                    linked_to_any_file.add(linked_json_filename)
                else:
                    non_json_links.add(linked_file)
            if linked_files:
                linked_to_any_file.add(filename)
    except Exception as e:
        print(f"Error reading {filepath}: {e}")

for filename in list(files_to_keep):
    if filename not in linked_to_any_file and filename not in en_json_files:
        files_to_keep.remove(filename)

for filename in all_json_files:
    if filename not in files_to_keep:
        filepath = os.path.join(json_dir, filename)
        try:
            os.remove(filepath)
            print(f"Deleted {filepath}")
        except Exception as e:
            print(f"Error deleting {filepath}: {e}")

for filename in os.listdir(downloaded_files_dir):
    if filename not in non_json_links:
        filepath = os.path.join(downloaded_files_dir, filename)
        try:
            os.remove(filepath)
            print(f"Deleted {filepath} from downloaded_files")
        except Exception as e:
            print(f"Error deleting {filepath}: {e}")

print("Cleanup complete.")
