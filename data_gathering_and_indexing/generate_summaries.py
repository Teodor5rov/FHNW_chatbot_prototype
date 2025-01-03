import os
import json
from dotenv import load_dotenv
from openai import OpenAI

def main():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    markdown_dir = 'markdown_pages'
    json_dir = 'json_files'
    json_output_dir = 'json_files_with_summaries'

    if not os.path.exists(json_output_dir):
        os.makedirs(json_output_dir)

    for markdown_filename in os.listdir(markdown_dir):
        if markdown_filename.endswith('.md'):
            markdown_path = os.path.join(markdown_dir, markdown_filename)

            json_filename = os.path.splitext(markdown_filename)[0] + '.json'
            json_path = os.path.join(json_dir, json_filename)

            if not os.path.exists(json_path):
                continue

            with open(markdown_path, 'r', encoding='utf-8') as f:
                content = f.read()

            prompt = """Extract a dense, very short, concise and information-rich summary. Follow these rules:
                        Omit articles (a, an, the), transitions
                        Maintain factual accuracy - include ONLY information present in source
                        Generate single-line plain text without any special characters, formatting or newlines
                        Do not include dates or deadline times as they might become outdated
                        Maximize information density
                        Include specific terminology"""

            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": content}
            ]

            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    temperature=0.1
                )
                summary = response.choices[0].message.content.strip()
            except Exception as e:
                print(f"Error processing {markdown_filename}: {e}")
                continue

            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            data['summary'] = summary
            data['file_name'] = markdown_filename

            if 'links' in data:
                data['links'] = [
                    link.replace('.html', '.md') if link.endswith('.html') else link
                    for link in data['links']
                ]

            json_output_path = os.path.join(json_output_dir, json_filename)
            with open(json_output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

            print(f"Processed {markdown_filename}, summary added to {json_filename}, links updated.")

if __name__ == "__main__":
    main()
