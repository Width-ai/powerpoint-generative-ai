# PowerPoint Generation Service

A standalone service for generating PowerPoint presentations from retreat proposal documents.

## Overview

This service converts markdown or Word document proposals into professionally designed PowerPoint presentations optimized for Zoom presentations. It includes AI-powered content reduction, quote generation, and follows specific design and emotional sequencing requirements.

## Service Architecture

This is designed as a **standalone service** that can be:
- Imported and used in any Python project
- Integrated into web applications (Flask, FastAPI, etc.)
- Called from automation workflows (n8n, Make.com, etc.)
- Used as a CLI tool

## Installation

```bash
pip install -r ppt_gen/requirements.txt
```

## Dependencies

All dependencies are listed in `requirements.txt`:
- `groq` - AI model API
- `python-pptx` - PowerPoint generation
- `python-docx` - Word document parsing
- `lxml` - XML processing

## Environment Variables

- `GROQ_API_KEY` - Required. Your Groq API key for AI model calls.

## Usage

### Basic Usage

```python
from ppt_gen import PPTService

# Initialize service (reads GROQ_API_KEY from environment)
service = PPTService()

# Generate from markdown text
pptx_bytes = service.generate_from_markdown(markdown_text, output_path="deck.pptx")

# Generate from file (auto-detects .md or .docx)
pptx_bytes = service.generate_from_file("proposal.md", output_path="deck.pptx")
```

### With Custom API Key

```python
from ppt_gen import PPTService

service = PPTService(groq_api_key="your-api-key-here")
pptx_bytes = service.generate_from_file("proposal.docx")
```

### CLI Usage

```bash
python -m ppt_gen.ppt_service proposal.md output.pptx
```

## Service API

### PPTService Class

Main service class that orchestrates the PowerPoint generation pipeline.

#### Methods

- `generate_from_markdown(markdown: str, output_path: Optional[str] = None) -> bytes`
  - Generate from raw markdown text
  
- `generate_from_file(proposal_path: str, output_path: Optional[str] = None) -> bytes`
  - Generate from file (supports .md, .txt, .docx)
  
- `generate_from_proposal(proposal: ProposalData, output_path: Optional[str] = None) -> bytes`
  - Generate from already-parsed ProposalData object

## Service Components

- `ppt_service.py` - Main service orchestrator
- `proposal_parser.py` - Parses markdown proposals
- `docx_reader.py` - Parses Word documents
- `info_reducer.py` - AI-powered content reduction
- `quote_service.py` - AI-powered quote generation
- `deck_generator.py` - PowerPoint deck builder
- `models.py` - Data models
- `prompts.py` - AI prompts

## Integration Examples

### Flask Integration

```python
from flask import Flask, request, send_file
from ppt_gen import PPTService
import io

app = Flask(__name__)
service = PPTService()

@app.route('/generate-ppt', methods=['POST'])
def generate_ppt():
    file = request.files['proposal']
    pptx_bytes = service.generate_from_file(file.filename)
    return send_file(
        io.BytesIO(pptx_bytes),
        mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation',
        as_attachment=True,
        download_name='presentation.pptx'
    )
```

### n8n/Make.com Integration

The service can be called via HTTP API if wrapped in a web service, or used directly in Python code nodes.

## Design Specifications

- **Background**: Black (#000000)
- **Titles**: Reddish-brown (#8B4513)
- **Quotes**: Green (#00FF00)
- **Layout**: Two-column layouts where specified
- **Emotional Sequencing**: Seen → Understood → Oriented → Deciding

## Output

The service generates a 14-slide PowerPoint presentation following the specified structure and design requirements.


