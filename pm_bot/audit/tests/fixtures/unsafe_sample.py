import socket


def unsafe_value():
    return socket.gethostname()
