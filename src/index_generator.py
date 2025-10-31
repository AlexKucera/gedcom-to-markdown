"""
Index file generator for family tree notes.

This module generates an alphabetical index of all individuals in the
family tree.
"""

from pathlib import Path
from typing import List
import logging

from individual import Individual


logger = logging.getLogger(__name__)


class IndexGenerator:
    """
    Generates an index file linking to all individual notes.

    The index is organized alphabetically by last name, then first name.
    """

    def __init__(self, output_dir: Path):
        """
        Initialize the index generator.

        Args:
            output_dir: Directory where the index file will be created
        """
        self.output_dir = output_dir

    def generate_index(
        self,
        individuals: List[Individual],
        index_filename: str = 'Index.md'
    ) -> Path:
        """
        Generate an alphabetical index of all individuals.

        Args:
            individuals: List of Individual objects
            index_filename: Name of the index file (default: 'Index.md')

        Returns:
            Path to the created index file
        """
        index_path = self.output_dir / index_filename

        logger.info(f"Generating index file: {index_filename}")

        # Sort individuals by last name, then first name
        sorted_individuals = sorted(
            individuals,
            key=lambda i: (i.get_names()[1].lower(), i.get_names()[0].lower())
        )

        with open(index_path, 'w', encoding='utf-8') as f:
            f.write("# Family Tree Index\n\n")
            f.write(f"Total individuals: {len(individuals)}\n\n")

            # Group by last name initial
            current_letter = ''

            for individual in sorted_individuals:
                first, last = individual.get_names()

                # Write letter header if changed
                if last:
                    letter = last[0].upper()
                else:
                    letter = '#'  # For individuals without last name

                if letter != current_letter:
                    current_letter = letter
                    f.write(f"\n## {current_letter}\n\n")

                # Write individual link with life span
                filename = individual.get_file_name()
                birth_info = individual.get_birth_info()
                death_info = individual.get_death_info()

                # Format life span
                if birth_info['year'] or death_info['date']:
                    death_year = death_info['date'][:4] if death_info['date'] else ''
                    life_span = f" ({birth_info['year']}-{death_year})"
                else:
                    life_span = ''

                f.write(f"- [[{filename}]]{life_span}\n")

        logger.info(f"Index generated with {len(individuals)} individuals")
        return index_path
