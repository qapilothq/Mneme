from platform import node
import networkx as nx
from lxml import etree
from xml_utils import check_if_element_is_ad, check_if_element_is_external, calculate_heuristic_score
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class UITree:
    def __init__(self, request_id, xml: str):
        """
        Initialize analyzer with screenshot and layout information
        
        Args:
            base64_screenshot: Base64 encoded screenshot image
            layout_xml: String containing the XML layout of the screen
        """
        self.logger = logging.getLogger(__name__)
        self.request_id = request_id
        self.xml =  xml
        # Initialize a counter for node IDs
        self.node_counter = [0]  # Use a list to allow modification within the nested function
        
        # Parse inputs
        self.root = etree.fromstring(xml.encode('utf-8'))
        self.ui_element_dict_original = dict() # node_id -> metadata dict
        self.ui_element_dict_processed = dict() # node_id -> metadata dict
        self.graph = nx.DiGraph()
        self.create_graph(self.root) # Start the recursive addition from the root
        logging.info(f"requestid :: {self.request_id} :: Creation of graph done :: Number of nodes -- {len(list(self.graph.nodes))}")
        self.update_processed_ui_element_dict()

    def create_graph(self, node, parent_id=None):

        """
        Recursively add nodes and edges to the graph.
        
        Args:
        - node: Current XML node.
        - parent_id: ID of the parent node.
        """

        # Create a directed graph
        # G = nx.DiGraph()
        # Use the current value of node_counter as the node_id
        node_id = self.node_counter[0]
        
        # Increment the counter for the next node
        self.node_counter[0] += 1

        # Add the node to the graph with its attributes
        self.graph.add_node(node_id, tag=node.tag, attributes=node.attrib)
        
        # If there's a parent, add an edge from parent to this node
        if parent_id is not None:
            self.graph.add_edge(parent_id, node_id)

        node_description = (node.attrib.get('text', '') + " " + node.attrib.get('content-desc', '')).strip()
        if not node_description:
            node_description =  node.attrib.get('resource-id', '').strip()
        attributes = dict(node.attrib)
        attributes['tag'] = node.tag
        # attributes['xpath'] = get_xpath(node)
        attributes['content_desc'] = attributes.get('content-desc', '')
        attributes['resource_id'] = attributes.get('resource-id', '')
        attributes.pop('content-desc', None)
        attributes.pop('resource-id', None)
        ui_element = {
            'node_id': node_id,
            'description': node_description,
            'attributes' : attributes,
            # 'is_external': check_if_element_is_external(node),
            # 'is_ad': check_if_element_is_ad(node)
        }

        ui_element['heuristic_score'] = calculate_heuristic_score(node_id=node_id, node_data=ui_element)

        self.ui_element_dict_original[node_id] = ui_element
        self.ui_element_dict_processed[node_id] = ui_element
        
        # Recursively add children
        for child in node:
            self.create_graph(child, parent_id=node_id)

        

    def update_processed_ui_element_dict(self):
        fields_to_check = ["content_desc", "resource_id", "text"]
        boolean_fields_to_check = ["clickable", "checkable", "checked", "enabled", "focusable", "focused", "long-clickable", "displayed", "scrollable", "selected"]
        for node_id in self.graph.nodes():
            self.update_field_using_parent(ui_element=self.ui_element_dict_processed.get(node_id), fields_to_check=fields_to_check)
            self.update_boolean_field_using_parent(ui_element=self.ui_element_dict_processed.get(node_id), boolean_fields_to_check=boolean_fields_to_check)
            ui_element_processed = self.ui_element_dict_processed.get(node_id)
            if ui_element_processed:
                # Recalculate heuristic score
                ui_element_processed['description'] = (ui_element_processed.get('attributes').get('text', '') + " " + ui_element_processed.get('attributes').get('content_desc', '')).strip()
                if not ui_element_processed['description']:
                    ui_element_processed['description'] =  ui_element_processed.get('attributes').get('resource_id', '').strip()
                ui_element_processed['heuristic_score'] = calculate_heuristic_score(node_id, ui_element_processed)
                ui_element_processed.get('attributes')['xpath'] = self.get_xpath(node_id=ui_element_processed.get('node_id', None))
                
                # Add to ui_element_dict
                self.ui_element_dict_processed[node_id] = ui_element_processed

    def update_field_using_parent(self, ui_element, fields_to_check, max_levels=1):
        node_id = ui_element.get("node_id", None)
        if node_id is None:
            return ui_element
        else:
            current_node_id = node_id
            levels_checked = 0
            updated_node_attributes = self.ui_element_dict_processed[node_id].get("attributes", {})

            while levels_checked < max_levels:
                parent_node_id = self.get_parent(node_id=current_node_id)
                if parent_node_id is None:
                    break  # No more ancestors

                parent_ui_element = self.ui_element_dict_processed.get(parent_node_id)
                if parent_ui_element:
                    parent_node_attributes = parent_ui_element.get("attributes", {})
                    for field in fields_to_check:
                        if not updated_node_attributes.get(field):
                            parent_value = parent_node_attributes.get(field)
                            if parent_value:
                                updated_node_attributes[field] = parent_value
                                break  # Break the loop once a non-empty value is found

                current_node_id = parent_node_id
                levels_checked += 1

            # Update the node's attributes in the dictionary
            self.ui_element_dict_processed[node_id]["attributes"] = updated_node_attributes

    def update_boolean_field_using_parent(self, ui_element, boolean_fields_to_check, max_levels=1):
        node_id = ui_element.get("node_id", None)
        if node_id is None:
            return ui_element
        else:
            current_node_id = node_id
            levels_checked = 0
            updated_node_attributes = ui_element.get("attributes", {})

            while levels_checked < max_levels:
                parent_node_id = self.get_parent(node_id=current_node_id)
                if parent_node_id is None:
                    break  # No more ancestors

                parent_ui_element = self.ui_element_dict_processed.get(parent_node_id)
                if parent_ui_element:
                    parent_node_attributes = parent_ui_element.get("attributes", {})
                    for field in boolean_fields_to_check:
                        if not updated_node_attributes.get(field) and not updated_node_attributes.get(field):
                            node_value = updated_node_attributes.get(field)
                            parent_value = parent_node_attributes.get(field)
                            if parent_value == "true" and node_value == "false":
                                updated_node_attributes[field] = parent_value
                                break  # Break the loop once a non-empty value is found

                current_node_id = parent_node_id
                levels_checked += 1

            # Update the node's attributes in the dictionary
            self.ui_element_dict_processed[node_id]["attributes"] = updated_node_attributes

    def get_xpath(self, node_id):
        path = []
        current_node = node_id

        while current_node is not None:
            node_data = self.graph.nodes[current_node]
            tag = node_data['tag']
            parent = list(self.graph.predecessors(current_node))
            
            # Determine the index of the current node among its siblings
            if parent:
                siblings = [n for n in self.graph.successors(parent[0]) if self.graph.nodes[n]['tag'] == tag]
                index = siblings.index(current_node) + 1
                path.append(f"{tag}[{index}]")
                current_node = parent[0]
            else:
                path.append(tag)
                current_node = None

        return '/' + '/'.join(reversed(path))

    # Function to get the parent of a node
    def get_parent(self, node_id):
        # Get the list of predecessors (parents)
        parents = list(self.graph.predecessors(node_id))
        # Return the first parent if it exists
        return parents[0] if parents else None
    
    # Function to get the children of a node
    def get_children(self, node_id):
        # Get the list of successors (children)
        return list(self.graph.successors(node_id))

    # Function to get node data by node ID
    def get_node_data(self, node_id):
        if node_id in self.graph:
            return self.graph.nodes[node_id]
        else:
            return None


