"""
Individual person data model.

This module provides a rich data model for individuals in a family tree,
extracting all relevant information from GEDCOM data.
"""

from typing import List, Dict, Optional, Tuple
import logging

from gedcom.element.individual import IndividualElement
import gedcom.tags


logger = logging.getLogger(__name__)


class Individual:
    """
    Represents an individual person in the family tree.

    This class wraps the GEDCOM IndividualElement and provides convenient
    access to all person data including names, dates, relationships, events,
    images, and notes.
    """

    def __init__(self, element: IndividualElement, gedcom_parser):
        """
        Initialize an Individual from a GEDCOM element.

        Args:
            element: The GEDCOM IndividualElement
            gedcom_parser: The GedcomParser instance for resolving references
        """
        self.element = element
        self.gedcom = gedcom_parser.parser

    def get_id(self) -> str:
        """Get the GEDCOM ID without @ symbols."""
        return self.element.get_pointer().replace('@', '')

    def get_names(self) -> Tuple[str, str]:
        """
        Get the person's names.

        Returns:
            Tuple of (first_name, last_name)
        """
        first, last = self.element.get_name()
        return first.strip(), last.strip()

    def get_full_name(self) -> str:
        """
        Get the full name in 'FirstName LastName' format.

        Returns:
            Full name with proper capitalization
        """
        first, last = self.get_names()
        return f"{first} {last}".strip().title()

    def get_file_name(self) -> str:
        """
        Get the filename for this person's note.

        Format: 'FamilyName FirstName BirthYear'
        If no birth year is known, year is omitted.

        Returns:
            Filename without .md extension
        """
        first, last = self.get_names()
        name_part = f"{last} {first}".strip().title()

        birth_year = self.element.get_birth_year()
        if birth_year != -1:
            return f"{name_part} {birth_year}"
        return name_part

    def get_birth_info(self) -> Dict[str, str]:
        """
        Get birth information.

        Returns:
            Dictionary with 'date', 'place', 'year' keys
        """
        date, place, sources = self.element.get_birth_data()
        year = self.element.get_birth_year()

        return {
            'date': date or '',
            'place': place or '',
            'year': str(year) if year != -1 else ''
        }

    def get_death_info(self) -> Dict[str, str]:
        """
        Get death information.

        Returns:
            Dictionary with 'date', 'place' keys
        """
        date, place, sources = self.element.get_death_data()

        return {
            'date': date or '',
            'place': place or ''
        }

    def get_gender(self) -> str:
        """Get the person's gender (M/F/U)."""
        return self.element.get_gender() or 'U'

    def get_parents(self) -> List['Individual']:
        """
        Get this person's parents.

        Returns:
            List of Individual objects representing parents
        """
        parent_elements = self.gedcom.get_parents(self.element)
        return [Individual(p, type('', (), {'parser': self.gedcom})())
                for p in parent_elements]

    def get_children(self) -> List['Individual']:
        """
        Get this person's children.

        Returns:
            List of Individual objects representing children
        """
        children = []
        for family in self.gedcom.get_families(self.element):
            child_elements = self.gedcom.get_family_members(
                family,
                gedcom.tags.GEDCOM_TAG_CHILD
            )
            for child in child_elements:
                children.append(
                    Individual(child, type('', (), {'parser': self.gedcom})())
                )
        return children

    def get_partners(self) -> List['Individual']:
        """
        Get this person's spouses/partners.

        Returns:
            List of Individual objects representing partners
        """
        partners = []
        for family in self.gedcom.get_families(self.element):
            parent_elements = self.gedcom.get_family_members(
                family,
                'PARENTS'
            )
            for parent in parent_elements:
                # Don't include self
                if parent.get_pointer() != self.element.get_pointer():
                    partners.append(
                        Individual(
                            parent,
                            type('', (), {'parser': self.gedcom})()
                        )
                    )
        return partners

    def get_families(self) -> List[Dict]:
        """
        Get all families this person is part of (as spouse).

        Returns:
            List of dictionaries with family information including:
            - partner: Individual object
            - marriage_date: str
            - marriage_place: str
            - children: List of Individual objects
        """
        families = []
        for family in self.gedcom.get_families(self.element):
            # Get partner
            partners = []
            for parent in self.gedcom.get_family_members(family, 'PARENTS'):
                if parent.get_pointer() != self.element.get_pointer():
                    partners.append(
                        Individual(
                            parent,
                            type('', (), {'parser': self.gedcom})()
                        )
                    )

            # Get marriage info
            marriage_date = ''
            marriage_place = ''
            for child in family.get_child_elements():
                if child.get_tag() == 'MARR':
                    for subchild in child.get_child_elements():
                        if subchild.get_tag() == 'DATE':
                            marriage_date = subchild.get_value()
                        elif subchild.get_tag() == 'PLAC':
                            marriage_place = subchild.get_value()

            # Get children
            children = []
            for child in self.gedcom.get_family_members(
                family,
                gedcom.tags.GEDCOM_TAG_CHILD
            ):
                children.append(
                    Individual(child, type('', (), {'parser': self.gedcom})())
                )

            families.append({
                'partner': partners[0] if partners else None,
                'marriage_date': marriage_date,
                'marriage_place': marriage_place,
                'children': children
            })

        return families

    def get_events(self) -> List[Dict[str, str]]:
        """
        Get all life events for this person.

        Returns:
            List of dictionaries with 'type', 'date', 'place' keys
        """
        events = []

        for child in self.element.get_child_elements():
            tag = child.get_tag()

            # Common event tags
            if tag in ['BIRT', 'DEAT', 'MARR', 'OCCU', 'EDUC', 'RESI', 'BURI']:
                event = {
                    'type': tag,
                    'date': '',
                    'place': '',
                    'details': child.get_value() or ''
                }

                # Extract date and place
                for subchild in child.get_child_elements():
                    if subchild.get_tag() == 'DATE':
                        event['date'] = subchild.get_value()
                    elif subchild.get_tag() == 'PLAC':
                        event['place'] = subchild.get_value()

                events.append(event)

        return events

    def get_images(self) -> List[str]:
        """
        Get all image/media references for this person.

        Returns:
            List of image reference IDs
        """
        images = []

        for child in self.element.get_child_elements():
            if child.get_tag() == 'OBJE':
                # OBJE can have a reference or inline data
                reference = child.get_value()
                if reference:
                    images.append(reference)

        return images

    def get_notes(self) -> List[str]:
        """
        Get all notes for this person.

        Returns:
            List of note texts
        """
        notes = []

        for child in self.element.get_child_elements():
            if child.get_tag() == 'NOTE':
                note_text = child.get_value() or ''

                # If note_text starts with @, it's a reference to a NOTE record
                if note_text.startswith('@') and note_text.endswith('@'):
                    # Resolve the reference
                    note_element = self.gedcom.get_element_dictionary().get(
                        note_text
                    )
                    if note_element:
                        # Get the note text from the NOTE element
                        note_text = note_element.get_value() or ''

                        # Get continued text from the NOTE record
                        for subchild in note_element.get_child_elements():
                            if subchild.get_tag() in ['CONT', 'CONC']:
                                note_text += '\n' + (subchild.get_value() or '')
                else:
                    # Inline note - check for continued text in subchilds
                    for subchild in child.get_child_elements():
                        if subchild.get_tag() in ['CONT', 'CONC']:
                            note_text += '\n' + (subchild.get_value() or '')

                if note_text and not note_text.startswith('@'):
                    notes.append(note_text.strip())

        return notes

    def get_stories(self) -> List[Dict]:
        """
        Get stories/narratives for this person.

        Some genealogy programs (like MobileFamilyTree) use custom _STO
        tags for storing longer narratives and stories about individuals.

        Returns:
            List of dictionaries with 'title', 'sections' keys
            Each section has 'subtitle', 'text', 'images'
        """
        stories = []

        for child in self.element.get_child_elements():
            if child.get_tag() == '_STO':
                story_ref = child.get_value()

                if story_ref and story_ref.startswith('@'):
                    # Resolve the story reference
                    story_element = self.gedcom.get_element_dictionary().get(
                        story_ref
                    )
                    if story_element:
                        story = {
                            'title': '',
                            'description': '',
                            'sections': []
                        }

                        # Get main title and metadata
                        for section in story_element.get_child_elements():
                            tag = section.get_tag()

                            if tag == 'TITL':
                                story['title'] = section.get_value() or ''
                            elif tag == 'DESC':
                                story['description'] = section.get_value() or ''
                            elif tag == '_STS':
                                # Story section with inline content
                                # Format: "1 @12375128@ _STS"
                                # Children at level 2 contain TITL, TEXT, OBJE
                                section_data = {
                                    'subtitle': '',
                                    'text': '',
                                    'images': []
                                }

                                # Extract content directly from child elements
                                for sts_child in section.get_child_elements():
                                    if sts_child.get_tag() == 'TITL':
                                        section_data['subtitle'] = sts_child.get_value() or ''
                                    elif sts_child.get_tag() == 'TEXT':
                                        text = sts_child.get_value() or ''
                                        # Get CONT lines
                                        for cont in sts_child.get_child_elements():
                                            if cont.get_tag() in ['CONT', 'CONC']:
                                                text += '\n' + (cont.get_value() or '')
                                        section_data['text'] = text
                                    elif sts_child.get_tag() == 'OBJE':
                                        # Get image reference
                                        img_ref = sts_child.get_value()
                                        if img_ref:
                                            section_data['images'].append(img_ref)

                                if section_data['subtitle'] or section_data['text']:
                                    story['sections'].append(section_data)

                        if story['title'] or story['sections']:
                            stories.append(story)

        return stories

    def get_attributes(self) -> Dict[str, str]:
        """
        Get physical attributes and other personal details.

        Returns:
            Dictionary with attribute names as keys
        """
        attributes = {}

        for child in self.element.get_child_elements():
            tag = child.get_tag()

            # Physical attributes
            if tag in ['EYES', 'HAIR', 'HEIG']:
                attributes[tag.lower()] = child.get_value() or ''

        return attributes
