"""
GEDCOM file parser module.

This module provides a clean interface to parse GEDCOM files and extract
individual and family data.
"""

from pathlib import Path
from typing import List, Optional
import logging

from gedcom.parser import Parser
from gedcom.element.individual import IndividualElement


logger = logging.getLogger(__name__)


class GedcomParser:
    """
    Parser for GEDCOM genealogy files.

    This class wraps the python-gedcom library and provides a clean interface
    for parsing GEDCOM files and extracting individual data.
    """

    def __init__(self, file_path: Path):
        """
        Initialize the parser with a GEDCOM file.

        Args:
            file_path: Path to the GEDCOM file to parse

        Raises:
            FileNotFoundError: If the GEDCOM file doesn't exist
            ValueError: If the file cannot be parsed
        """
        if not file_path.exists():
            raise FileNotFoundError(f"GEDCOM file not found: {file_path}")

        self.file_path = file_path
        self.parser = Parser()

        try:
            logger.info(f"Parsing GEDCOM file: {file_path}")
            self.parser.parse_file(str(file_path))
        except Exception as e:
            raise ValueError(f"Failed to parse GEDCOM file: {e}") from e

    def get_individuals(self) -> List[IndividualElement]:
        """
        Get all individuals from the GEDCOM file.

        Returns:
            List of IndividualElement objects representing people in the tree
        """
        individuals = []
        for element in self.parser.get_root_child_elements():
            if isinstance(element, IndividualElement):
                individuals.append(element)

        logger.info(f"Found {len(individuals)} individuals")
        return individuals

    def get_element_by_pointer(self, pointer: str):
        """
        Get a GEDCOM element by its pointer/ID.

        Args:
            pointer: The GEDCOM pointer (e.g., '@I123@')

        Returns:
            The element with the given pointer, or None if not found
        """
        return self.parser.get_element_dictionary().get(pointer)
