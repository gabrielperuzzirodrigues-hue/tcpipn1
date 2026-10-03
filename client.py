#!/usr/bin/env python3
"""Cliente HTTP/1.1 didático: GET, 404 e POST JSON na mesma conexão TCP."""

import argparse
import json
import socket


def build_request(method, path, host, port, payload=None, close_connection=False):
    body = b""
    headers = [
        f"{method} {path} HTTP/1.1",
        f"Host: {host}:{port}",
        "User-Agent: demonstracao-http11/1.0",
        "Accept: application/json",
    ]
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers.append("Content-Type: application/json; charset=utf-8")
        headers.append(f"Content-Length: {len(body)}")
    headers.append(f"Connection: {'close' if close_connection else 'keep-alive'}")
    return ("\r\n".join(headers) + "\r\n\r\n").encode("ascii") + body


def read_response(connection):
    data = bytearray()
    while not data.endswith(b"\r\n\r\n"):
        piece = connection.recv(1)
        if not piece:
            raise ConnectionError("Conexão encerrada antes do fim dos cabeçalhos.")
        data.extend(piece)

    header_bytes = bytes(data[:-4])
    lines = header_bytes.split(b"\r\n")
    status_line = lines[0].decode("latin-1")
    headers = {}
    for line in lines[1:]:
        name, separator, value = line.partition(b":")
        if separator:
            headers[name.decode("ascii").lower()] = value.decode("latin-1").strip()

    if "content-length" not in headers:
        raise ValueError("O servidor não enviou Content-Length.")

    expected = int(headers["content-length"])
    body = bytearray()
    while len(body) < expected:
        piece = connection.recv(expected - len(body))
        if not piece:
            raise ConnectionError("Conexão encerrada antes do fim do corpo.")
        body.extend(piece)
    return status_line, headers, bytes(body)


def main():
    parser = argparse.ArgumentParser(description="Cliente HTTP/1.1 didático.")
    parser.add_argument("--host", default="127.0.0.1", help="Servidor (padrão: 127.0.0.1).")
    parser.add_argument("--port", type=int, default=8080, help="Porta TCP (padrão: 8080).")
    args = parser.parse_args()

    operations = [
        ("GET", "/", None),
        ("GET", "/missing", None),
        ("POST", "/echo", {"mensagem": "Olá, HTTP/1.1", "numero": 7}),
    ]
    with socket.create_connection((args.host, args.port), timeout=5) as connection:
        for index, (method, path, payload) in enumerate(operations):
            request = build_request(
                method,
                path,
                args.host,
                args.port,
                payload=payload,
                close_connection=index == len(operations) - 1,
            )
            print(">>> Requisição enviada:")
            print(request.decode("utf-8"), end="")
            if payload is not None:
                print()  # separa a exibição do corpo da próxima linha do terminal
            connection.sendall(request)

            status, headers, body = read_response(connection)
            print("<<< Resposta recebida:")
            print(status)
            print(f"Content-Type: {headers.get('content-type', '(ausente)')}")
            print(f"Content-Length: {headers.get('content-length', '(ausente)')}")
            print(f"Connection: {headers.get('connection', '(ausente)')}")
            print(body.decode("utf-8"))
            print()


if __name__ == "__main__":
    main()