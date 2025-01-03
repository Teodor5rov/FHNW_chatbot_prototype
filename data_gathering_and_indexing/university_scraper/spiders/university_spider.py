import scrapy
from urllib.parse import urlparse
import os
import json
import hashlib
from scrapy.linkextractors import LinkExtractor

class UniversitySpider(scrapy.Spider):
    name = "university_spider"
    allowed_domains = ["fhnw.ch", "www.fhnw.ch"]
    start_urls = ["https://www.fhnw.ch"]

    custom_settings = {
        'LOG_LEVEL': 'INFO',
        'DEPTH_LIMIT': 15,
        'DOWNLOAD_DELAY': 0.4,
        'ROBOTSTXT_OBEY': True,
    }

    def __init__(self, *args, **kwargs):
        super(UniversitySpider, self).__init__(*args, **kwargs)
        for directory in ['downloaded_files', 'html_pages', 'json_files']:
            os.makedirs(directory, exist_ok=True)

    def parse(self, response):
        page_url = response.url
        content_type = response.headers.get('Content-Type', b'').decode('utf-8').lower()

        if 'text/html' in content_type:
            page_content = response.text
            filename = self.get_filename_from_url(page_url, '.html')
            filepath = os.path.join('html_pages', filename)
            if not os.path.exists(filepath):
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(page_content)
                yield {'file': filepath, 'url': page_url, 'type': 'html'}

            link_extractor = LinkExtractor(
                allow_domains=self.allowed_domains,
                deny_extensions=[]
            )
            links = [link.url for link in link_extractor.extract_links(response)]
            links = [link for link in links if self.is_valid_link(link)]
            link_filenames = [self.get_filename_from_url(link, '.html') for link in links]
            json_data = {
                'url_path': urlparse(page_url).path,
                'file_name': filename,
                'links': link_filenames,
            }
            json_filename = f"{os.path.splitext(filename)[0]}.json"
            json_filepath = os.path.join('json_files', json_filename)
            with open(json_filepath, 'w', encoding='utf-8') as json_file:
                json.dump(json_data, json_file, ensure_ascii=False, indent=2)

            for link in links:
                yield scrapy.Request(link, callback=self.parse)
        else:
            self.save_file(response, 'downloaded_files')

    def save_file(self, response, folder_name):
        filename = self.get_filename_from_url(response.url)
        filepath = os.path.join(folder_name, filename)
        if not os.path.exists(filepath):
            with open(filepath, 'wb') as f:
                f.write(response.body)
            self.logger.info(f"Saved file {filepath}")

    def get_filename_from_url(self, url, default_extension='.html'):
        known_extensions = [
            '.html', '.htm', '.pdf', '.doc', '.docx', '.xls', '.xlsx',
            '.jpg', '.jpeg', '.png', '.gif', '.txt', '.csv', '.json',
            '.xml', '.zip', '.tar', '.gz', '.rar', '.mp3', '.mp4',
            '.avi', '.mov', '.css', '.js', '.php', '.asp', '.aspx',
            '.jsp', '.py', '.rb', '.pl', '.cgi', '.svg', '.woff', '.woff2',
            '.ttf', '.otf', '.eot', '.ico', '.bmp', '.webp'
        ]

        parsed_url = urlparse(url)
        path = parsed_url.path
        query = parsed_url.query
        _, ext = os.path.splitext(path)
        ext = ext.lower()
        extension = ext if ext in known_extensions else default_extension
        if not path or path == '/':
            filename = 'index'
        else:
            filename = path.lstrip('/').replace('/', '_')
            filename = os.path.splitext(filename)[0]
        if query:
            filename += '_' + query.replace('=', '_').replace('&', '_')
        filename = self.clean_filename(filename)
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()[:8]
        max_base_length = 200 - len(extension) - 9
        if len(filename) > max_base_length:
            filename = filename[:max_base_length]
        filename = f"{filename}_{url_hash}{extension}"
        return filename

    def clean_filename(self, filename):
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return '_'.join(filename.split())

    def is_valid_link(self, url):
        parsed_uri = urlparse(url)
        return (
            parsed_uri.netloc in self.allowed_domains and
            parsed_uri.scheme in ['http', 'https'] and
            not url.startswith(('mailto:', 'tel:'))
        )
