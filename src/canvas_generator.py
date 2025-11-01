"""
Canvas generator for creating Obsidian Canvas family trees.

This module generates JSON Canvas files that visualize family relationships
from GEDCOM data in a generational tree layout compatible with Obsidian.
"""

import json
import logging
import os
import uuid
from typing import List, Dict, Tuple
from collections import defaultdict, deque
from individual import Individual


logger = logging.getLogger(__name__)


class CanvasGenerator:
    """Generates Obsidian Canvas files for family tree visualization."""

    # Layout constants
    NODE_WIDTH = 250
    NODE_BASE_HEIGHT = 60  # Base height, will grow with content
    HORIZONTAL_SPACING = 100
    VERTICAL_SPACING = 200
    IMAGE_HEIGHT = 150  # Height for nodes with images
    TREE_SPACING = 400  # Space between disconnected trees

    def __init__(self, individuals: List[Individual], output_dir: str):
        """
        Initialize the canvas generator.

        Args:
            individuals: List of all individuals from GEDCOM
            output_dir: Directory where canvas file will be saved
        """
        self.individuals = individuals
        self.output_dir = output_dir

        # Create lookup dictionary for fast access
        self.individual_map: Dict[str, Individual] = {
            ind.get_pointer(): ind for ind in individuals
        }

        # Canvas data structures
        self.nodes: List[Dict] = []
        self.edges: List[Dict] = []

        logger.info(f"Initialized CanvasGenerator with {len(individuals)} individuals")

    def generate_canvas(self, root_person_id: str, canvas_filename: str = "Family Tree.canvas") -> str:
        """
        Generate canvas file with family tree visualization.

        Args:
            root_person_id: GEDCOM pointer of the root person
            canvas_filename: Name of the output canvas file

        Returns:
            Path to the generated canvas file
        """
        logger.info(f"Generating canvas with root person: {root_person_id}")

        # Build family tree structure starting from root
        tree_structure = self._build_tree_structure(root_person_id)

        # Calculate node positions using generational layout
        positioned_nodes = self._calculate_positions(tree_structure)

        # Create canvas nodes and edges
        self._create_canvas_elements(positioned_nodes, tree_structure)

        # Find and add disconnected family trees
        self._add_disconnected_trees(tree_structure)

        # Write canvas file
        canvas_path = os.path.join(self.output_dir, canvas_filename)
        self._write_canvas_file(canvas_path)

        logger.info(f"Canvas generated with {len(self.nodes)} nodes and {len(self.edges)} edges")
        return canvas_path

    def _build_tree_structure(self, root_id: str) -> Dict[str, Dict]:
        """
        Build tree structure starting from root person using BFS.

        Returns a dict mapping person_id -> {
            'individual': Individual,
            'generation': int,
            'spouses': List[str],
            'children': List[str],
            'parents': List[str]
        }
        """
        structure = {}
        visited = set()
        queue = deque([(root_id, 0)])  # (person_id, generation)

        while queue:
            person_id, generation = queue.popleft()

            if person_id in visited or person_id not in self.individual_map:
                continue

            visited.add(person_id)
            individual = self.individual_map[person_id]

            # Initialize structure for this person
            structure[person_id] = {
                'individual': individual,
                'generation': generation,
                'spouses': [],
                'children': [],
                'parents': []
            }

            # Get families where this person is a child (to find parents)
            families_as_child = individual.get_families_as_child()
            for family in families_as_child:
                # Add parents
                if family.get('father'):
                    father_id = family['father']
                    structure[person_id]['parents'].append(father_id)
                    if father_id not in visited:
                        queue.append((father_id, generation - 1))

                if family.get('mother'):
                    mother_id = family['mother']
                    structure[person_id]['parents'].append(mother_id)
                    if mother_id not in visited:
                        queue.append((mother_id, generation - 1))

            # Get families where this person is a spouse (to find spouses and children)
            families = individual.get_families()
            for family in families:
                # Add spouse
                partner = family.get('partner')
                if partner:
                    spouse_id = partner.get_pointer()
                    if spouse_id and spouse_id not in structure[person_id]['spouses']:
                        structure[person_id]['spouses'].append(spouse_id)
                        if spouse_id not in visited:
                            queue.append((spouse_id, generation))

                # Add children
                children = family.get('children', [])
                for child in children:
                    child_id = child.get_pointer()
                    if child_id and child_id not in structure[person_id]['children']:
                        structure[person_id]['children'].append(child_id)
                        if child_id not in visited:
                            queue.append((child_id, generation + 1))

        logger.info(f"Built tree structure with {len(structure)} people from root {root_id}")
        return structure

    def _calculate_positions(self, tree_structure: Dict[str, Dict]) -> Dict[str, Tuple[int, int]]:
        """
        Calculate x, y positions for each person using generational layout.

        Returns dict mapping person_id -> (x, y)
        """
        # Group people by generation
        generations: Dict[int, List[str]] = defaultdict(list)
        for person_id, data in tree_structure.items():
            generations[data['generation']].append(person_id)

        positions = {}
        min_gen = min(generations.keys()) if generations else 0
        max_gen = max(generations.keys()) if generations else 0

        # Calculate positions generation by generation
        for gen in range(min_gen, max_gen + 1):
            people_in_gen = generations.get(gen, [])

            # Sort by last name for consistent positioning
            people_in_gen.sort(key=lambda pid: self.individual_map[pid].get_names()[1] or "")

            # Calculate Y position (vertical, based on generation)
            y_pos = gen * (self.NODE_BASE_HEIGHT + self.VERTICAL_SPACING)

            # Calculate X positions (horizontal, evenly spaced)
            total_width = len(people_in_gen) * self.NODE_WIDTH + (len(people_in_gen) - 1) * self.HORIZONTAL_SPACING
            start_x = -(total_width // 2)  # Center the generation

            for idx, person_id in enumerate(people_in_gen):
                x_pos = start_x + idx * (self.NODE_WIDTH + self.HORIZONTAL_SPACING)
                positions[person_id] = (x_pos, y_pos)

        return positions

    def _create_canvas_elements(self, positions: Dict[str, Tuple[int, int]], tree_structure: Dict[str, Dict]):
        """
        Create canvas nodes and edges from positioned tree structure.
        """
        node_ids = {}  # Map person_id -> canvas node_id

        # Create nodes
        for person_id, (x, y) in positions.items():
            individual = tree_structure[person_id]['individual']
            node_id = self._create_node(individual, x, y)
            node_ids[person_id] = node_id

        # Create edges
        for person_id, data in tree_structure.items():
            from_node_id = node_ids.get(person_id)
            if not from_node_id:
                continue

            # Create parent-child edges
            for child_id in data['children']:
                to_node_id = node_ids.get(child_id)
                if to_node_id:
                    self._create_edge(from_node_id, to_node_id, "Child", "bottom", "top")

            # Create spouse edges
            for spouse_id in data['spouses']:
                to_node_id = node_ids.get(spouse_id)
                if to_node_id:
                    # Only create edge once (from lower ID to higher ID to avoid duplicates)
                    if person_id < spouse_id:
                        self._create_edge(from_node_id, to_node_id, "Spouse", "right", "left")

    def _add_disconnected_trees(self, main_tree: Dict[str, Dict]):
        """
        Find individuals not in main tree and create separate tree groups.
        """
        connected_ids = set(main_tree.keys())
        disconnected_ids = set(self.individual_map.keys()) - connected_ids

        if not disconnected_ids:
            logger.info("No disconnected family trees found")
            return

        logger.info(f"Found {len(disconnected_ids)} people in disconnected trees")

        # Find separate tree roots (people with no parents in the disconnected set)
        tree_roots = []

        for person_id in disconnected_ids:
            individual = self.individual_map[person_id]
            families_as_child = individual.get_families_as_child()

            has_parent_in_disconnected = False
            for family in families_as_child:
                father_id = family.get('father')
                mother_id = family.get('mother')
                if (father_id and father_id in disconnected_ids) or (mother_id and mother_id in disconnected_ids):
                    has_parent_in_disconnected = True
                    break

            if not has_parent_in_disconnected:
                tree_roots.append(person_id)

        logger.info(f"Found {len(tree_roots)} disconnected tree roots")

        # Calculate offset for disconnected trees
        # Place them to the right of the main tree
        if self.nodes:
            max_x = max(node['x'] + node['width'] for node in self.nodes)
            offset_x = max_x + self.TREE_SPACING
        else:
            offset_x = 0

        # Build and position each disconnected tree
        for root_id in tree_roots:
            if root_id not in disconnected_ids:
                continue  # Already processed

            # Build tree structure for this root
            tree_structure = self._build_tree_structure(root_id)

            # Update disconnected_ids to track what we've processed
            disconnected_ids -= set(tree_structure.keys())

            # Calculate positions
            positions = self._calculate_positions(tree_structure)

            # Offset positions
            offset_positions = {
                pid: (x + offset_x, y) for pid, (x, y) in positions.items()
            }

            # Create nodes and edges
            self._create_canvas_elements(offset_positions, tree_structure)

            # Update offset for next tree
            if offset_positions:
                max_x_in_tree = max(x + self.NODE_WIDTH for x, y in offset_positions.values())
                offset_x = max_x_in_tree + self.TREE_SPACING

    def _create_node(self, individual: Individual, x: int, y: int) -> str:
        """
        Create a canvas node for an individual.

        Returns the node ID.
        """
        node_id = str(uuid.uuid4().hex[:16])
        first_name, last_name = individual.get_names()

        # Get filename (same logic as in markdown generator)
        birth_year = ""
        events = individual.get_events()
        for event in events:
            if event["type"] == "BIRT" and event.get("date"):
                import re
                year_match = re.search(r'\b(\d{4})\b', event["date"])
                if year_match:
                    birth_year = year_match.group(1)
                    break

        # Build filename for WikiLink
        filename_parts = []
        if last_name:
            filename_parts.append(last_name)
        if first_name:
            filename_parts.append(first_name)
        if birth_year:
            filename_parts.append(birth_year)
        filename = " ".join(filename_parts)

        # Get images
        images = individual.get_images()
        has_image = len(images) > 0

        # Build node text content
        text_parts = []

        # Add image if available (use first image)
        if has_image:
            # images is a list of dicts with 'file', 'title', 'format' keys
            image_file = images[0].get('file', '')
            if image_file:
                text_parts.append(f"![Image]({image_file})")

        # Add WikiLink to person's markdown file
        text_parts.append(f"[[{filename}]]")

        node_text = "\n".join(text_parts)

        # Calculate height based on content
        height = self.IMAGE_HEIGHT if has_image else self.NODE_BASE_HEIGHT

        node = {
            "id": node_id,
            "type": "text",
            "text": node_text,
            "x": x,
            "y": y,
            "width": self.NODE_WIDTH,
            "height": height
        }

        self.nodes.append(node)
        return node_id

    def _create_edge(self, from_node: str, to_node: str, label: str,
                     from_side: str = "bottom", to_side: str = "top"):
        """
        Create a canvas edge between two nodes.
        """
        edge_id = str(uuid.uuid4().hex[:16])

        edge = {
            "id": edge_id,
            "fromNode": from_node,
            "fromSide": from_side,
            "toNode": to_node,
            "toSide": to_side,
            "label": label
        }

        self.edges.append(edge)

    def _write_canvas_file(self, canvas_path: str):
        """
        Write canvas data to JSON file.
        """
        canvas_data = {
            "nodes": self.nodes,
            "edges": self.edges
        }

        with open(canvas_path, 'w', encoding='utf-8') as f:
            json.dump(canvas_data, f, indent="\t")

        logger.info(f"Canvas file written to: {canvas_path}")
