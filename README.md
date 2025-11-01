# GEDCOM to Markdown Converter

Convert GEDCOM genealogy files to Obsidian-compatible markdown notes with WikiLinks.

## Features

- **GEDZIP Support**: Automatically extracts and processes ZIP archives with media files
- **Automatic Line Ending Fix**: Detects and corrects Mac-style line endings
- **Complete Individual Notes**: Generates detailed markdown notes for each person
- **WikiLinks**: All relationships use `[[WikiLinks]]` format for Obsidian
- **Comprehensive Data**: Captures births, deaths, marriages, events, physical attributes, images, and notes
- **Multiple Marriages**: Supports individuals with multiple spouses
- **Life Stories**: Extracts long-form narratives and stories with embedded images
- **Media Management**: Automatically copies and organizes image files
- **Global Index**: Creates an alphabetical index of all individuals
- **Proper Naming**: Files named as "FamilyName FirstName BirthYear.md"

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python src/main.py path/to/family.ged output/directory
```

### GEDZIP Support (Recommended)

For best results, **export your genealogy data as a GEDZIP (ZIP) file** which includes both the GEDCOM data and all media files:

```bash
python src/main.py path/to/family.zip output/directory --media-subdir images
```

This will automatically:
- Extract the ZIP file
- Find and process the GEDCOM file
- Copy all media files to the output directory
- Fix line endings if needed
- Clean up temporary files

### Options

- `--no-index`: Skip creating the index file
- `--verbose` or `-v`: Enable detailed logging
- `--media-subdir <name>`: Place media files in a subdirectory (e.g., "images")

### Examples

**With GEDZIP file (includes media):**
```bash
python src/main.py examples/family.zip examples/output --media-subdir images --verbose
```

**With plain GEDCOM file:**
```bash
python src/main.py examples/family.ged examples/output --verbose
```

This will create:
- One markdown file per person in the output directory
- An `Index.md` file with alphabetical listing
- Media files in `output/images/` (if GEDZIP and --media-subdir used)

## Output Format

Each person gets a markdown note with sections for:
- **Attributes**: Name, birth, death, physical characteristics
- **Life Events**: Occupations, education, residences, etc.
- **Families**: Marriages with dates, places, and children
- **Parents**: Links to parent notes
- **Images**: Media references from GEDCOM
- **Notes**: Long-form stories and narratives

## Project Structure

```
src/
├── gedcom_parser.py      # GEDCOM file parsing
├── individual.py         # Person data model
├── markdown_generator.py # Note generation
├── index_generator.py    # Index file creation
└── main.py              # CLI entry point
```

## Requirements

- Python 3.7+
- python-gedcom==1.0.0

## Common Issues

### Line Ending Issue

Some GEDCOM files exported from macOS applications use old Mac-style line endings (CR only). **This is automatically detected and fixed** by the converter.

If you see a warning message like:
```
WARNING - Detected old Mac-style (CR-only) line endings in GEDCOM file.
Converting to Unix-style (LF) line endings...
```

This is normal and the file will be automatically corrected. No manual intervention is needed.

### GEDCOM Version Compatibility

This tool works best with **GEDCOM version 5.5.x or 5.x**. If you're using GEDCOM 7.0+, you may encounter issues with custom tags and story extraction. When exporting from your genealogy software:

1. Choose GEDCOM version 5.5.1 or 5.1.0 if available
2. Avoid GEDCOM version 7.0+ for better compatibility
3. **Export as GEDZIP (ZIP)** to include media files automatically

### Exporting GEDZIP from Your Genealogy Software

Most genealogy applications support exporting to GEDZIP format:

- **Family Tree Maker**: File → Export → GEDCOM Package (includes media)
- **MobileFamilyTree**: Share → GEDCOM Package → Include Media
- **Ancestry**: Export family tree → Include media files → Download as ZIP
- **Gramps**: Family Trees → Export → GEDCOM with Media

The GEDZIP format is a standard ZIP archive containing:
- A `.ged` file with your family tree data
- All referenced media files (photos, documents, etc.)

This is the **recommended export format** for use with this converter.
