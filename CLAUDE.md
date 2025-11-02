# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based GEDCOM (genealogical data) parser that converts family tree data into Obsidian-compatible Markdown notes with WikiLinks. The project extracts comprehensive genealogical data including relationships, events, images, and long-form narratives.

## Key Features

- **GEDZIP Support**: Automatically extracts and processes ZIP archives with media files
- **Automatic Line Ending Fix**: Detects and corrects Mac-style line endings
- **Organized Directory Structure**: Creates separate subdirectories for people, media, and stories (or flat structure with `--flat`)
- **Canvas Visualization**: Generates Obsidian Canvas files for interactive family tree visualization
- **Complete Individual Notes**: Detailed markdown notes for each person with comprehensive data
- **Separate Story Files**: Extracts long-form narratives to individual markdown files with bidirectional linking
- **WikiLinks**: All relationships use `[[WikiLinks]]` format for Obsidian
- **Multiple Marriages**: Full support for individuals with multiple spouses
- **Media Management**: Automatically copies and organizes image files with collision detection
- **Global Index**: Creates alphabetical index of all individuals
- **Interactive Person Selection**: Choose root person for canvas with sortable list
- **Comprehensive Testing**: pytest-based test suite with coverage reporting

## Core Architecture

The codebase follows a clean modular architecture in `src/`:

1. **GedcomParser** (`gedcom_parser.py`): GEDCOM file parser
   - Wraps the `python-gedcom` library with error handling
   - Parses GEDCOM files and extracts individuals
   - Provides element lookup by pointer/ID
   - Handles line ending issues (CR vs LF)
   - Automatically detects and fixes Mac-style line endings

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
   - Creates separate story files in stories/ subdirectory (or output root if using --flat)
   - Supports both organized (subdirectories) and flat directory structures

4. **IndexGenerator** (`index_generator.py`): Global index creation
   - Creates alphabetical index by last name
   - Groups individuals by first letter
   - Includes life spans where available
   - Generates WikiLinks to person notes with proper path prefixes

5. **CanvasGenerator** (`canvas_generator.py`): Obsidian Canvas visualization
   - Generates JSON Canvas files for family tree visualization
   - Creates generational layout with ancestors to the right, descendants to the left
   - Builds tree structure using breadth-first search from root person
   - Handles disconnected family trees (adds as separate groups)
   - Positions nodes with proper spacing: generations, siblings, couples
   - Creates edges for parent-child and spouse relationships
   - Includes person images in canvas nodes when available

6. **PersonSelector** (`person_selector.py`): Interactive root person selection
   - Displays all individuals in sortable, numbered list
   - Shows name, birth year, death year for each person
   - Supports both interactive selection and command-line specification
   - Accepts numeric index (e.g., "85") or GEDCOM ID (e.g., "@I253884714@")
   - Used for canvas root person selection

7. **main.py**: CLI entry point
   - Argument parsing with argparse (--input, --output, --flat, --canvas, --root, etc.)
   - Logging configuration (INFO for main, WARNING for libraries, DEBUG with --verbose)
   - Handles GEDZIP extraction to temporary directory
   - Orchestrates parsing, generation, indexing, and canvas creation
   - Manages media file copying with collision detection
   - Cleanup of temporary files

## Development Environment Setup

```sh
# Install dependencies
pip install -r requirements.txt

# Run tests (requires pytest and pytest-cov)
pytest

# Run with coverage report
pytest --cov=src --cov-report=html
```

## Running the Converter

### Basic Usage
```sh
# With GEDCOM file (creates organized subdirectories)
python src/main.py --input examples/Stammbaum_Kucera.ged --output output/

# Short form
python src/main.py -i examples/Stammbaum_Kucera.ged -o output/

# With GEDZIP file (recommended - includes media)
python src/main.py -i examples/family.zip -o output/
```

### Directory Structure Options
```sh
# Organized structure (default): creates people/, media/, stories/ subdirectories
python src/main.py -i input.ged -o output/

# Flat structure: all files in output root
python src/main.py -i input.ged -o output/ --flat
```

### Canvas Generation
```sh
# Interactive root person selection
python src/main.py -i input.ged -o output/ --canvas

# Specify root person by selection number
python src/main.py -i input.ged -o output/ --canvas --root 85

# Specify root person by GEDCOM ID
python src/main.py -i input.ged -o output/ --canvas --root @I253884714@
python src/main.py -i input.ged -o output/ --canvas --root I253884714
```

### Other Options
```sh
# Verbose logging
python src/main.py -i input.ged -o output/ --verbose

# Skip index creation
python src/main.py -i input.ged -o output/ --no-index

# All options combined
python src/main.py -i family.zip -o output/ --flat --canvas --root 85 --verbose
```

**Note**: Output directory will be created automatically if it doesn't exist.

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
- Story references (`_STO`) to narrative text (extracted to separate files)
- Family references to spouse and children data
- Image/media references (OBJE) to file paths

### Multiple Marriages
Families are extracted with full context:
- Partner information with WikiLinks
- Marriage date and place
- Children grouped by marriage
- All marriages numbered if more than one

### Story Files
Long-form narratives (`_STO` tags) are extracted to separate markdown files:
- Created in stories/ subdirectory (or output root with --flat)
- Bidirectional linking between person notes and story files
- Properly resolved image paths within stories
- Story title and description as metadata

### Canvas Visualization
The CanvasGenerator creates Obsidian Canvas files:
- Left-to-right timeline layout (descendants left, ancestors right)
- Gender-aware vertical positioning (reduces crossings)
- Automatic handling of disconnected family trees
- Includes person images in nodes when available
- Parent-child edges connect left to right
- Spouse edges are bidirectional (vertical)

## Common Issues

### Line Ending Problem
Some GEDCOM files (especially from macOS apps) use CR line endings which the parser can't handle. **This is now automatically detected and fixed** by the converter. You'll see a warning message but the conversion will proceed.

Symptoms of CR-only line endings:
- Parser reports 0 individuals
- No output files created
- Warning message about Mac-style line endings

**Fix**: Automatic - the converter detects and converts line endings on the fly.

### Empty Notes
If NOTE records exist but appear empty, they may be placeholder records without content. This is valid GEDCOM.

### Story Tags
The `_STO` tag is a custom extension used by MobileFamilyTree. Other genealogy programs may use different custom tags for stories.

### GEDCOM Version Compatibility
This tool works best with GEDCOM version 5.5.x or 5.x. GEDCOM 7.0+ may have compatibility issues with custom tags. When exporting from genealogy software, choose GEDCOM 5.5.1 or 5.1.0 if available, and prefer GEDZIP format to include media files.

### Media File Handling
When using GEDZIP files:
- All media files (jpg, jpeg, png, gif, bmp) are automatically extracted and copied
- Files are organized in media/ subdirectory (or output root with --flat)
- Filename collisions are handled with numeric suffixes
- Relative paths in GEDCOM are preserved

## Testing

The project uses pytest for testing with comprehensive coverage:

### Test Structure
```
tests/
├── conftest.py              # Shared fixtures
├── test_gedcom_parser.py    # Parser tests
├── test_individual.py       # Individual model tests
├── test_markdown_generator.py  # Markdown generation tests
├── test_index_generator.py  # Index generation tests
├── test_main.py             # CLI integration tests
└── __init__.py
```

### Running Tests
```sh
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_individual.py

# Run with coverage report
pytest --cov=src --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=src --cov-report=html
# Open htmlcov/index.html
```

### Test Configuration
Tests are configured in `pytest.ini`:
- Test discovery: `tests/` directory
- Python path: `src/` (allows direct imports)
- Coverage: Branch and line coverage enabled
- Coverage reports: Terminal (with missing lines) and HTML

### Writing Tests
- Use fixtures from `conftest.py` for sample GEDCOM data
- Test both happy path and error cases
- Use descriptive test names: `test_<functionality>_<scenario>`
- Mock file I/O and external dependencies
- Aim for high coverage on core business logic

## Dependencies

- `python-gedcom==1.0.0`: GEDCOM parsing library
- `pytest>=7.4.0`: Testing framework
- `pytest-cov>=4.1.0`: Coverage plugin
- Python 3.8+

Update dependencies:
```sh
pip install <package-name>
pip freeze > requirements.txt
```

## Code Style

- Follow PEP 8
- Use type hints for all function signatures
- Docstrings for all public functions and classes (Google style)
- Logging for important operations (use module-level logger)
- Proper error handling with specific exceptions
- Clear variable names that explain purpose
- Extract magic numbers to named constants
- Keep functions focused on single responsibility
