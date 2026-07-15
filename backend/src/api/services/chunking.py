import re
from typing import List, Dict, Optional

# Regex for detecting legal headers (e.g., "ARTICLE I", "Section 2.1", "(a)")
SECTION_REGEX = re.compile(r"^\s*(?:ARTICLE|SECTION)\s+[IVXLCDM\d]+\b", re.IGNORECASE)
CLAUSE_REGEX = re.compile(r"^\s*(?:\d+\.\d+|[a-z]\)|\([a-z]\))\s+")

def recursive_split(text: str, max_size: int, overlap: int) -> List[str]:
    """
    Recursively splits oversized text using progressively smaller boundaries.
    """
    if len(text) <= max_size:
        return [text]

    # Boundaries in order of preference
    separators = ["\n\n", "\n", ". ", " "]
    
    for sep in separators:
        splits = text.split(sep)
        if len(splits) > 1:
            chunks = []
            current_chunk = ""
            
            for part in splits:
                part = part + sep if sep != " " else part + sep
                if len(current_chunk) + len(part) <= max_size:
                    current_chunk += part
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = part
            
            if current_chunk:
                chunks.append(current_chunk.strip())
            
            # If this separator successfully brought chunks down to size, return them
            # (Note: Overlap is tricky in pure recursive split without advanced logic. 
            # For simplicity, we just return the chunks here. LangChain handles overlap better.)
            if all(len(c) <= max_size for c in chunks):
                return chunks

    # Ultimate fallback: brutal slice if no separators worked (very rare)
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_size
        chunks.append(text[start:end])
        start += (max_size - overlap)
    return chunks

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[Dict[str, Optional[str]]]:
    """
    Structure-aware chunking.
    Returns: [{"text_content": "...", "section": "ARTICLE I", "clause": "1.1"}]
    """
    if not text:
        return []
        
    lines = text.split('\n')
    structured_blocks = []
    
    current_section = None
    current_clause = None
    current_block = []
    
    def flush_block():
        if current_block:
            block_text = "\n".join(current_block).strip()
            if block_text:
                structured_blocks.append({
                    "text_content": block_text,
                    "section": current_section,
                    "clause": current_clause
                })
            current_block.clear()

    for line in lines:
        is_header = False
        
        if SECTION_REGEX.match(line):
            flush_block()
            current_section = line.strip()
            current_clause = None
            is_header = True
        elif CLAUSE_REGEX.match(line):
            flush_block()
            current_clause = line.strip()
            is_header = True
            
        current_block.append(line)
        
        # If it was a header, we immediately flush it so the header is its own small block 
        # (or attached to the top of the next block. We append it to current_block above).
        # Actually, it's better to just leave it in the block so the clause text includes the header.

    flush_block()
    
    # Now that we have structured blocks, apply recursive splitting ONLY to oversized blocks
    final_chunks = []
    for block in structured_blocks:
        block_text = block["text_content"]
        
        if len(block_text) <= chunk_size:
            final_chunks.append(block)
        else:
            # It's an oversized clause. Recursive split it.
            sub_chunks = recursive_split(block_text, chunk_size, overlap)
            for sub_text in sub_chunks:
                final_chunks.append({
                    "text_content": sub_text,
                    "section": block["section"],
                    "clause": block["clause"]
                })
                
    return final_chunks
