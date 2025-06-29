# PPTX Preprocessing for Gym Chatbot Knowledge Base

This document explains how to use the PPTX preprocessing script to convert PowerPoint presentations into a format suitable for your AWS Bedrock Knowledge Base.

## Overview

The PPTX preprocessing script (`preprocess_pptx.py`) extracts content from PowerPoint files, processes tables with color coding, and converts them into structured markdown format that can be ingested into your knowledge base.

### Key Features

- **Text Extraction**: Extracts all text content from slides
- **Table Processing**: Converts tables to markdown format
- **Color Coding Interpretation**: Analyzes cell colors and assigns meanings
- **Slide Notes**: Extracts speaker notes and comments
- **Metadata Extraction**: Captures presentation properties
- **Batch Processing**: Handles multiple files at once
- **Structured Output**: Generates both JSON and markdown formats

## Installation

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

The script requires the `python-pptx` library, which is already included in `requirements.txt`.

### 2. Verify Installation

```bash
python -c "import pptx; print('✅ python-pptx installed successfully')"
```

## Usage

### Basic Usage

#### Process a Single PPTX File

```bash
python preprocess_pptx.py your_presentation.pptx -o processed/
```

#### Process Multiple Files

```bash
python preprocess_pptx.py *.pptx -o processed/
```

#### Process Files from a Directory

```bash
python preprocess_pptx.py /path/to/pptx/files/ -o processed/
```

### Advanced Usage

#### Generate Structured Output (JSON + Markdown)

```bash
python preprocess_pptx.py presentation.pptx -o output/ --format structured
```

This creates:
- `presentation_processed.json` - Structured data with metadata
- `presentation_processed.md` - Markdown for knowledge base

#### Generate Markdown Only

```bash
python preprocess_pptx.py presentation.pptx -o output/ --format markdown
```

#### Enable Verbose Logging

```bash
python preprocess_pptx.py presentation.pptx -o output/ --verbose
```

## Output Format

### Markdown Output

The script generates markdown files with the following structure:

```markdown
# Presentation Title

**Source:** presentation.pptx
**Author:** John Doe
**Subject:** Fitness Training
**Total Slides:** 10

## Slide 1: Introduction

Welcome to the fitness training program...

### Table 1

| Exercise | Sets | Reps | Intensity |
|----------|------|------|-----------|
| Squats | 3 | 12 | Moderate/Average |
| Deadlifts | 3 | 8 | Good |
| Bench Press | 3 | 10 | Poor/Needs Attention |

**Color Coding Legend:**
- Good
- Moderate/Average
- Poor/Needs Attention

**Notes:** Focus on proper form during all exercises.

## Summary

- **Total Slides:** 10
- **Total Tables:** 3
- **Total Text Blocks:** 15
- **Color-Coded Cells:** 12

**Color Distribution:**
- Good: 8 cells
- Moderate/Average: 3 cells
- Poor/Needs Attention: 1 cell
```

### JSON Output

The structured JSON output includes:

```json
{
  "metadata": {
    "filename": "presentation.pptx",
    "title": "Fitness Training Program",
    "author": "John Doe",
    "total_slides": 10
  },
  "slides": [
    {
      "slide_number": 1,
      "title": "Introduction",
      "text_content": ["Welcome to the fitness training program..."],
      "tables": [...],
      "notes": "Focus on proper form during all exercises."
    }
  ],
  "summary": {
    "total_slides": 10,
    "total_tables": 3,
    "total_color_coded_cells": 12,
    "color_distribution": {
      "Good": 8,
      "Moderate/Average": 3,
      "Poor/Needs Attention": 1
    }
  }
}
```

## Color Coding Interpretation

The script automatically interprets common color coding patterns:

### Default Color Meanings

- **Green Variations**: Excellent/Great, Good
- **Yellow Variations**: Moderate/Average
- **Red Variations**: Poor/Needs Attention
- **Blue Variations**: Informational
- **Gray Variations**: Neutral

### Customizing Color Meanings

You can modify the color meanings in the `ColorCodingInterpreter` class:

```python
COLOR_MEANINGS = {
    '00FF00': 'Excellent/Great',
    'FF0000': 'Poor/Needs Attention',
    # Add your custom colors here
}
```

## Integration with Knowledge Base

### 1. Process Your PPTX Files

```bash
# Process all PPTX files in your data directory
python preprocess_pptx.py ../data/*.pptx -o processed_pptx/
```

### 2. Review Generated Files

Check the generated markdown files to ensure they look correct:

```bash
# View the processed output
cat processed_pptx/your_presentation_processed.md
```

### 3. Upload to Knowledge Base

Use the existing ingestion script to upload the processed files:

```bash
# Copy processed files to data directory
cp processed_pptx/*.md ../data/

# Run the ingestion script
cd ../terraform
python scripts/ingest_documents.py
```

## Examples

### Example 1: Fitness Assessment Presentation

```bash
# Process a fitness assessment presentation
python preprocess_pptx.py fitness_assessment.pptx -o processed/

# This will create:
# - fitness_assessment_processed.md (for knowledge base)
# - fitness_assessment_processed.json (structured data)
```

### Example 2: Workout Plan with Color-Coded Tables

```bash
# Process a workout plan with color-coded intensity levels
python preprocess_pptx.py workout_plan.pptx -o processed/ --verbose

# The script will interpret:
# - Green cells as "Good/Recommended"
# - Yellow cells as "Moderate/Intermediate"
# - Red cells as "Advanced/Use Caution"
```

### Example 3: Batch Processing Training Materials

```bash
# Process all training materials at once
python preprocess_pptx.py training_materials/ -o processed/ --format structured

# This processes all PPTX files in the training_materials directory
```

## Troubleshooting

### Common Issues

#### 1. "python-pptx not found" Error

```bash
pip install python-pptx
```

#### 2. "No PPTX files found" Error

Ensure your files have the `.pptx` extension (not `.ppt`).

#### 3. Color Coding Not Detected

- Check if the table cells have background colors
- Verify the colors are not theme-based
- Try processing with `--verbose` flag for debugging

#### 4. Large Files Take Too Long

- The script processes files sequentially
- Consider processing files individually for very large presentations
- Check the log file for progress information

### Debug Mode

Enable verbose logging to see detailed processing information:

```bash
python preprocess_pptx.py file.pptx -o output/ --verbose
```

This will show:
- File loading progress
- Slide processing details
- Table extraction information
- Color coding analysis
- Output file creation

## Best Practices

### 1. File Organization

```
data/
├── raw_pptx/
│   ├── presentation1.pptx
│   ├── presentation2.pptx
│   └── ...
├── processed_pptx/
│   ├── presentation1_processed.md
│   ├── presentation2_processed.md
│   └── ...
└── knowledge_base/
    ├── presentation1_processed.md
    ├── presentation2_processed.md
    └── ...
```

### 2. Color Coding Standards

Use consistent color coding in your presentations:

- **Green**: Good/Recommended/Pass
- **Yellow**: Moderate/Average/Caution
- **Red**: Poor/Needs Attention/Fail
- **Blue**: Informational/Reference
- **Gray**: Neutral/Not Applicable

### 3. Table Structure

For best results, structure your tables with:

- Clear headers in the first row
- Consistent data types in columns
- Meaningful color coding
- Descriptive cell content

### 4. Slide Organization

- Use descriptive slide titles
- Include speaker notes for context
- Keep text concise and readable
- Use consistent formatting

## Integration with Existing Workflow

### Current Knowledge Base Workflow

1. **Document Preparation**: Convert PPTX to markdown
2. **Quality Review**: Check processed output
3. **Upload to S3**: Use Terraform scripts
4. **Ingest to Bedrock**: Use ingestion script
5. **Test Chatbot**: Verify knowledge retrieval

### Enhanced Workflow with PPTX Processing

1. **PPTX Processing**: Run preprocessing script
2. **Content Review**: Check generated markdown
3. **Format Optimization**: Adjust if needed
4. **Upload to S3**: Use existing Terraform scripts
5. **Ingest to Bedrock**: Use existing ingestion script
6. **Test Knowledge Retrieval**: Verify chatbot responses

## Script Customization

### Adding Custom Color Meanings

Edit the `ColorCodingInterpreter` class in `preprocess_pptx.py`:

```python
COLOR_MEANINGS = {
    # Add your custom colors
    'FF6B6B': 'High Priority',
    '4ECDC4': 'Low Priority',
    '45B7D1': 'Reference',
    # ... existing colors
}
```

### Modifying Output Format

Customize the `format_for_knowledge_base` method to change the markdown structure:

```python
def format_for_knowledge_base(self, processed_data):
    # Customize the output format here
    # ...
```

### Adding Custom Processing

Extend the `PPTXProcessor` class to add custom processing logic:

```python
class CustomPPTXProcessor(PPTXProcessor):
    def custom_processing_method(self, slide):
        # Add your custom processing logic
        pass
```

## Support

For issues or questions:

1. Check the log file: `pptx_preprocessing.log`
2. Run with `--verbose` flag for detailed output
3. Review the example script: `example_pptx_processing.py`
4. Check the main script documentation

## Next Steps

1. **Install Dependencies**: `pip install -r requirements.txt`
2. **Test with Sample File**: Use the example script
3. **Process Your Files**: Run the preprocessing script
4. **Review Output**: Check generated markdown files
5. **Upload to Knowledge Base**: Use existing ingestion workflow
6. **Test Chatbot**: Verify knowledge retrieval works correctly 