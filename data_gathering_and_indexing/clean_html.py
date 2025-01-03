import os
from bs4 import BeautifulSoup, Comment
import html2text
import hashlib
from collections import defaultdict

def get_file_hash(content):
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def main():
    html_dir = 'html_pages'
    output_dir = 'markdown_pages'

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    content_hashes = defaultdict(list)
    
    for filename in os.listdir(html_dir):
        if filename.endswith('.html'):
            html_path = os.path.join(html_dir, filename)
            with open(html_path, 'r', encoding='utf-8') as file:
                html_content = file.read()

            soup = BeautifulSoup(html_content, 'lxml')

            if soup.head:
                soup.head.decompose()

            for script_or_style in soup(['script', 'style']):
                script_or_style.decompose()

            if soup.header:
                soup.header.decompose()
            if soup.footer:
                footer = soup.footer
                for sibling in list(footer.find_next_siblings()):
                    sibling.decompose()
                footer.decompose()

            for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
                comment.extract()

            for selector in [
                {"class": "widg_searchbar", "data-init": "searchbar"},
                {"class": "widg_follow_us", "data-init": "follow_us"},
                {"class": "widg_so_me_share", "data-init": "so_me_share"},
                {"aria-hidden": "false", "aria-label": "Datenschutz und Cookies", "class": "cookiealert", "role": "alert"}
            ]:
                for div in soup.find_all("div", selector):
                    div.decompose()

            remove_empty_tags(soup)

            html_to_md = html2text.HTML2Text()
            html_to_md.body_width = 0

            markdown_text = html_to_md.handle(str(soup))
            
            content_hash = get_file_hash(markdown_text)
            output_filename = os.path.splitext(filename)[0] + '.md'
            
            content_hashes[content_hash].append((output_filename, html_path))
            
            if len(content_hashes[content_hash]) == 1:
                output_path = os.path.join(output_dir, output_filename)
                with open(output_path, 'w', encoding='utf-8') as output_file:
                    output_file.write(markdown_text)
                print(f"Saved new file: {output_filename}")

    print("\nDuplicate Content Report:")
    print("-" * 50)
    duplicates_found = False
    for content_hash, file_pairs in content_hashes.items():
        if len(file_pairs) > 1:
            duplicates_found = True
            print(f"\nFound {len(file_pairs)} files with identical content:")
            print(f"Kept: {file_pairs[0][0]} and its HTML source")
            print("Removed duplicates:")
            for duplicate_md, duplicate_html in file_pairs[1:]:
                print(f"- {duplicate_md} and its HTML source")
                os.remove(duplicate_html)
    
    if not duplicates_found:
        print("No duplicates found.")
    
    print("\nProcessing complete.")

def remove_empty_tags(soup):
    for element in soup.find_all():
        if element.name == 'a' and 'href' in element.attrs and element['href'].startswith('https://'):
            element.attrs = {'href': element['href']} 
        elif element.name == 'a' and 'href' in element.attrs and element['href'].startswith('geomailto:'):
            element.decompose()
        elif element.name == 'button' and 'onclick' in element.attrs and element['onclick'].startswith('https://'):
            element.attrs = {'onclick': element['onclick']}
        elif not element.text.strip():
            element.decompose()
        else:
            element.attrs = {}

if __name__ == "__main__":
    main()
