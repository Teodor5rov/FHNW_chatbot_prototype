import os

script_dir = os.path.dirname(os.path.abspath(__file__))

html_dir = os.path.join(script_dir, 'html_pages')
json_dir = os.path.join(script_dir, 'json_files')

if not os.path.isdir(html_dir) or not os.path.isdir(json_dir):
    print("One of the directories does not exist. Please check the paths.")
    exit(1)

html_files = {os.path.splitext(file)[0] for file in os.listdir(html_dir) if file.endswith('.html')}
json_files = {os.path.splitext(file)[0] for file in os.listdir(json_dir) if file.endswith('.json')}

common_files = html_files & json_files

for file in os.listdir(json_dir):
    if file.endswith('.json'):
        json_base = os.path.splitext(file)[0]
        if json_base not in common_files:
            json_path = os.path.join(json_dir, file)
            os.remove(json_path)
            print(f"Deleted JSON file without matching HTML: {json_path}")
    else:
        non_json_path = os.path.join(json_dir, file)
        os.remove(non_json_path)
        print(f"Deleted non-JSON file from json_files: {non_json_path}")

for file in os.listdir(html_dir):
    if file.endswith('.html'):
        html_base = os.path.splitext(file)[0]
        if html_base not in common_files:
            html_path = os.path.join(html_dir, file)
            os.remove(html_path)
            print(f"Deleted HTML file without matching JSON: {html_path}")
    else:
        non_html_path = os.path.join(html_dir, file)
        os.remove(non_html_path)
        print(f"Deleted non-HTML file from html_pages: {non_html_path}")

print("Cleanup complete.")
