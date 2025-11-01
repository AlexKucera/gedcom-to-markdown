#!/usr/bin/env python3
"""
GEDCOM to Markdown converter.

This script converts GEDCOM genealogy files into Obsidian-compatible
markdown notes with WikiLinks.
"""

import argparse
import logging
import sys
import tempfile
import zipfile
import shutil
from pathlib import Path
from typing import Tuple, Optional

from gedcom_parser import GedcomParser
from individual import Individual
from markdown_generator import MarkdownGenerator
from index_generator import IndexGenerator


def setup_logging(verbose: bool = False):
    """Configure logging for the application."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def extract_gedzip(zip_path: Path, temp_dir: Path) -> Tuple[Path, Optional[Path]]:
    """
    Extract a GEDZIP file and locate the GEDCOM file and media directory.

    Args:
        zip_path: Path to the ZIP/GEDZIP file
        temp_dir: Temporary directory for extraction

    Returns:
        Tuple of (gedcom_file_path, media_directory_path)

    Raises:
        ValueError: If no GEDCOM file is found in the archive
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Extracting ZIP archive: {zip_path}")

    # Extract the ZIP file
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)

    logger.info(f"Extracted to: {temp_dir}")

    # Find the GEDCOM file (should have .ged extension)
    gedcom_files = list(temp_dir.glob('**/*.ged'))

    if not gedcom_files:
        raise ValueError("No GEDCOM (.ged) file found in the ZIP archive")

    if len(gedcom_files) > 1:
        logger.warning(f"Found {len(gedcom_files)} GEDCOM files, using first: {gedcom_files[0]}")

    gedcom_file = gedcom_files[0]
    logger.info(f"Found GEDCOM file: {gedcom_file.name}")

    # Find media directory (look for common image extensions)
    media_dir = None
    for ext in ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp']:
        media_files = list(temp_dir.glob(f'**/{ext}'))
        if media_files:
            # Get the common parent directory of media files
            media_dir = media_files[0].parent
            logger.info(f"Found {len(media_files)} media files in: {media_dir}")
            break

    return gedcom_file, media_dir


def convert_gedcom_to_markdown(
    gedcom_file: Path,
    output_dir: Path,
    create_index: bool = True,
    media_dir: Optional[Path] = None,
    media_subdir: str = ''
) -> int:
    """
    Convert a GEDCOM file to markdown notes.

    Args:
        gedcom_file: Path to the input GEDCOM file
        output_dir: Directory for output markdown files
        create_index: Whether to create an index file
        media_dir: Optional directory containing media files to copy
        media_subdir: Subdirectory name for media files (e.g., 'images')

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    logger = logging.getLogger(__name__)

    try:
        # Parse GEDCOM file
        logger.info(f"Parsing GEDCOM file: {gedcom_file}")
        parser = GedcomParser(gedcom_file)

        # Get all individuals
        individual_elements = parser.get_individuals()
        logger.info(f"Found {len(individual_elements)} individuals")

        if not individual_elements:
            logger.warning("No individuals found in GEDCOM file")
            return 1

        # Wrap individuals in our data model
        individuals = [
            Individual(elem, parser) for elem in individual_elements
        ]

        # Generate markdown notes
        logger.info(f"Generating markdown notes in: {output_dir}")
        generator = MarkdownGenerator(output_dir, media_subdir=media_subdir)
        created_files = generator.generate_all(individuals)
        logger.info(f"Created {len(created_files)} markdown files")

        # Copy media files if available
        if media_dir and media_dir.exists():
            media_output_dir = output_dir / media_subdir if media_subdir else output_dir
            media_output_dir.mkdir(parents=True, exist_ok=True)

            logger.info(f"Copying media files to: {media_output_dir}")
            media_files = []
            for ext in ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp', '*.JPG', '*.JPEG', '*.PNG']:
                media_files.extend(media_dir.glob(ext))

            copied_count = 0
            for media_file in media_files:
                dest = media_output_dir / media_file.name
                shutil.copy2(media_file, dest)
                copied_count += 1

            logger.info(f"Copied {copied_count} media files")

        # Generate index
        if create_index:
            logger.info("Generating index file")
            index_gen = IndexGenerator(output_dir)
            index_path = index_gen.generate_index(individuals)
            logger.info(f"Created index file: {index_path}")

        logger.info("Conversion completed successfully")
        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description='Convert GEDCOM genealogy files to Obsidian markdown notes'
    )

    parser.add_argument(
        'gedcom_file',
        type=Path,
        help='Path to the input GEDCOM (.ged) or GEDZIP (.zip) file'
    )

    parser.add_argument(
        'output_dir',
        type=Path,
        help='Directory for output markdown files'
    )

    parser.add_argument(
        '--no-index',
        action='store_true',
        help='Do not create an index file'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    parser.add_argument(
        '--media-subdir',
        type=str,
        default='',
        help='Subdirectory for media files (e.g., "images"). If not specified, media files are placed in output_dir.'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    # Validate inputs
    if not args.gedcom_file.exists():
        logger.error(f"GEDCOM file not found: {args.gedcom_file}")
        return 1

    if not args.output_dir.exists():
        logger.error(f"Output directory not found: {args.output_dir}")
        logger.info("Please create the output directory first")
        return 1

    # Check if input is a ZIP file
    is_zip = args.gedcom_file.suffix.lower() in ['.zip', '.gedzip']
    temp_dir = None
    gedcom_file = args.gedcom_file
    media_dir = None

    try:
        if is_zip:
            # Extract ZIP file to temporary directory
            temp_dir = Path(tempfile.mkdtemp(prefix='gedcom_'))
            gedcom_file, media_dir = extract_gedzip(args.gedcom_file, temp_dir)

        # Convert
        exit_code = convert_gedcom_to_markdown(
            gedcom_file=gedcom_file,
            output_dir=args.output_dir,
            create_index=not args.no_index,
            media_dir=media_dir,
            media_subdir=args.media_subdir
        )

        return exit_code

    finally:
        # Clean up temporary directory
        if temp_dir and temp_dir.exists():
            logger.debug(f"Cleaning up temporary directory: {temp_dir}")
            shutil.rmtree(temp_dir)


if __name__ == '__main__':
    sys.exit(main())
