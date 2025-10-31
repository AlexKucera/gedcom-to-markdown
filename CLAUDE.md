# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based GEDCOM (genealogical data) parser that converts family tree data into Obsidian-compatible Markdown notes with WikiLinks. The project extracts comprehensive genealogical data including relationships, events, images, and long-form narratives.

## Core Architecture

The codebase follows a clean modular architecture in `src/`:

1. **GedcomParser** (`gedcom_parser.py`): GEDCOM file parser
   - Wraps the `python-gedcom` library with error handling
   - Parses GEDCOM files and extracts individuals
   - Provides element lookup by pointer/ID
   - Handles line ending issues (CR vs LF)

2. **Individual** (`individual.py`): Rich person data model
   - Comprehensive data extraction: names, dates, relationships, events
   - Resolves GEDCOM references (notes, images, stories)
   - Supports multiple marriages and families
   - Extracts physical attributes (eyes, hair, height)
   - Handles custom tags like `_STO` (stories from MobileFamilyTree)
   - Generates proper filenames: "FamilyName FirstName BirthYear"

3. **MarkdownGenerator** (`markdown_generator.py`): Obsidian note creation
   - Generates notes with proper WikiLinks format
   - Sections: Attributes, Events, Families, Parents, Children, Images, Notes
   - Uses Obsidian metadata: `[key:: value]` (visible) and `(key:: value)` (hidden)
   - Handles multiple marriages with proper formatting

4. **IndexGenerator** (`index_generator.py`): Global index creation
   - Creates alphabetical index by last name
   - Groups individuals by first letter
   - Includes life spans where available

5. **main.py**: CLI entry point
   - Argument parsing with argparse
   - Logging configuration
   - Orchestrates parsing, generation, and indexing

## Development Environment Setup

```sh
# Install dependencies
pip install -r requirements.txt

# The main script is directly executable
python src/main.py <gedcom_file> <output_dir>
```

## Running the Converter

### Basic Usage
```sh
python src/main.py examples/Stammbaum_Kucera.ged output/
```

### With Options
```sh
# Verbose logging
python src/main.py input.ged output/ --verbose

# Skip index creation
python src/main.py input.ged output/ --no-index
```

**Important**: Output directory must exist before running.

## Key Implementation Details

### File Naming Convention
- Format: "FamilyName FirstName BirthYear.md"
- Birth year omitted if unknown
- Example: "Kucera Alexander Maximilian 1980.md"

### Obsidian Metadata Format
- Visible metadata: `[key:: value]` - displays in note
- Hidden metadata: `(key:: value)` - indexed but not displayed
- WikiLinks: `[[Note Name]]` - links to other notes

### Data Extraction Strategy
The Individual class extracts data through several methods:
- `get_names()`: Returns (first_name, last_name) tuple
- `get_families()`: Returns list of marriages with partners and children
- `get_events()`: Extracts BIRT, DEAT, OCCU, EDUC, RESI, BURI events
- `get_notes()`: Resolves NOTE references and inline notes
- `get_stories()`: Extracts custom `_STO` story records
- `get_images()`: Extracts OBJE media references

### Reference Resolution
GEDCOM uses pointers (`@ID@`) to reference other records. The Individual class resolves:
- NOTE references to actual note text
- Story references (`_STO`) to narrative text
- Family references to spouse and children data

### Multiple Marriages
Families are extracted with full context:
- Partner information with WikiLinks
- Marriage date and place
- Children grouped by marriage
- All marriages numbered if more than one

## Common Issues

### Line Ending Problem
Some GEDCOM files (especially from macOS apps) use CR line endings which the parser can't handle. Symptoms:
- Parser reports 0 individuals
- No output files created

**Fix**: Convert line endings before parsing (see README.md)

### Empty Notes
If NOTE records exist but appear empty, they may be placeholder records without content. This is valid GEDCOM.

### Story Tags
The `_STO` tag is a custom extension used by MobileFamilyTree. Other genealogy programs may use different custom tags for stories.

## Dependencies

- `python-gedcom==1.0.0`: GEDCOM parsing library
- Python 3.7+

Update dependencies:
```sh
pip install <package-name>
pip freeze > requirements.txt
```

## Code Style

- Follow PEP 8
- Use type hints for all function signatures
- Docstrings for all public functions and classes
- Logging for important operations
- Proper error handling with specific exceptions
