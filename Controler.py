import socket
import threading
from Node import Node
from Link import Link
import networkx as nx
import matplotlib.pyplot as plt
import json

# Define a lock for synchronization
lock = threading.Lock()

def write_json(data, filename='data.json'):
    """
    Write a Python dictionary to a JSON file.

    Parameters:
    data (dict): The data to be written to the JSON file.
    filename (str): The name of the JSON file. Default is 'data.json'.
    """
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)

def read_json(filename='data.json'):
    """
    Read a JSON file and return the data as a Python dictionary.

    Parameters:
    filename (str): The name of the JSON file. Default is 'data.json'.

    Returns:
    dict: The data from the JSON file.
    """
    with open(filename, 'r') as file:
        data = json.load(file)
        return data

class Network:
    """
    A class to represent a network of nodes and links.
    """

    def __init__(self):
        """
        Initialize the Network with an empty graph, nodes, and links.
        """
        self.nodes = {}
        self.links = []
        self.graph = nx.Graph()

    def find_shortest_path(self, network, source_name, destination_name, weight='weight'):
        """
        Find the shortest path between two nodes in the network using Dijkstra's algorithm.

        Parameters:
        network (Network): The network object.
        source_name (str): The name of the source node.
        destination_name (str): The name of the destination node.
        weight (str): The weight attribute for the edges. Default is 'weight'.

        Returns:
        list: The shortest path from source to destination.
        """
        try:
            path = nx.dijkstra_path(network.graph, source=source_name, target=destination_name, weight=weight)
            print(f"Shortest path from {source_name} to {destination_name}: {path}")
            return path
        except nx.NetworkXNoPath:
            print(f"No path exists between {source_name} and {destination_name}.")
            return None
        except KeyError as e:
            print(f"Node {e} not found in the network.")
            return None

    def visualize_shortest_path(self, network, source_name, destination_name):
        """
        Visualize the shortest path between two nodes in the network.

        Parameters:
        network (Network): The network object.
        source_name (str): The name of the source node.
        destination_name (str): The name of the destination node.
        """
        path = nx.dijkstra_path(network.graph, source=source_name, target=destination_name)
        pos = nx.spring_layout(network.graph)
        nx.draw(network.graph, pos, with_labels=True, node_color='lightblue', node_size=500, font_size=10, font_weight='bold')
        path_edges = list(zip(path, path[1:]))
        nx.draw_networkx_nodes(network.graph, pos, nodelist=path, node_color='red')
        nx.draw_networkx_edges(network.graph, pos, edgelist=path_edges, edge_color='red', width=2)
        plt.show()

    def compute_all_shortest_paths(self, network):
        """
        Compute all shortest paths in the network and save the routing tables to a JSON file.

        Parameters:
        network (Network): The network object.
        """
        all_paths = dict(nx.all_pairs_dijkstra_path(network.graph))
        routing_tables = {}
        for source, destinations in all_paths.items():
            routing_table = {}
            for destination, path in destinations.items():
                routing_table[destination] = path
            if source in network.nodes:  # Check if the source node exists
                ip, port, node_id = network.get_node_p(source)
                routing_tables[source] = {
                    'ip': ip,
                    'port': port,
                    'node_id': node_id,
                    'routing_table': routing_table
                }
        write_json(routing_tables, 'HSF.json')
        print("Routing tables saved to HSF.json")

    def add_node(self, node_id, name, ip_address=None, port=None, node_type='router'):
        """
        Add a node to the network.

        Parameters:
        node_id (int): The unique identifier for the node.
        name (str): The name of the node.
        ip_address (str): The IP address of the node. Default is None.
        port (int): The port of the node. Default is None.
        node_type (str): The type of the node (e.g., 'router'). Default is 'router'.
        """
        if node_id not in self.nodes:
            self.nodes[node_id] = Node(node_id, name, ip_address, port, node_type)
            self.graph.add_node(name, node_type=node_type)

    def add_link(self, source_id, destination_id, bandwidth):
        """
        Add a link between two nodes in the network.

        Parameters:
        source_id (int): The ID of the source node.
        destination_id (int): The ID of the destination node.
        bandwidth (int): The bandwidth of the link.
        """
        if source_id in self.nodes and destination_id in self.nodes:
            self.links.append(Link(self.nodes[source_id], self.nodes[destination_id], bandwidth))
            self.graph.add_edge(self.nodes[source_id].name, self.nodes[destination_id].name, weight=bandwidth)
        else:
            print("Error: One or both nodes not found in the network.")

    def remove_node(self, node_id):
        """
        Remove a node and its associated links from the network.

        Parameters:
        node_id (int): The ID of the node to be removed.
        """
        if node_id in self.nodes:
            node_name = self.nodes[node_id].name
            self.graph.remove_node(node_name)
            # Remove any links associated with this node
            self.links = [link for link in self.links if link.source.node_id != node_id and link.destination.node_id != node_id]
            del self.nodes[node_id]
            print(f"Node {node_name} and its associated links have been removed from the network.")
        else:
            print(f"Node ID {node_id} not found in the network.")

    def get_node_p(self, node_name):
        """
        Get the IP address, port, and node ID for a given node name.

        Parameters:
        node_name (str): The name of the node.

        Returns:
        tuple: A tuple containing the IP address, port, and node ID of the node.
        """
        for node_id, node in self.nodes.items():
            if node.name == node_name:
                return node.ip_address, node.port, node.node_id
        return None, None, None

    def display_network(self):
        """
        Display the nodes and links in the network.
        """
        print("Nodes in the network:")
        for node in self.nodes.values():
            print(node)
        print("\nLinks in the network:")
        for link in self.links:
            print(link)

    def visualize_network(self):
        """
        Visualize the network graph.
        """
        pos = nx.spring_layout(self.graph)  # positions for all nodes
        nx.draw(self.graph, pos, with_labels=True, node_size=7000, node_color="skyblue", font_size=15, font_weight="bold")
        labels = nx.get_edge_attributes(self.graph, 'weight')
        nx.draw_networkx_edge_labels(self.graph, pos, edge_labels=labels)
        plt.show()

class TCPServer:
    """
    A class to represent a TCP server.
    """

    def __init__(self, host, port):
        """
        Initialize the server with a host address and port.

        Parameters:
        host (str): The host address for the server.
        port (int): The port number for the server.
        """
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = []

    def start(self):
        """
        Start the TCP server and listen for incoming connections.
        """
        # Create a TCP server socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Bind the socket to the address and port
        self.server_socket.bind((self.host, self.port))
        # Listen for incoming connections
        self.server_socket.listen(10)
        print(f"Server listening on {self.host}:{self.port}...")
        while True:
            # Accept a new connection
            client_socket, client_address = self.server_socket.accept()
            print(f"Connection established with {client_address}")
            # Add the client socket to the list of clients
            self.clients.append(client_socket)
            # Start a new thread to handle the client
            client_handler_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_handler_thread.start()




    def handle_client(self, client_socket):
        """
                Handle communication with a connected client.

                Parameters:
                client_socket (socket): The socket connected to the client.
                """

        node_remove = None
        try:
            while True:
                # Receive data from the client
                data = client_socket.recv(1024).decode()
                if not data:
                    break

                # Split the data
                data_split = data.split("-")
                if data_split[0] == 'data':
                    # Process data
                    client_ip = data_split[1]
                    client_port = int(data_split[2])
                    # node_rec = int(data_split[3])
                    # node_cr = data_split[4]
                    # Load routing tables from JSON file
                    data_jsonH = read_json('HSF.json')
                    data_jsonA = read_json('ASK.json')
                    json_dataA = json.dumps(data_jsonA)
                    ip_port_list = []

                    for node_name, node_data in data_jsonH.items():
                        ip_address = node_data.get('ip')
                        port = node_data.get('port')
                        ip_port_list.append((ip_address, port))
                        if ip_address == client_ip and port == client_port:
                            node_client = node_name
                            node_remove = node_data.get('node_id')

                    if (client_ip, client_port) in ip_port_list:
                        client_table = data_jsonH[node_client]['routing_table']
                        ip_table = {}
                        for node_name, path in client_table.items():
                            ip_table[node_name] = [data_jsonH[n]['port'] for n in path]

                        table_send = json.dumps(ip_table)
                        data_all = table_send + " - " + json_dataA
                        client_socket.sendall(data_all.encode())

                    else:
                        print(f"No routing table found for node {client_socket.getpeername()}")

        except Exception as e:
            print(f"Error handling node: {e}")

        finally:
            nsfnet.remove_node(node_remove)
            nsfnet.compute_all_shortest_paths(nsfnet)
            print(f"Node ID {node_remove} not found in the network.")
            self.clients.remove(client_socket)
            client_socket.close()

    def stop(self):
        """""
        Stop the TCP server and close all client connections.
        """
        if self.server_socket:
            self.server_socket.close()
        for client_socket in self.clients:
            client_socket.close()

# Example usage
if __name__ == "__main__":

    nsfnet = Network()
    nsfnet.add_node(1, 'WA',  ip_address='192.168.1.10', port=8000)
    nsfnet.add_node(2, 'CA1', ip_address='192.168.1.11', port=8001)
    nsfnet.add_node(3, 'CA2', ip_address='192.168.1.12', port=8002)
    nsfnet.add_node(4, 'UT',  ip_address='192.168.1.13', port=8003)
    nsfnet.add_node(5, 'CO', ip_address='192.168.1.14', port=8004)
    nsfnet.add_node(6, 'TX', ip_address='192.168.1.15', port=8005)
    nsfnet.add_node(7, 'NE', ip_address='192.168.1.16', port=8006)
    nsfnet.add_node(8, 'IL', ip_address='192.168.1.17', port=8007)
    nsfnet.add_node(9, 'PA', ip_address='192.168.1.18', port=8008)
    nsfnet.add_node(10, 'GA', ip_address='192.168.1.19', port=8009)
    nsfnet.add_node(11, 'MI', ip_address='192.168.1.20', port=8010)
    nsfnet.add_node(12, 'NY', ip_address='192.168.1.21', port=8011)
    nsfnet.add_node(13, 'NJ', ip_address='192.168.1.22', port=8012)
    nsfnet.add_node(14, 'DC', ip_address='192.168.1.23', port=8013)

    for link in [
        (1, 2, 2100), (1, 3, 3000), (1, 8, 4800),
        (2, 1, 2100), (2, 3, 1200), (2, 4, 1500),
        (3, 1, 3000), (3, 2, 1200), (3, 6, 3600),
        (4, 2, 1500), (4, 5, 1200), (4, 11, 3900),
        (5, 4, 1200), (5, 6, 2400), (5, 7, 1200),
        (6, 3, 3600), (6, 5, 2400), (6, 10, 2100), (6, 14, 3600),
        (7, 5, 1200), (7, 8, 1500), (7, 10, 2700),
        (8, 1, 4800), (8, 7, 1500), (8, 9, 1500),
        (9, 8, 1500), (9, 10, 1500), (9, 12, 600), (9, 13, 600),
        (10, 6, 2100), (10, 7, 2700), (10, 9, 1500),
        (11, 4, 3900), (11, 12, 1200), (11, 13, 1500),
        (12, 9, 600), (12, 11, 1200), (12, 14, 600),
        (13, 9, 600), (13, 11, 1500), (13, 14, 300),
        (14, 6, 3600), (14, 12, 600), (14, 13, 300)
    ]:
        nsfnet.add_link(*link)

    # display the network
    #nsfnet.display_network()
    nsfnet.visualize_network()
    nsfnet.compute_all_shortest_paths(nsfnet)


    message = {
        "message": "ASK"
    }
    # Write the example data to 'ASK.json'
    write_json(message, 'ASK.json')

    server = TCPServer("localhost", 8888)
    server.start()