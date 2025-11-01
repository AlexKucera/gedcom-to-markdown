"""
Markdown note generator for Obsidian.

This module generates Obsidian-compatible markdown notes for individuals
in the family tree.
"""

from pathlib import Path
from typing import List
import logging

from individual import Individual


logger = logging.getLogger(__name__)


class MarkdownGenerator:
    """
    Generates Obsidian markdown notes for individuals.

    This class handles formatting individual data into Obsidian-compatible
    markdown with WikiLinks and metadata.
    """

    def __init__(self, output_dir: Path, media_subdir: str = ''):
        """
        Initialize the generator.

        Args:
            output_dir: Directory where markdown files will be created
            media_subdir: Subdirectory for media files (e.g., 'images')

        Raises:
            ValueError: If output_dir doesn't exist or isn't a directory
        """
        if not output_dir.exists():
            raise ValueError(f"Output directory doesn't exist: {output_dir}")
        if not output_dir.is_dir():
            raise ValueError(f"Output path is not a directory: {output_dir}")

        self.output_dir = output_dir
        self.media_subdir = media_subdir

    def generate_note(self, individual: Individual) -> Path:
        """
        Generate a markdown note for an individual.

        Args:
            individual: The Individual to create a note for

        Returns:
            Path to the created markdown file
        """
        filename = individual.get_file_name() + '.md'
        file_path = self.output_dir / filename

        logger.info(f"Generating note: {filename}")

        with open(file_path, 'w', encoding='utf-8') as f:
            # Write all sections
            self._write_header(f, individual)
            self._write_attributes(f, individual)
            self._write_events(f, individual)
            self._write_families(f, individual)
            self._write_parents(f, individual)
            self._write_children(f, individual)
            self._write_images(f, individual)
            self._write_notes(f, individual)

        return file_path

    def _write_header(self, f, individual: Individual):
        """Write the note header with main name."""
        f.write(f"# {individual.get_full_name()}\n\n")

    def _write_attributes(self, f, individual: Individual):
        """Write basic attributes section."""
        f.write("## Attributes\n")

        birth = individual.get_birth_info()
        death = individual.get_death_info()

        self._write_metadata(f, 'ID', individual.get_id())
        self._write_metadata(f, 'Name', individual.get_full_name())

        # Lived years
        lived = f"{birth['year']}-{death['date'][:4] if death['date'] else ''}"
        self._write_metadata(f, 'Lived', lived)

        self._write_metadata(f, 'Sex', individual.get_gender())

        # Birth details
        if birth['date']:
            self._write_metadata(f, 'Born', birth['date'])
        if birth['place']:
            self._write_metadata(f, 'Place of birth', birth['place'])

        # Death details
        if death['date']:
            self._write_metadata(f, 'Passed away', death['date'])
        if death['place']:
            self._write_metadata(f, 'Place of death', death['place'])

        # Physical attributes
        attrs = individual.get_attributes()
        for key, value in attrs.items():
            if value:
                self._write_metadata(f, key.capitalize(), value)

        f.write('\n')

    def _write_events(self, f, individual: Individual):
        """Write life events section."""
        events = individual.get_events()

        # Filter out birth and death (already in attributes)
        other_events = [e for e in events
                        if e['type'] not in ['BIRT', 'DEAT']]

        if not other_events:
            return

        f.write("## Life Events\n")

        event_names = {
            'MARR': 'Marriage',
            'OCCU': 'Occupation',
            'EDUC': 'Education',
            'RESI': 'Residence',
            'BURI': 'Burial'
        }

        for event in other_events:
            event_type = event_names.get(event['type'], event['type'])
            f.write(f"### {event_type}\n")

            if event['date']:
                f.write(f"- **Date**: {event['date']}\n")
            if event['place']:
                f.write(f"- **Place**: {event['place']}\n")
            if event['details']:
                f.write(f"- **Details**: {event['details']}\n")

            f.write('\n')

        f.write('\n')

    def _write_families(self, f, individual: Individual):
        """Write families/marriages section."""
        families = individual.get_families()

        if not families:
            return

        f.write("## Families\n")

        for i, family in enumerate(families, 1):
            if family['partner']:
                partner_name = family['partner'].get_file_name()
                f.write(f"### Marriage {i if len(families) > 1 else ''}\n")
                self._write_metadata_hidden(
                    f,
                    'Partner',
                    self._wiki_link(partner_name)
                )

                if family['marriage_date']:
                    self._write_metadata_hidden(
                        f,
                        'Marriage date',
                        family['marriage_date']
                    )
                if family['marriage_place']:
                    self._write_metadata_hidden(
                        f,
                        'Marriage place',
                        family['marriage_place']
                    )

                if family['children']:
                    f.write('\n**Children:**\n')
                    for child in family['children']:
                        self._write_metadata_hidden(
                            f,
                            'Child',
                            self._wiki_link(child.get_file_name())
                        )

                f.write('\n')

        f.write('\n')

    def _write_parents(self, f, individual: Individual):
        """Write parents section."""
        parents = individual.get_parents()

        if not parents:
            return

        f.write("## Parents\n")

        for parent in parents:
            self._write_metadata_hidden(
                f,
                'Parent',
                self._wiki_link(parent.get_file_name())
            )

        f.write('\n')

    def _write_children(self, f, individual: Individual):
        """Write children section (if not already in families)."""
        # Skip if we already wrote families section
        if individual.get_families():
            return

        children = individual.get_children()

        if not children:
            return

        f.write("## Children\n")

        for child in children:
            self._write_metadata_hidden(
                f,
                'Child',
                self._wiki_link(child.get_file_name())
            )

        f.write('\n')

    def _write_images(self, f, individual: Individual):
        """Write images section."""
        images = individual.get_images()

        if not images:
            return

        f.write("## Images\n")

        for image in images:
            title = image['title'] if image['title'] else 'Image'
            filename = image['file']
            # Add media subdirectory prefix if specified
            if self.media_subdir:
                image_path = f"{self.media_subdir}/{filename}"
            else:
                image_path = filename
            f.write(f"![{title}]({image_path})\n\n")

        f.write('\n')

    def _write_notes(self, f, individual: Individual):
        """Write notes section."""
        notes = individual.get_notes()
        stories = individual.get_stories()

        if not notes and not stories:
            return

        f.write("## Notes\n")

        # Write regular notes
        for note in notes:
            f.write(f"{note}\n\n")

        # Write stories with their sections
        for story in stories:
            if story['title']:
                f.write(f"### {story['title']}\n\n")

            if story['description']:
                f.write(f"*{story['description']}*\n\n")

            # Write each section
            for section in story['sections']:
                if section['subtitle']:
                    f.write(f"#### {section['subtitle']}\n\n")

                if section['text']:
                    f.write(f"{section['text']}\n\n")

                # Write images for this section
                if section['images']:
                    for img in section['images']:
                        title = img['title'] if img['title'] else 'Image'
                        filename = img['file']
                        # Add media subdirectory prefix if specified
                        if self.media_subdir:
                            image_path = f"{self.media_subdir}/{filename}"
                        else:
                            image_path = filename
                        f.write(f"![{title}]({image_path})\n\n")

        f.write('\n')

    def _write_metadata(self, f, key: str, value: str):
        """Write visible Obsidian metadata."""
        f.write(f"[{key}:: {value}]\n")

    def _write_metadata_hidden(self, f, key: str, value: str):
        """Write hidden Obsidian metadata."""
        f.write(f"({key}:: {value})\n")

    def _wiki_link(self, text: str) -> str:
        """Format text as a WikiLink."""
        return f"[[{text}]]"

    def generate_all(self, individuals: List[Individual]) -> List[Path]:
        """
        Generate notes for all individuals.

        Args:
            individuals: List of Individual objects

        Returns:
            List of paths to created files
        """
        logger.info(f"Generating notes for {len(individuals)} individuals")

        paths = []
        for individual in individuals:
            try:
                path = self.generate_note(individual)
                paths.append(path)
            except Exception as e:
                logger.error(
                    f"Failed to generate note for "
                    f"{individual.get_full_name()}: {e}"
                )

        logger.info(f"Successfully generated {len(paths)} notes")
        return paths
