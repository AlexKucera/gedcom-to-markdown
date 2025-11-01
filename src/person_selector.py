"""
Interactive person selector for choosing root person in family tree.

This module provides functionality to display individuals from a GEDCOM file
in a multi-column format and allow the user to select one as the root person
for canvas generation.
"""

import logging
from typing import List, Optional
from individual import Individual


logger = logging.getLogger(__name__)


def select_root_person(individuals: List[Individual]) -> Optional[str]:
    """
    Display an interactive list of individuals and let user select root person.

    Args:
        individuals: List of Individual objects from GEDCOM file

    Returns:
        The GEDCOM pointer/ID of the selected individual, or None if cancelled
    """
    if not individuals:
        logger.error("No individuals provided for selection")
        return None

    # Sort individuals by last name, then first name
    sorted_individuals = sorted(
        individuals,
        key=lambda ind: (
            ind.get_names()[1] or "",  # Last name
            ind.get_names()[0] or ""   # First name
        )
    )

    print("\n" + "="*80)
    print("SELECT ROOT PERSON FOR FAMILY TREE CANVAS")
    print("="*80)
    print(f"\nTotal individuals: {len(sorted_individuals)}\n")

    # Display individuals in a numbered list with columns
    # Format: Index | Name | Birth | Death
    print(f"{'#':<5} {'Name':<40} {'Birth':<12} {'Death':<12}")
    print("-" * 80)

    for idx, individual in enumerate(sorted_individuals, start=1):
        first_name, last_name = individual.get_names()
        full_name = f"{last_name or ''} {first_name or ''}".strip()

        # Get birth and death years
        birth_year = ""
        death_year = ""
        events = individual.get_events()

        for event in events:
            if event["type"] == "BIRT" and event.get("date"):
                # Extract year from date string (format varies)
                date_str = event["date"]
                # Try to find a 4-digit year
                import re
                year_match = re.search(r'\b(\d{4})\b', date_str)
                if year_match:
                    birth_year = year_match.group(1)
            elif event["type"] == "DEAT" and event.get("date"):
                date_str = event["date"]
                import re
                year_match = re.search(r'\b(\d{4})\b', date_str)
                if year_match:
                    death_year = year_match.group(1)

        print(f"{idx:<5} {full_name:<40} {birth_year:<12} {death_year:<12}")

    print("-" * 80)

    # Prompt for selection
    while True:
        try:
            selection = input("\nEnter number to select root person (or 'q' to quit): ").strip()

            if selection.lower() == 'q':
                logger.info("User cancelled person selection")
                return None

            index = int(selection)
            if 1 <= index <= len(sorted_individuals):
                selected = sorted_individuals[index - 1]
                first_name, last_name = selected.get_names()
                full_name = f"{last_name or ''} {first_name or ''}".strip()

                print(f"\nSelected: {full_name}")
                logger.info(f"User selected root person: {full_name} ({selected.get_pointer()})")

                return selected.get_pointer()
            else:
                print(f"Please enter a number between 1 and {len(sorted_individuals)}")

        except ValueError:
            print("Invalid input. Please enter a number or 'q' to quit.")
        except KeyboardInterrupt:
            print("\n\nSelection cancelled.")
            logger.info("User cancelled person selection with Ctrl+C")
            return None
