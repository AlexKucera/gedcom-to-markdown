#!/usr/bin/env python3
"""
GEDCOM to Markdown converter.

This script converts GEDCOM genealogy files into Obsidian-compatible
markdown notes with WikiLinks.
"""

import argparse
import logging
import sys
from pathlib import Path

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


def convert_gedcom_to_markdown(
    gedcom_file: Path,
    output_dir: Path,
    create_index: bool = True
) -> int:
    """
    Convert a GEDCOM file to markdown notes.

    Args:
        gedcom_file: Path to the input GEDCOM file
        output_dir: Directory for output markdown files
        create_index: Whether to create an index file

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
        generator = MarkdownGenerator(output_dir)
        created_files = generator.generate_all(individuals)
        logger.info(f"Created {len(created_files)} markdown files")

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
        help='Path to the input GEDCOM file'
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

    # Convert
    exit_code = convert_gedcom_to_markdown(
        gedcom_file=args.gedcom_file,
        output_dir=args.output_dir,
        create_index=not args.no_index
    )

    return exit_code


if __name__ == '__main__':
    sys.exit(main())
