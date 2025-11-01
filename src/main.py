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
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
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
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(temp_dir)

    logger.info(f"Extracted to: {temp_dir}")

    # Find the GEDCOM file (should have .ged extension)
    gedcom_files = list(temp_dir.glob("**/*.ged"))

    if not gedcom_files:
        raise ValueError("No GEDCOM (.ged) file found in the ZIP archive")

    if len(gedcom_files) > 1:
        logger.warning(
            f"Found {len(gedcom_files)} GEDCOM files, using first: {gedcom_files[0]}"
        )

    gedcom_file = gedcom_files[0]
    logger.info(f"Found GEDCOM file: {gedcom_file.name}")

    # Find media directory (look for common image extensions)
    media_dir = None
    for ext in ["*.jpg", "*.jpeg", "*.png", "*.gif", "*.bmp"]:
        media_files = list(temp_dir.glob(f"**/{ext}"))
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
    use_flat_structure: bool = False,
) -> int:
    """
    Convert a GEDCOM file to markdown notes.

    Args:
        gedcom_file: Path to the input GEDCOM file
        output_dir: Directory for output markdown files
        create_index: Whether to create an index file
        media_dir: Optional directory containing media files to copy
        use_flat_structure: If True, use flat structure. If False, create subdirectories.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    logger = logging.getLogger(__name__)

    try:
        # Determine directory structure
        if use_flat_structure:
            people_dir = output_dir
            media_output_dir = output_dir
            stories_dir = output_dir
            media_subdir_name = ""
            stories_subdir_name = ""
        else:
            people_dir = output_dir / "people"
            media_output_dir = output_dir / "media"
            stories_dir = output_dir / "stories"
            media_subdir_name = "media"
            stories_subdir_name = "stories"

            # Create subdirectories
            people_dir.mkdir(parents=True, exist_ok=True)
            media_output_dir.mkdir(parents=True, exist_ok=True)
            stories_dir.mkdir(parents=True, exist_ok=True)

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
        individuals = [Individual(elem, parser) for elem in individual_elements]

        # Generate markdown notes
        logger.info(f"Generating markdown notes in: {people_dir}")
        generator = MarkdownGenerator(
            people_dir,
            media_subdir=media_subdir_name,
            stories_subdir=stories_subdir_name,
            stories_dir=stories_dir,
        )
        created_files = generator.generate_all(individuals)
        logger.info(f"Created {len(created_files)} markdown files")

        # Copy media files if available
        if media_dir and media_dir.exists():
            logger.info(f"Copying media files to: {media_output_dir}")
            media_files = []
            for ext in [
                "*.jpg",
                "*.jpeg",
                "*.png",
                "*.gif",
                "*.bmp",
                "*.JPG",
                "*.JPEG",
                "*.PNG",
            ]:
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
            people_subdir_name = "" if use_flat_structure else "people"
            index_gen = IndexGenerator(output_dir, people_subdir=people_subdir_name)
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
        description="Convert GEDCOM genealogy files to Obsidian markdown notes",
        epilog="Example: python src/main.py --input family.zip --output vault/family",
    )

    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        required=True,
        metavar="FILE",
        help="Path to input GEDCOM (.ged) or GEDZIP (.zip) file",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        metavar="DIR",
        help="Output directory for generated notes",
    )

    parser.add_argument(
        "--flat",
        action="store_true",
        help="Use flat structure (all files in output root). Default creates subdirectories: people/, media/, stories/",
    )

    parser.add_argument(
        "--no-index", action="store_true", help="Do not create an index file"
    )

    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    # Validate inputs
    if not args.input.exists():
        logger.error(f"Input file not found: {args.input}")
        return 1

    # Create output directory if it doesn't exist
    args.output.mkdir(parents=True, exist_ok=True)

    # Check if input is a ZIP file
    is_zip = args.input.suffix.lower() in [".zip", ".gedzip"]
    temp_dir = None
    gedcom_file = args.input
    media_dir = None

    try:
        if is_zip:
            # Extract ZIP file to temporary directory
            temp_dir = Path(tempfile.mkdtemp(prefix="gedcom_"))
            gedcom_file, media_dir = extract_gedzip(args.input, temp_dir)

        # Convert
        exit_code = convert_gedcom_to_markdown(
            gedcom_file=gedcom_file,
            output_dir=args.output,
            create_index=not args.no_index,
            media_dir=media_dir,
            use_flat_structure=args.flat,
        )

        return exit_code

    finally:
        # Clean up temporary directory
        if temp_dir and temp_dir.exists():
            logger.debug(f"Cleaning up temporary directory: {temp_dir}")
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    sys.exit(main())
