"""
Серверное приложение для соединений
"""
import asyncio
from asyncio import transports


class ClientProtocol(asyncio.Protocol):
    login: str
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None

    def data_received(self, data: bytes):
        decoded = data.decode()
        print(decoded)

        if self.login is None:
            # login:User
            if decoded.startswith("login:"):
                tmp_login = decoded.replace("login:", "").replace("\r\n", "")

                for client in self.server.clients:
                    if client.login == tmp_login:
                        self.transport.write(f"Логин {tmp_login} уже существует".encode())
                        self.transport.close()
                        break
                else:
                    self.login = tmp_login
                    self.transport.write(f"Привет, {self.login}!".encode())
                    self.server.send_history(self)
        else:
            self.send_message(decoded)

    def send_message(self, message):
        format_string = f"<{self.login}> {message}"
        encoded = format_string.encode()

        self.server.add_history(format_string)

        for client in self.server.clients:
            if client.login != self.login:
                client.transport.write(encoded)

    def connection_made(self, transport: transports.Transport):
        self.transport = transport
        self.server.clients.append(self)
        print("Соединение установлено")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Соединение разорвано")


class Server:
    clients: list
    history: list

    def __init__(self):
        self.clients = []
        self.history = []

    def add_history(self, message):
        if len(self.history) >= 10:
            self.history.pop(0)
        self.history.append(message)

    def send_history(self, client):
        for message in self.history:
            client.transport.write(f"\r\n{message}".encode())

    def create_protocol(self):
        return ClientProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.create_protocol,
            "127.0.0.1",
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
