import socket
import threading
import json
import time
from Controler import Network

nsfnet = Network()


class TCPClient:
    def __init__(self, server_host, server_port, client_ip, client_port, node_id, controller_host, controller_port):
        self.server_host = server_host
        self.server_port = server_port
        self.client_ip = client_ip
        self.client_port = client_port
        self.node_id = node_id
        self.controller_host = controller_host
        self.controller_port = controller_port
        self.client_socket = None
        self.routing_table = {}
        self.server_thread = None

    def connect_to_controller(self):
        """
        Connects to the controller, receives the routing table, and starts a thread to send messages.
        """
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.server_host, self.server_port))
            print(f"Connected to controller at {self.server_host}:{self.server_port}")

            # Start a thread for sending messages to the controller
            send_thread = threading.Thread(target=self.send_messages)
            send_thread.start()

            while True:
                # Receive the routing table from the controller
                data = self.client_socket.recv(4096).decode()
                json_parts = data.split(' - ')
                json_obj1 = json_parts[0]
                self.routing_table = json.loads(json_obj1)  # Convert the JSON string to a Python dictionary
                print(f"Received routing table: {self.routing_table}")

        except Exception as e:
            print(f"Error connecting to controller: {e}")

    def send_to_controller(self, data):
        """
        Sends data to the controller.

        Parameters:
        data (str): The data to be sent to the controller.
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as controller_socket:
                controller_socket.connect((self.controller_host, self.controller_port))
                controller_socket.sendall(data.encode())
                print(f"Sent data to controller at {self.controller_host}:{self.controller_port}")
        except Exception as e:
            print(f"Error sending data to controller: {e}")

    def send_messages(self):
        """
        Continuously sends requests to the controller for the routing table.
        """
        while True:
            # Send a request to the controller for the routing table
            request = f"data-{self.client_ip}-{self.client_port}-{self.node_id}"
            self.client_socket.sendall(request.encode())
            time.sleep(5)  # Wait 5 seconds before sending the next request


class TCPServer:
    def __init__(self, host, port, controller_host, controller_port, tcp_client):
        self.host = host
        self.port = port
        self.controller_host = controller_host
        self.controller_port = controller_port
        self.server_socket = None
        self.tcp_client = tcp_client
        self.routing_table = tcp_client.routing_table  # Reference to the routing table from the client
        self.host_socket = None

    def start(self):
        """
        Starts the server to listen for incoming connections.
        """
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Server listening on {self.host}:{self.port}...")
        while True:
            client_socket, client_address = self.server_socket.accept()
            print(f"Connection established with {client_address}")
            self.host_socket = client_socket  # Update the host_socket reference
            client_handler_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_handler_thread.start()

    def handle_client(self, client_socket):
        """
        Handles communication with a connected client.

        Parameters:
        client_socket (socket.socket): The socket connected to the client.
        """
        try:
            while True:
                data = client_socket.recv(1024).decode()
                if not data:
                    break

                data_split = data.split("-")
                data_port = int(data_split[1])
                data_source = data_split[3]
                print(data_source)
                routing_table = self.tcp_client.routing_table

                # Busca el nodo correspondiente en la tabla de enrutamiento
                for node_data, ports in routing_table.items():
                    if data_port in ports:
                        # Encontró el nodo, ahora envía el mensaje
                        data_split = data.split("-")
                        data_port = data_split[1] if len(data_split) > 1 else None
                        next_hop = self.determine_next_hop(data_port)
                        print(f"Next hop for data {data_split[0]} is {next_hop}")
                        if next_hop:
                            self.forward_data(next_hop, data)
                        else:
                            # If next_hop is None, it means the data has reached its destination node
                            print(f"Send message to host.")
                            # View
                            nsfnet.find_shortest_path(nsfnet, data_source, "WA")
                            nsfnet.visualize_shortest_path(nsfnet, data_source, "WA")
                            # Enviar al host conectado
                            self.send_to_host(data, client_socket)

        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            client_socket.close()

    def determine_next_hop(self, destination_port):
        """
        Determines the next hop for the given destination port using the routing table.

        Parameters:
        destination_port (int): The destination port.

        Returns:
        tuple or None: The next hop information or None if the destination is reached.
        """
        try:
            routing_table = self.tcp_client.routing_table

            for indicator, path in routing_table.items():
                if str(destination_port) == str(path[-1]):
                    next_hop_index = path.index(int(self.port)) + 1 if int(self.port) in path else 0
                    if next_hop_index < len(path):
                        next_hop_port = path[next_hop_index]
                        return indicator, [next_hop_port]
                    else:
                        return None
        except Exception as e:
            print(f"Error determining next hop: {e}")
            return None

    def forward_data(self, next_hop, data):
        """
        Forwards data to the next hop.

        Parameters:
        next_hop (tuple): The next hop information.
        data (str): The data to be forwarded.
        """
        try:
            if next_hop:
                next_hop_ip = 'localhost'  # Assuming localhost for simplicity
                next_hop_port = next_hop[1][0]  # The next hop port
                print(next_hop_port)
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as next_hop_socket:
                    next_hop_socket.connect((next_hop_ip, next_hop_port))
                    next_hop_socket.sendall(data.encode())
                    print(f"Forwarded data to next hop {next_hop}")
            else:
                print("Next hop not found")
        except Exception as e:
            print(f"Error forwarding data to next hop: {e}")

    def send_to_host(self, data, client_socket):
        """
        Sends data to the connected host.

        Parameters:
        data (str): The data to be sent.
        client_socket (socket.socket): The socket connected to the client.
        """
        try:
            self.host_socket.sendall(data.encode())
            print(f"Sent data to host connected: {data}")
        except Exception as e:
            print(f"Error sending data to host: {e}")


# Example usage
if __name__ == "__main__":
    client = TCPClient("localhost", 8888, '192.168.1.18', 8008, 9, "localhost", 8888)
    server = TCPServer("localhost", 8008, "localhost", 8888, client)

    client_thread = threading.Thread(target=client.connect_to_controller)
    server_thread = threading.Thread(target=server.start)

    client_thread.start()
    server_thread.start()
