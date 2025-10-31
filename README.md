# GEDCOM to Markdown Converter

Convert GEDCOM genealogy files to Obsidian-compatible markdown notes with WikiLinks.

## Features

- **Complete Individual Notes**: Generates detailed markdown notes for each person
- **WikiLinks**: All relationships use `[[WikiLinks]]` format for Obsidian
- **Comprehensive Data**: Captures births, deaths, marriages, events, physical attributes, images, and notes
- **Multiple Marriages**: Supports individuals with multiple spouses
- **Life Stories**: Extracts long-form narratives and stories
- **Global Index**: Creates an alphabetical index of all individuals
- **Proper Naming**: Files named as "FamilyName FirstName BirthYear.md"

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python src/main.py path/to/family.ged output/directory
```

### Options

- `--no-index`: Skip creating the index file
- `--verbose` or `-v`: Enable detailed logging

### Example

```bash
python src/main.py examples/Stammbaum_Kucera.ged examples/files --verbose
```

This will create:
- One markdown file per person in `examples/files/`
- An `Index.md` file with alphabetical listing

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

## Line Ending Issue

**Important**: Some GEDCOM files exported from macOS applications may use old Mac-style line endings (CR only). If the parser finds 0 individuals, convert line endings first:

```bash
python -c "
with open('file.ged', 'rb') as f:
    content = f.read()
with open('file.ged', 'wb') as f:
    f.write(content.replace(b'\r', b'\n'))
"
```
