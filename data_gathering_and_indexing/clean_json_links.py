import os
import json
import re
from collections import Counter

script_dir = os.path.dirname(os.path.abspath(__file__))
json_dir = os.path.join(script_dir, 'json_files')
html_dir = os.path.join(script_dir, 'html_pages')
pdf_dir = os.path.join(script_dir, 'downloaded_files')

if not os.path.isdir(json_dir):
    print("The json_files directory does not exist. Please check the path.")
    exit(1)

if not os.path.isdir(html_dir):
    print("The html_files directory does not exist. Please check the path.")
    exit(1)

if not os.path.isdir(pdf_dir):
    print("The downloaded_files directory does not exist. Please check the path.")
    exit(1)

def filter_and_validate_links(links):
    filtered_links = []
    for link in links:
        if re.match(r'^[A-Za-z]', link):
            if link.endswith('.html'):
                html_path = os.path.join(html_dir, link)
                if os.path.isfile(html_path):
                    filtered_links.append(link)
                else:
                    base_name = os.path.splitext(link)[0]
                    for file in os.listdir(pdf_dir):
                        if file.startswith(base_name + '.'):
                            filtered_links.append(file)
                            break
            elif link.endswith('.pdf'):
                pdf_path = os.path.join(pdf_dir, link)
                if os.path.isfile(pdf_path):
                    filtered_links.append(link)
    return filtered_links

link_counter = Counter()
total_files = 0

for file in os.listdir(json_dir):
    if file.endswith('.json'):
        json_path = os.path.join(json_dir, file)
        with open(json_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                total_files += 1
                if "links" in data and isinstance(data["links"], list):
                    unique_links = set(data["links"])
                    link_counter.update(unique_links)
            except json.JSONDecodeError:
                print(f"Error decoding JSON in file: {json_path}")

threshold = total_files * 0.15
common_links = {link for link, count in link_counter.items() if count > threshold}

print(common_links)

for file in os.listdir(json_dir):
    if file.endswith('.json'):
        json_path = os.path.join(json_dir, file)
        with open(json_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                if "links" in data and isinstance(data["links"], list) and "file_name" in data:
                    unique_links = set(data["links"])
                    unique_links.discard(data["file_name"])
                    if data["file_name"] in common_links:
                        validated_links = filter_and_validate_links(unique_links)
                    else:
                        validated_links = filter_and_validate_links(unique_links - common_links)
                    data["links"] = sorted(validated_links)
                with open(json_path, 'w', encoding='utf-8') as f_out:
                    json.dump(data, f_out, ensure_ascii=False, indent=4)
            except json.JSONDecodeError:
                print(f"Error decoding JSON in file: {json_path}")

print(f"Duplicates removed, 'links' filtered, validated for existence, common links conditionally removed (threshold: {threshold} files), and sorted alphabetically in all JSON files.")
