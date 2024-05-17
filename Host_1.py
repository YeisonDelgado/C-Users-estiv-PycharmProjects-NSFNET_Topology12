import socket
import threading

class TCPClient:
    def __init__(self, server_host, server_port):
        self.server_host = server_host
        self.server_port = server_port
        self.client_socket = None

    def connect(self):
        """
        Establishes a connection to the TCP server and starts a thread to receive messages.
        """
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.server_host, self.server_port))

        # Start a thread to receive messages from the server
        receive_thread = threading.Thread(target=self.receive_messages)
        receive_thread.start()

    def send_data(self, data):
        """
        Sends data to the server and waits for a response.

        Parameters:
        data (str): The data to be sent to the server.

        Returns:
        str: The response received from the server.
        """
        self.client_socket.sendall(data.encode())
        response = self.client_socket.recv(1024).decode()
        return response

    def receive_messages(self):
        """
        Continuously listens for messages from the server and prints them.
        """
        while True:
            try:
                response = self.client_socket.recv(1024).decode()
                if response:
                    print(f"Received message from server: {response}")
            except Exception as e:
                print(f"Error receiving data from server: {e}")
                break

    def close(self):
        """
        Closes the connection to the server.
        """
        self.client_socket.close()

# Example usage
if __name__ == "__main__":
    client = TCPClient("localhost", 8000)
    client.connect()

    try:
        while True:
            message = input("Enter message to send (type 'exit' to quit): ")
            destination = input("Enter destination host (type 'exit' to quit): ")
            if message.lower() == 'exit' and destination.lower() == 'exit':
                break

            destination_ports = {
                "wa": "8000",
                "ca1": "8001",
                "ca2": "8002",
                "ut": "8003",
                "co": "8004",
                "tx": "8005",
                "ne": "8006",
                "il": "8007",
                "pa": "8008",
                "ga": "8009",
                "mi": "8010",
                "ny": "8011",
                "nj": "8012",
                "dc": "8013"
            }

            if destination.lower() in destination_ports:
                destination_port = destination_ports[destination.lower()]
                message_send = f"{message}-{destination_port}-{client.server_port}-{destination.upper()}"
                response = client.send_data(message_send)
                print(response)
            else:
                print("Invalid host destination")

    except KeyboardInterrupt:
        pass
    finally:
        client.close()