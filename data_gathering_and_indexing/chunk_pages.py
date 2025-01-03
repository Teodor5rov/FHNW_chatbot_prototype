import os
import re
from tiktoken import get_encoding

def main():
    input_dir = 'markdown_pages'
    output_dir = 'chunked_pages'

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    tokenizer = get_encoding("o200k_base")

    total_chunks = 0
    total_token_count = 0
    chunks_under_400 = 0
    chunks_between_400_600 = 0
    chunks_over_600 = 0
    chunks_under_20 = 0
    top_10_largest_chunks = []
    top_10_smallest_chunks = []
    file_chunk_counts = {}

    for filename in os.listdir(input_dir):
        if filename.endswith('.md'):
            file_path = os.path.join(input_dir, filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                markdown_content = file.read()

            blocks = parse_markdown(markdown_content)

            chunks = process_blocks(blocks, tokenizer)

            num_chunks = len(chunks)
            total_chunks += num_chunks
            total_token_count += sum(chunk['token_count'] for chunk in chunks)
            chunks_under_400 += sum(1 for chunk in chunks if chunk['token_count'] < 400)
            chunks_between_400_600 += sum(1 for chunk in chunks if 400 <= chunk['token_count'] < 600)
            chunks_over_600 += sum(1 for chunk in chunks if chunk['token_count'] >= 600)
            chunks_under_20 += sum(1 for chunk in chunks if chunk['token_count'] < 20)

            for idx, chunk in enumerate(chunks):
                chunk_size = chunk['token_count']
                top_10_largest_chunks.append((chunk_size, filename, idx + 1))
                top_10_largest_chunks = sorted(top_10_largest_chunks, reverse=True)[:10]
                top_10_smallest_chunks.append((chunk_size, filename, idx + 1))
                top_10_smallest_chunks = sorted(top_10_smallest_chunks)[:10]

            file_chunk_counts[filename] = num_chunks
            save_chunks(chunks, filename, output_dir)

            print(f"Processed {filename} into {num_chunks} chunks.")

    average_chunk_size = total_token_count / total_chunks if total_chunks > 0 else 0
    top_10_files = sorted(file_chunk_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    print("\nMarkdown chunking complete.")
    print(f"Total number of chunks created: {total_chunks}")
    print(f"Average chunk size: {average_chunk_size:.2f} tokens")
    print(f"Number of chunks under 400 tokens: {chunks_under_400}")
    print(f"Number of chunks between 400 and 600 tokens: {chunks_between_400_600}")
    print(f"Number of chunks over 600 tokens: {chunks_over_600}")
    print(f"Number of chunks with less than 20 tokens: {chunks_under_20}")

    print("\nTop 10 largest chunks:")
    for chunk_size, file, chunk_index in top_10_largest_chunks:
        print(f"{file} - Chunk {chunk_index}: {chunk_size} tokens")

    print("\nTop 10 smallest chunks:")
    for chunk_size, file, chunk_index in top_10_smallest_chunks:
        print(f"{file} - Chunk {chunk_index}: {chunk_size} tokens")

    print("\nTop 10 files with the most chunks:")
    for file, count in top_10_files:
        print(f"{file}: {count} chunks")

def parse_markdown(content):
    lines = content.split('\n')
    blocks = []
    current_paragraph = []

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped_line = line.strip()
        if re.match(r'#{1,6}\s', stripped_line):
            if current_paragraph:
                blocks.append({
                    'type': 'paragraph',
                    'content': '\n'.join(current_paragraph)
                })
                current_paragraph = []
            heading_level = len(stripped_line) - len(stripped_line.lstrip('#'))
            blocks.append({
                'type': 'heading',
                'level': heading_level,
                'content': line
            })
        elif stripped_line == '':
            if current_paragraph:
                blocks.append({
                    'type': 'paragraph',
                    'content': '\n'.join(current_paragraph)
                })
                current_paragraph = []
            empty_lines = []
            while i < len(lines) and lines[i].strip() == '':
                empty_lines.append(lines[i])
                i += 1
            i -= 1
            blocks.append({
                'type': 'empty_lines',
                'content': '\n'.join(empty_lines)
            })
        elif stripped_line.startswith('*'):
            if current_paragraph:
                blocks.append({
                    'type': 'paragraph',
                    'content': '\n'.join(current_paragraph)
                })
                current_paragraph = []
            blocks.append({
                'type': 'asterisk_item',
                'content': line
            })
        else:
            current_paragraph.append(line)
        i += 1

    if current_paragraph:
        blocks.append({
            'type': 'paragraph',
            'content': '\n'.join(current_paragraph)
        })

    return blocks

def process_blocks(blocks, tokenizer):
    chunks = []
    i = 0
    n = len(blocks)

    while i < n:
        chunk_blocks, next_i = process_chunk(blocks, i, tokenizer)
        chunk_content = ''.join([b['content'] + '\n' for b in chunk_blocks])
        chunk_token_count = sum(len(tokenizer.encode(b['content'])) for b in chunk_blocks)
        if chunk_token_count > 10:
            chunks.append({
                'content': chunk_content,
                'token_count': chunk_token_count
            })
        i = next_i

    return chunks

def process_chunk(blocks, start_index, tokenizer):
    current_chunk = []
    current_token_count = 0
    i = start_index
    n = len(blocks)
    level = 1

    levels = [
        {'threshold': 200, 'stopping_levels': [1, 2], 'stopping_newlines': None, 'stopping_characters': None, 'next_level_threshold': 300},
        {'threshold': 300, 'stopping_levels': [1, 2, 3], 'stopping_newlines': None, 'stopping_characters': None, 'next_level_threshold': 400},
        {'threshold': 400, 'stopping_levels': [1, 2, 3, 4], 'stopping_newlines': 3, 'stopping_characters': None, 'next_level_threshold': 500},
        {'threshold': 500, 'stopping_levels': [1, 2, 3, 4], 'stopping_newlines': 2, 'stopping_characters': None, 'next_level_threshold': 600},
        {'threshold': 600, 'stopping_levels': [1, 2, 3, 4], 'stopping_newlines': 2, 'stopping_characters': ['*'], 'next_level_threshold': 800},
        {'threshold': 800, 'stopping_levels': [1, 2, 3, 4], 'stopping_newlines': 1, 'stopping_characters': ['*'], 'next_level_threshold': None}
    ]

    min_tokens = 200

    while i < n:
        block = blocks[i]
        block_content = block['content']
        block_token_count = len(tokenizer.encode(block_content))
        current_chunk.append(block)
        current_token_count += block_token_count
        should_end_chunk = False
        current_level = levels[min(level - 1, len(levels) - 1)]
        stopping_levels = current_level['stopping_levels']
        stopping_newlines = current_level['stopping_newlines']
        stopping_characters = current_level.get('stopping_characters')
        next_level_threshold = current_level['next_level_threshold']

        if current_token_count >= min_tokens:
            if is_stopping_point(block, stopping_levels, stopping_newlines, stopping_characters):
                chunk_token_count = current_token_count - block_token_count
                if chunk_token_count >= min_tokens:
                    should_end_chunk = True

            if next_level_threshold and current_token_count >= next_level_threshold:
                current_chunk = []
                current_token_count = 0
                i = start_index
                level += 1
                continue

            elif should_end_chunk:
                chunk_blocks = current_chunk[:-1]
                next_start_index = i
                return chunk_blocks, next_start_index

        i += 1

    return current_chunk, n

def is_stopping_point(block, stopping_levels, stopping_newlines, stopping_characters):
    if block['type'] == 'heading' and block['level'] in stopping_levels:
        return True
    if stopping_newlines is not None and block['type'] == 'empty_lines':
        num_newlines = block['content'].count('\n') + 1
        if num_newlines >= stopping_newlines:
            return True
    if stopping_characters is not None and block['type'] == 'asterisk_item':
        return True
    return False

def save_chunks(chunks, original_filename, output_dir):
    base_filename = os.path.splitext(original_filename)[0]
    file_output_dir = os.path.join(output_dir, base_filename)

    if not os.path.exists(file_output_dir):
        os.makedirs(file_output_dir)

    for idx, chunk in enumerate(chunks):
        chunk_filename = f"chunk_{idx+1}.md"
        chunk_path = os.path.join(file_output_dir, chunk_filename)
        cleaned_content = remove_extra_empty_lines(chunk['content'])
        with open(chunk_path, 'w', encoding='utf-8') as chunk_file:
            chunk_file.write(cleaned_content)

def remove_extra_empty_lines(text):
    return re.sub(r'(\n\s*){2,}', '\n\n', text)

if __name__ == "__main__":
    main()
