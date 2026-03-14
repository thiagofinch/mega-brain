# Example 01: Ingest a PDF Course

Demonstrates how to extract text from a PDF and route it to the knowledge inbox.

## Prerequisites

```bash
pip install pymupdf
```

## Usage

### Basic extraction (returns text)

```python
from core.intelligence.pipeline.pdf_extractor import extract_pdf

# Extract all pages, get text back
text = extract_pdf("path/to/course-module-1.pdf")
print(f"Extracted {len(text)} chars from PDF")
```

### Extract and save to file

```python
from core.intelligence.pipeline.pdf_extractor import extract_pdf

# Extract and write to a specific output path
text = extract_pdf(
    pdf_path="path/to/course-module-1.pdf",
    output_path="output/course-module-1.txt"
)
# File created at output/course-module-1.txt
```

### Extract and route to knowledge inbox (recommended)

```python
from core.intelligence.pipeline.pdf_extractor import extract_pdf_to_inbox

# Extract and route to the expert's inbox folder
output_path = extract_pdf_to_inbox(
    pdf_path="path/to/course-module-1.pdf",
    source_tag="alex-hormozi"
)
print(f"Extracted to: {output_path}")
# Output: knowledge/external/inbox/alex-hormozi/course-module-1.txt
```

### CLI usage

```bash
# Print extracted text to stdout
python -m core.intelligence.pipeline.pdf_extractor path/to/file.pdf

# Extract and save to file
python -m core.intelligence.pipeline.pdf_extractor path/to/file.pdf output.txt
```

## What Happens

1. PyMuPDF opens the PDF and iterates all pages
2. Text is extracted from each page with separator markers (`--- Page N ---`)
3. Empty pages are skipped
4. When using `extract_pdf_to_inbox`:
   - File is saved to `knowledge/external/inbox/{source_tag}/{stem}.txt`
   - Parent directories are created automatically
   - File is ready for MCE pipeline processing

## Next Steps

After ingesting, use the pipeline to process the file:

- Run `/ingest` to register the file in the pipeline
- Run `/process-jarvis` to extract DNA layers (philosophies, frameworks, heuristics, etc.)

## Source

Module: `core/intelligence/pipeline/pdf_extractor.py`

Key functions:
- `extract_pdf(pdf_path, output_path=None) -> str`
- `extract_pdf_to_inbox(pdf_path, source_tag) -> Path`
