#!/usr/bin/env python3
"""Gera imagens legíveis do código e de uma execução real do experimento."""

import html
import shutil
import subprocess
import sys
import time
from pathlib import Path


BASE = Path(__file__).resolve().parent
FIGURES = BASE / "figuras"
HOST = "127.0.0.1"
PORT = 8080


def make_image(title, subtitle, text, output_name):
    FIGURES.mkdir(parents=True, exist_ok=True)
    html_path = FIGURES / f"{output_name}.html"
    png_path = FIGURES / f"{output_name}.png"
    line_count = max(1, len(text.splitlines()))
    height = max(500, min(2200, 220 + line_count * 29))
    page = f"""<!doctype html>
<html lang="pt-BR">
<meta charset="utf-8">
<title>{html.escape(title)}</title>
<style>
  * {{ box-sizing: border-box; }}
  html, body {{ margin: 0; width: 1600px; background: #101827; color: #e5edf8; }}
  body {{ padding: 34px 42px 42px; font-family: Arial, sans-serif; }}
  .top {{ display:flex; justify-content:space-between; align-items:center;
          border-bottom:1px solid #344156; padding-bottom:18px; margin-bottom:22px; }}
  h1 {{ margin:0; font-size:27px; font-weight:650; }}
  .tag {{ color:#a9c8ff; border:1px solid #5877a5; border-radius:15px;
          padding:7px 13px; font-size:14px; }}
  .sub {{ color:#a9b6ca; font-size:16px; margin:0 0 18px; }}
  pre {{ margin:0; padding:25px 28px; border:1px solid #344156; border-radius:9px;
         background:#0b111b; color:#e2e8f0; font-family:"DejaVu Sans Mono",
          "Liberation Mono", monospace; font-size:20px; line-height:1.4;
         white-space:pre-wrap; overflow-wrap:anywhere; }}
</style>
<body>
  <div class="top"><h1>{html.escape(title)}</h1><span class="tag">REGISTRO DO EXPERIMENTO</span></div>
  <p class="sub">{html.escape(subtitle)}</p>
  <pre>{html.escape(text)}</pre>
</body>
</html>"""
    html_path.write_text(page, encoding="utf-8")

    browser = next(
        (
            shutil.which(name)
            for name in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable")
            if shutil.which(name)
        ),
        None,
    )
    if browser is None and Path("/repl/tools/bin/chromium").exists():
        browser = "/repl/tools/bin/chromium"
    if browser is None:
        raise RuntimeError(
            "Chromium não encontrado. Instale Chromium ou adicione-o ao PATH para gerar as figuras."
        )
    command = [
        browser,
        "--headless",
        "--no-sandbox",
        "--disable-gpu",
        "--disable-dev-shm-usage",
        "--hide-scrollbars",
        "--no-first-run",
        f"--window-size=1600,{height}",
        f"--screenshot={png_path}",
        html_path.as_uri(),
    ]
    result = subprocess.run(command, capture_output=True, text=True, timeout=30)
    if result.returncode != 0 or not png_path.exists():
        raise RuntimeError(f"Falha ao renderizar {png_path.name}: {result.stderr}")
    return png_path


def code_excerpt():
    lines = (BASE / "server.py").read_text(encoding="utf-8").splitlines()
    blocks = [
        (
            next(i for i, line in enumerate(lines) if 'if "transfer-encoding" in headers:' in line),
            next(i for i, line in enumerate(lines) if "return method, target, version, headers, bytes(body)" in line),
        ),
        (
            next(i for i, line in enumerate(lines) if 'elif method == "POST" and path == "/echo":' in line),
            next(i for i, line in enumerate(lines) if 'elif method in {"GET", "POST"}:' in line) - 1,
        ),
    ]
    selected = []
    for block_index, (start, end) in enumerate(blocks):
        if block_index:
            selected.extend(["", "    # --- processamento da rota POST /echo ---"])
        selected.extend(f"{number + 1:4d}  {lines[number]}" for number in range(start, end + 1))
    return "\n".join(selected)


def wait_for_server(process):
    time.sleep(0.25)
    if process.poll() is not None:
        raise RuntimeError("O servidor encerrou antes de ficar pronto.")


def main():
    code_path = make_image(
        "Código do servidor: processamento do payload",
        "server.py — leitura por Content-Length, validação e decodificação do JSON em /echo",
        code_excerpt(),
        "codigo_payload",
    )

    server = subprocess.Popen(
        [sys.executable, "-u", "server.py", "--host", HOST, "--port", str(PORT)],
        cwd=BASE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        wait_for_server(server)
        client = subprocess.run(
            [sys.executable, "client.py", "--host", HOST, "--port", str(PORT)],
            cwd=BASE,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if client.returncode != 0:
            raise RuntimeError(f"Cliente falhou: {client.stderr}")
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait()

    server_output = server.stdout.read()
    client_output = "$ python3 client.py --host 127.0.0.1 --port 8080\n" + client.stdout
    client_path = make_image(
        "Cliente HTTP/1.1: requisições e respostas",
        "Execução real de GET /, GET /missing e POST /echo na mesma conexão TCP",
        client_output,
        "cliente_http11",
    )
    server_output = (
        "$ python3 server.py --host 127.0.0.1 --port 8080\n"
        + server_output.strip()
    )
    server_path = make_image(
        "Servidor HTTP/1.1: registro da execução",
        "Saída do servidor correspondente às três requisições enviadas pelo cliente",
        server_output,
        "servidor_http11",
    )
    print("Capturas geradas a partir do código-fonte e da execução real:")
    print(code_path)
    print(server_path)
    print(client_path)


if __name__ == "__main__":
    main()