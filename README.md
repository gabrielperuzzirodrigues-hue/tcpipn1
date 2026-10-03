# Demonstração didática de HTTP/1.1 — foco no payload

O relatório trata do **payload em HTTP/1.1**. Payload é o corpo/conteúdo carregado pela mensagem, não um protocolo independente; HTTP/1.1 continua sendo o protocolo analisado para atender ao enunciado.

Este exemplo usa apenas a biblioteca padrão do Python 3. Ele implementa um servidor local mínimo e um cliente que envia três requisições pela mesma conexão TCP: `GET /`, `GET /missing` e `POST /echo` com um corpo JSON em UTF-8. A execução torna observáveis o formato das mensagens, os cabeçalhos, `Content-Length`, os códigos `200`/`404` e a conexão persistente.

## Arquivos do pacote

- `relatorio_payload_http11.pdf`: versão final para leitura e entrega.
- `relatorio_payload_http11.docx`: versão editável do relatório.
- `server.py` e `client.py`: código-fonte da demonstração HTTP/1.1.
- `gerar_relatorio.py`, `gerar_capturas.py` e `exportar_pdf.py`: fontes usados para reconstruir o relatório e as figuras.
- `figuras/`: imagens incluídas no relatório.

Para reconstruir os documentos, na pasta `trabalho_http11`, execute:

```bash
python3 -m pip install -r requirements-report.txt
python3 gerar_capturas.py
python3 gerar_relatorio.py
python3 exportar_pdf.py
```

Essa etapa requer Chromium instalado; a execução de `server.py` e `client.py` não requer pacotes externos.

## Requisitos

- Python 3.9 ou superior (sem instalação de pacotes).
- Um terminal com acesso à pasta deste projeto.

## Execução

Abra um terminal na pasta `trabalho_http11` e execute:

```bash
python3 server.py --host 127.0.0.1 --port 8080
```

Deixe o servidor ativo. Em outro terminal, na mesma pasta:

```bash
python3 client.py --host 127.0.0.1 --port 8080
```

No Windows, se `python3` não existir, use `py` no lugar:

```powershell
py server.py --host 127.0.0.1 --port 8080
py client.py --host 127.0.0.1 --port 8080
```

O cliente envia `GET /`, `GET /missing` e `POST /echo` sequencialmente no mesmo socket. As respostas esperadas são `200 OK`, `404 Not Found` e `200 OK`. A última requisição inclui um objeto JSON; o servidor o decodifica e o devolve na resposta. A conexão é encerrada pelo cliente após o `POST`. No terminal do servidor, devem aparecer três linhas associadas à mesma conexão TCP.

Também é possível observar a troca com `curl`:

```bash
curl -v http://127.0.0.1:8080/status
```

Para testar o envio de JSON com outro cliente HTTP:

```bash
curl -v -H 'Content-Type: application/json' \
  --data-binary '{"mensagem":"Olá"}' \
  http://127.0.0.1:8080/echo
```

## Parâmetros e configuração

- `--host 127.0.0.1`: limita a escuta ao próprio computador. É adequado para um teste local e evita expor o servidor à rede.
- `--port 8080`: porta TCP escolhida para a atividade, sem exigir privilégios administrativos. A porta padrão convencional de HTTP é 80; `8080` é apenas a escolha desta demonstração.
- O cliente usa `Host`, `Accept`, `User-Agent` e `Connection`. No `POST`, acrescenta `Content-Type: application/json; charset=utf-8` e calcula `Content-Length` sobre os bytes UTF-8, não sobre o número de caracteres.
- O servidor responde com JSON em UTF-8 e informa o tamanho do corpo em bytes. O cliente lê exatamente essa quantidade para delimitar a resposta e continuar usando a conexão.
- O servidor aceita cabeçalhos de até 16 KiB e corpos de até 65.536 bytes; o limite ilustra validação de recursos em um parser de rede.
- `GET /` retorna uma mensagem; `GET /status` retorna um estado; `POST /echo` aceita JSON; caminhos não reconhecidos retornam `404`. Métodos fora de `GET` e `POST` recebem `405` e o campo `Allow`.

Se a porta 8080 já estiver ocupada, escolha outra porta, por exemplo 8081, e use o mesmo número nos comandos do servidor e do cliente. Isso altera apenas a porta de destino; cliente e servidor precisam concordar para estabelecer a conexão TCP.

## Limitações importantes

Este código é uma demonstração de conceitos, não uma implementação completa nem adequada para produção. Ele não oferece HTTPS/TLS, autenticação, tratamento de `Transfer-Encoding: chunked`, concorrência, suporte a pipeline ou todas as regras de segurança e interoperabilidade da especificação. O servidor processa conexões sequencialmente e deve permanecer restrito a testes locais; não o exponha à Internet.

## Figuras e prints do trabalho

O DOCX inclui uma imagem renderizada diretamente de um trecho real de `server.py` e duas imagens com a saída de uma execução real do servidor e do cliente neste ambiente. Elas mostram o código e as mensagens correspondentes, mas não são fotografias nem capturas da tela do computador do aluno. Se o professor exigir capturas feitas no próprio computador, execute os comandos acima e substitua as figuras de terminal pelas capturas originais:

1. A pasta com `server.py`, `client.py` e este `README.md` (configuração/arquivos).
2. O terminal do servidor mostrando `GET /`, `GET /missing`, `POST /echo` e os códigos `200`, `404` e `200`.
3. O terminal do cliente mostrando o `Content-Type`, o `Content-Length` e o corpo JSON enviado e recebido.

No Windows, use `Win + Shift + S`; no macOS, `Shift + Command + 4`; no Linux, a ferramenta de captura do ambiente. As capturas de execução devem corresponder ao que foi executado.