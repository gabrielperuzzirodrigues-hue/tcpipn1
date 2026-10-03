#!/usr/bin/env python3
"""Servidor HTTP/1.1 didático: GET, POST JSON e conexões persistentes."""

import argparse
import json
import socket
from datetime import datetime, timezone
from urllib.parse import urlsplit

MAX_HEADER_BYTES = 16_384
MAX_BODY_BYTES = 65_536
MAX_REQUESTS_PER_CONNECTION = 20

REASONS = {
    200: "OK",
    400: "Bad Request",
    404: "Not Found",
    405: "Method Not Allowed",
    413: "Content Too Large",
    415: "Unsupported Media Type",
    431: "Request Header Fields Too Large",
    501: "Not Implemented",
}


class RequestProblem(Exception):
    """Erro de leitura da requisição com um código HTTP associado."""

    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


def read_request(connection):
    """Lê cabeçalhos e o corpo delimitado por Content-Length."""
    data = bytearray()
    while not data.endswith(b"\r\n\r\n"):
        piece = connection.recv(1)
        if not piece:
            return None
        data.extend(piece)
        if len(data) > MAX_HEADER_BYTES:
            raise RequestProblem(431, "Cabeçalho maior que o limite didático.")

    lines = bytes(data[:-4]).split(b"\r\n")
    try:
        request_line = lines[0].decode("ascii")
        parts = request_line.split(" ", 2)
        if len(parts) != 3:
            raise ValueError("Linha de requisição inválida.")
        method, target, version = parts

        headers = {}
        for line in lines[1:]:
            name, separator, value = line.partition(b":")
            if not separator or not name:
                raise ValueError("Campo de cabeçalho inválido.")
            key = name.decode("ascii").strip().lower()
            value_text = value.decode("latin-1").strip()
            headers[key] = f"{headers[key]}, {value_text}" if key in headers else value_text
    except (UnicodeDecodeError, ValueError):
        raise RequestProblem(400, "Requisição HTTP malformada.") from None

    if "transfer-encoding" in headers:
        raise RequestProblem(
            501,
            "Transfer-Encoding não é implementado nesta demonstração; use Content-Length.",
        )

    raw_content_length = headers.get("content-length", "0")
    try:
        if not raw_content_length.isascii() or not raw_content_length.isdecimal():
            raise ValueError
        content_length = int(raw_content_length)
    except ValueError:
        raise RequestProblem(400, "Content-Length inválido.") from None

    if content_length > MAX_BODY_BYTES:
        raise RequestProblem(413, "Corpo maior que o limite de 65536 bytes.")

    body = bytearray()
    while len(body) < content_length:
        piece = connection.recv(content_length - len(body))
        if not piece:
            raise RequestProblem(400, "Conexão encerrada antes do fim do corpo.")
        body.extend(piece)

    return method, target, version, headers, bytes(body)


def send_response(connection, status, payload, close_connection=False, extra_headers=None):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    reason = REASONS.get(status, "Unknown")
    connection_header = "close" if close_connection else "keep-alive"
    headers = [
        f"HTTP/1.1 {status} {reason}",
        f"Date: {datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')}",
        "Content-Type: application/json; charset=utf-8",
        f"Content-Length: {len(body)}",
        f"Connection: {connection_header}",
    ]
    if extra_headers:
        headers.extend(extra_headers)
    response = ("\r\n".join(headers) + "\r\n\r\n").encode("ascii") + body
    connection.sendall(response)


def handle_client(connection, address):
    print(f"Conexão TCP recebida de {address[0]}:{address[1]}")
    with connection:
        for request_number in range(1, MAX_REQUESTS_PER_CONNECTION + 1):
            try:
                request = read_request(connection)
            except RequestProblem as error:
                send_response(
                    connection,
                    error.status,
                    {"erro": str(error)},
                    close_connection=True,
                )
                break

            if request is None:
                break

            method, target, version, headers, body = request
            if version != "HTTP/1.1" or "host" not in headers:
                send_response(
                    connection,
                    400,
                    {"erro": "Use HTTP/1.1 e envie o cabeçalho Host."},
                    True,
                )
                break

            connection_tokens = {
                token.strip().lower()
                for token in headers.get("connection", "keep-alive").split(",")
            }
            close_after_response = (
                "close" in connection_tokens
                or request_number == MAX_REQUESTS_PER_CONNECTION
            )

            path = urlsplit(target).path
            if method == "GET" and body:
                status = 400
                payload = {"erro": "Esta demonstração não aceita corpo em requisições GET."}
                extra = None
            elif method == "GET" and path == "/":
                status = 200
                payload = {
                    "mensagem": "Olá! Esta resposta foi enviada por HTTP/1.1.",
                    "protocolo": version,
                    "rota": path,
                }
                extra = None
            elif method == "GET" and path == "/status":
                status = 200
                payload = {
                    "status": "ok",
                    "instante_utc": datetime.now(timezone.utc).isoformat(),
                }
                extra = None
            elif method == "POST" and path == "/echo":
                media_type = headers.get("content-type", "").split(";", 1)[0].strip().lower()
                if media_type != "application/json":
                    status = 415
                    payload = {"erro": "Envie Content-Type: application/json."}
                    extra = None
                else:
                    try:
                        received_json = json.loads(body.decode("utf-8"))
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        status = 400
                        payload = {"erro": "Corpo deve ser JSON válido codificado em UTF-8."}
                    else:
                        status = 200
                        payload = {
                            "mensagem": "JSON recebido com sucesso.",
                            "dados_recebidos": received_json,
                            "bytes_recebidos": len(body),
                        }
                    extra = None
            elif method in {"GET", "POST"}:
                status = 404
                payload = {"erro": "Recurso não encontrado.", "rota": path}
                extra = None
            else:
                status = 405
                payload = {
                    "erro": "Método não implementado.",
                    "metodos_permitidos": ["GET", "POST"],
                }
                extra = ["Allow: GET, POST"]

            send_response(
                connection,
                status,
                payload,
                close_connection=close_after_response,
                extra_headers=extra,
            )
            print(f"{method} {target} -> {status}")
            if close_after_response:
                break

    print(f"Conexão encerrada com {address[0]}:{address[1]}")


def main():
    parser = argparse.ArgumentParser(description="Servidor HTTP/1.1 didático.")
    parser.add_argument("--host", default="127.0.0.1", help="Endereço de escuta (padrão: loopback).")
    parser.add_argument("--port", type=int, default=8080, help="Porta TCP (padrão: 8080).")
    args = parser.parse_args()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((args.host, args.port))
        server.listen()
        print(f"Servidor HTTP/1.1 em http://{args.host}:{args.port}")
        print("Pressione Ctrl+C para encerrar.")
        try:
            while True:
                connection, address = server.accept()
                handle_client(connection, address)
        except KeyboardInterrupt:
            print("\nServidor encerrado pelo usuário.")


if __name__ == "__main__":
    main()