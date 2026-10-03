#!/usr/bin/env python3
"""Gera o relatório acadêmico em DOCX com formatação-base ABNT."""

import os

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.shared import Cm, Pt, Inches
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

OUTPUT = os.path.join(os.path.dirname(__file__), "relatorio_payload_http11.docx")
FIGURE_DIR = os.path.join(os.path.dirname(__file__), "figuras")


def add_page_number(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = paragraph.add_run()
    set_run_font(run, size=10)
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instruction = OxmlElement("w:instrText")
    instruction.set(qn("xml:space"), "preserve")
    instruction.text = " PAGE "
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t")
    text.text = "6"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.extend([begin, instruction, separate, text, end])


def set_run_font(run, name="Times New Roman", size=12, bold=None, italic=None):
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic


def add_body(doc, text):
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    paragraph.paragraph_format.first_line_indent = Cm(1.25)
    paragraph.paragraph_format.line_spacing = 1.5
    paragraph.paragraph_format.space_after = Pt(0)
    run = paragraph.add_run(text)
    set_run_font(run)
    return paragraph


def add_heading(doc, text, level=1):
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.keep_with_next = True
    paragraph.paragraph_format.line_spacing = 1.5
    paragraph.paragraph_format.space_before = Pt(18 if level == 1 else 12)
    paragraph.paragraph_format.space_after = Pt(18 if level == 1 else 12)
    is_numbered = text[:1].isdigit()
    paragraph.alignment = (
        WD_ALIGN_PARAGRAPH.LEFT if is_numbered else WD_ALIGN_PARAGRAPH.CENTER
    )
    if level == 1 and text not in {"1 INTRODUÇÃO"}:
        paragraph.paragraph_format.page_break_before = True
    run = paragraph.add_run(text)
    set_run_font(run, size=12, bold=True)
    return paragraph


def add_front_paragraph(
    doc,
    text,
    style_name,
    *,
    alignment=WD_ALIGN_PARAGRAPH.CENTER,
    size=12,
    bold=False,
    italic=False,
    before=0,
    after=0,
    line_spacing=1.5,
    left_indent=0,
    right_indent=0,
    first_line_indent=0,
    page_break_before=False,
):
    if style_name not in doc.styles:
        doc.styles.add_style(style_name, WD_STYLE_TYPE.PARAGRAPH)
    paragraph = doc.add_paragraph(style=style_name)
    paragraph.alignment = alignment
    paragraph.paragraph_format.space_before = Pt(before)
    paragraph.paragraph_format.space_after = Pt(after)
    paragraph.paragraph_format.line_spacing = line_spacing
    paragraph.paragraph_format.left_indent = Cm(left_indent)
    paragraph.paragraph_format.right_indent = Cm(right_indent)
    paragraph.paragraph_format.first_line_indent = Cm(first_line_indent)
    paragraph.paragraph_format.page_break_before = page_break_before
    set_run_font(
        paragraph.add_run(text),
        size=size,
        bold=bold,
        italic=italic,
    )
    return paragraph


def add_abstract_paragraph(doc, text, style_name):
    return add_front_paragraph(
        doc,
        text,
        style_name,
        alignment=WD_ALIGN_PARAGRAPH.JUSTIFY,
        size=12,
        line_spacing=1.0,
        first_line_indent=0,
    )


def add_toc_entry(doc, label, page, level=1, style_name="TocEntry"):
    if style_name not in doc.styles:
        doc.styles.add_style(style_name, WD_STYLE_TYPE.PARAGRAPH)
    paragraph = doc.add_paragraph(style=style_name)
    paragraph.paragraph_format.left_indent = Cm(0 if level == 1 else 0.75)
    paragraph.paragraph_format.first_line_indent = Cm(0)
    paragraph.paragraph_format.line_spacing = 1.0
    paragraph.paragraph_format.space_after = Pt(4)
    paragraph.paragraph_format.tab_stops.add_tab_stop(
        Cm(15.8), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS
    )
    paragraph.add_run(f"{label}\t{page}")
    return paragraph


def add_code(doc, text):
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.left_indent = Cm(1)
    paragraph.paragraph_format.right_indent = Cm(0.5)
    paragraph.paragraph_format.first_line_indent = Cm(0)
    paragraph.paragraph_format.line_spacing = 1.0
    paragraph.paragraph_format.space_before = Pt(3)
    paragraph.paragraph_format.space_after = Pt(3)
    paragraph.paragraph_format.keep_together = True
    run = paragraph.add_run(text)
    set_run_font(run, name="Consolas", size=9)
    return paragraph


def add_figure_image(doc, image_path, caption, source_text):
    image_paragraph = doc.add_paragraph()
    image_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    image_paragraph.paragraph_format.first_line_indent = Cm(0)
    image_paragraph.paragraph_format.space_before = Pt(5)
    image_paragraph.paragraph_format.space_after = Pt(3)
    image_paragraph.add_run().add_picture(image_path, width=Inches(6.1))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.first_line_indent = Cm(0)
    cap.paragraph_format.line_spacing = 1.0
    cap.paragraph_format.space_before = Pt(4)
    cap.paragraph_format.space_after = Pt(2)
    set_run_font(cap.add_run(caption), size=10)
    source = doc.add_paragraph()
    source.alignment = WD_ALIGN_PARAGRAPH.LEFT
    source.paragraph_format.first_line_indent = Cm(0)
    source.paragraph_format.line_spacing = 1.0
    source.paragraph_format.space_after = Pt(8)
    set_run_font(source.add_run(f"Fonte: {source_text} (2026)."), size=10)


def add_reference(doc, text):
    if "ReferenceEntry" not in doc.styles:
        doc.styles.add_style("ReferenceEntry", WD_STYLE_TYPE.PARAGRAPH)
    paragraph = doc.add_paragraph(style="ReferenceEntry")
    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
    paragraph.paragraph_format.first_line_indent = Cm(0)
    paragraph.paragraph_format.line_spacing = 1.0
    paragraph.paragraph_format.space_after = Pt(12)
    run = paragraph.add_run(text)
    set_run_font(run, size=12)


def main():
    doc = Document()
    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(3)
    section.left_margin = Cm(3)
    section.bottom_margin = Cm(2)
    section.right_margin = Cm(2)
    section.header_distance = Cm(2)
    section.footer_distance = Cm(1.25)

    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    normal.font.size = Pt(12)

    title_text = (
        "PAYLOAD EM HTTP/1.1: FORMATO, DELIMITAÇÃO E "
        "PROCESSAMENTO DO CORPO DA MENSAGEM"
    )

    add_front_paragraph(
        doc,
        "UniRedentor",
        "CoverInstitution",
        bold=True,
        after=4,
        line_spacing=1.0,
    )
    add_front_paragraph(
        doc,
        "Engenharia da Computação",
        "CoverCourse",
        after=2,
        line_spacing=1.0,
    )
    add_front_paragraph(
        doc,
        "Arquitetura TCP/IP",
        "CoverDiscipline",
        line_spacing=1.0,
    )
    add_front_paragraph(
        doc,
        "Gabriel Peruzzi Rodrigues",
        "CoverAuthor",
        before=115,
        line_spacing=1.0,
    )
    add_front_paragraph(
        doc,
        "Matrícula: 2577853",
        "CoverRegistration",
        line_spacing=1.0,
    )
    add_front_paragraph(
        doc,
        title_text,
        "CoverTitle",
        bold=True,
        before=150,
        line_spacing=1.5,
    )
    add_front_paragraph(
        doc,
        "Itaperuna – RJ",
        "CoverPlace",
        before=215,
        line_spacing=1.0,
    )
    add_front_paragraph(
        doc,
        "2026",
        "CoverYear",
        line_spacing=1.0,
    )

    add_front_paragraph(
        doc,
        "Gabriel Peruzzi Rodrigues",
        "TitlePageAuthor",
        before=0,
        after=0,
        line_spacing=1.0,
        page_break_before=True,
    )
    add_front_paragraph(
        doc,
        "Matrícula: 2577853",
        "TitlePageRegistration",
        line_spacing=1.0,
    )
    add_front_paragraph(
        doc,
        title_text,
        "TitlePageTitle",
        bold=True,
        before=75,
        line_spacing=1.5,
    )
    add_front_paragraph(
        doc,
        "Trabalho acadêmico apresentado à disciplina Arquitetura TCP/IP, "
        "do curso de Engenharia da Computação da UniRedentor, como requisito "
        "parcial de avaliação. Professor: Hugo Hoffmann Borges.",
        "TitlePageNature",
        alignment=WD_ALIGN_PARAGRAPH.JUSTIFY,
        before=140,
        line_spacing=1.0,
        left_indent=7,
    )
    add_front_paragraph(
        doc,
        "Itaperuna – RJ",
        "TitlePagePlace",
        before=175,
        line_spacing=1.0,
    )
    add_front_paragraph(
        doc,
        "2026",
        "TitlePageYear",
        line_spacing=1.0,
    )

    add_heading(doc, "RESUMO")
    summary_pt = (
        "Este trabalho analisa o HTTP/1.1 com foco no payload, isto é, no conteúdo "
        "transportado no corpo das mensagens, sem tratar Payload como protocolo "
        "independente. O objetivo é explicar como esse conteúdo é representado, "
        "delimitado e processado em conjunto com os cabeçalhos e a conexão TCP. "
        "O estudo descreve as funções de transporte, gerenciamento de conexão, "
        "apresentação dos dados e semântica da camada de aplicação, considerando "
        "que sessão e apresentação não são camadas autônomas no modelo TCP/IP. "
        "Como método demonstrativo, foram utilizados um servidor e um cliente "
        "mínimos em Python, com sockets da biblioteca padrão, executados em loopback. "
        "O cliente envia GET /, GET /missing e POST /echo na mesma conexão; o POST "
        "transporta um objeto JSON codificado em UTF-8. A execução permite observar "
        "Content-Length como tamanho em bytes, a leitura exata do corpo, a decodificação "
        "do JSON e as respostas 200 e 404. Testes adicionais verificam erros para JSON "
        "inválido e tipo de mídia incompatível. Conclui-se que o corpo só pode ser "
        "interpretado com enquadramento explícito e metadados coerentes. A implementação "
        "é limitada a fins didáticos e não deve ser usada em produção."
    )
    add_abstract_paragraph(doc, summary_pt, "AbstractBody")
    add_front_paragraph(
        doc,
        "Palavras-chave: payload; HTTP/1.1; TCP; corpo da mensagem; JSON.",
        "AbstractKeywords",
        alignment=WD_ALIGN_PARAGRAPH.LEFT,
        before=8,
        line_spacing=1.0,
    )

    add_heading(doc, "LISTA DE ILUSTRAÇÕES")
    add_toc_entry(
        doc,
        "Figura 1 — Código de leitura, validação e processamento do payload",
        "10",
        style_name="FigureListEntry",
    )
    add_toc_entry(
        doc,
        "Figura 2 — Saída do servidor ao processar as requisições",
        "11",
        style_name="FigureListEntry",
    )
    add_toc_entry(
        doc,
        "Figura 3 — Mensagens e respostas observadas pelo cliente",
        "11",
        style_name="FigureListEntry",
    )

    add_heading(doc, "SUMÁRIO")
    for label, page, level in (
        ("1 INTRODUÇÃO", "5", 1),
        ("2 ANÁLISE DO HTTP/1.1 COM FOCO NO PAYLOAD", "6", 1),
        ("2.1 Relação com as camadas inferiores", "6", 2),
        ("2.2 Funções de sessão", "6", 2),
        ("2.3 Funções de apresentação", "7", 2),
        ("2.4 Decisões da camada de aplicação", "8", 2),
        ("3 TUTORIAL DE CONFIGURAÇÃO E UTILIZAÇÃO", "9", 1),
        ("3.1 Arquivos e parâmetros", "9", 2),
        ("3.2 Execução passo a passo", "9", 2),
        ("3.3 Registros de configuração e execução", "10", 2),
        ("4 DISCUSSÃO E LIMITAÇÕES", "12", 1),
        ("5 CONCLUSÃO", "13", 1),
        ("REFERÊNCIAS", "14", 1),
    ):
        add_toc_entry(doc, label, page, level=level)

    main_section = doc.add_section(WD_SECTION.NEW_PAGE)
    main_section.page_width = Cm(21)
    main_section.page_height = Cm(29.7)
    main_section.top_margin = Cm(3)
    main_section.left_margin = Cm(3)
    main_section.bottom_margin = Cm(2)
    main_section.right_margin = Cm(2)
    main_section.header_distance = Cm(2)
    main_section.footer_distance = Cm(1.25)
    main_section.header.is_linked_to_previous = False
    main_section.footer.is_linked_to_previous = False
    add_page_number(main_section.header.paragraphs[0])
    page_numbering = OxmlElement("w:pgNumType")
    page_numbering.set(qn("w:start"), "5")
    main_section._sectPr.append(page_numbering)

    add_heading(doc, "1 INTRODUÇÃO")
    add_body(
        doc,
        "O Hypertext Transfer Protocol (HTTP) é um protocolo da camada de aplicação para "
        "sistemas distribuídos de informação. Ele define como um cliente identifica um "
        "recurso, envia uma requisição e interpreta a resposta de um servidor, sem exigir "
        "que ambos usem o mesmo sistema operacional ou linguagem de programação (IETF, "
        "2022a). Essa interoperabilidade sustenta a Web, APIs, distribuição de arquivos, "
        "proxies e caches."
    )
    add_body(
        doc,
        "O problema tratado pelo HTTP é a comunicação interoperável orientada a recursos: "
        "uma implementação precisa expressar a operação pretendida, transportar metadados "
        "e conteúdo e interpretar um resultado padronizado. O protocolo não especifica a "
        "lógica interna do serviço nem o formato universal de cada conteúdo; esses aspectos "
        "são negociados por métodos, campos de cabeçalho e tipos de mídia."
    )
    add_body(
        doc,
        "O tema deste estudo é o payload em HTTP/1.1: o corpo da mensagem da camada de "
        "aplicação, sua representação e seu enquadramento no fluxo da conexão. Payload "
        "não é um protocolo independente; é o conteúdo carregado por uma mensagem. "
        "O trabalho, portanto, analisa o HTTP/1.1: sua sintaxe de mensagens e gerenciamento "
        "de conexões são especificados pelo RFC 9112, em conjunto com a semântica comum "
        "descrita pelo RFC 9110 (IETF, 2022a; IETF, 2022b). O objetivo é explicar as "
        "decisões de projeto por trás do protocolo e demonstrá-las por meio de um cliente "
        "e um servidor locais escritos com sockets da biblioteca padrão do Python. "
        "O cliente executa GET e POST na mesma conexão, para tornar visível também "
        "a delimitação do corpo da requisição."
    )

    add_heading(doc, "2 ANÁLISE DO HTTP/1.1 COM FOCO NO PAYLOAD")
    add_heading(doc, "2.1 Relação com as camadas inferiores", 2)
    add_body(
        doc,
        "Na arquitetura TCP/IP, HTTP ocupa a camada de aplicação. Abaixo dela, a "
        "demonstração usa TCP na camada de transporte, IPv4 na camada de Internet e a "
        "interface de loopback do próprio sistema como acesso à rede. Em uma rede real, "
        "o tráfego ainda seria encapsulado por tecnologias de enlace, como Ethernet ou "
        "Wi-Fi. A pilha pode ser resumida assim:"
    )
    add_code(doc, "Aplicação: HTTP/1.1  →  Transporte: TCP  →  Internet: IPv4  →  Enlace")
    add_body(
        doc,
        "HTTP/1.1 usa uma conexão TCP confiável e ordenada porque suas mensagens são "
        "fluxos de bytes: a aplicação precisa reconstruir linhas, campos e corpos na "
        "ordem enviada. O TCP detecta perdas e retransmite segmentos, além de oferecer "
        "controle de fluxo entre emissor e receptor (IETF, 2022c). Isso simplifica o "
        "protocolo de aplicação e permite que o servidor processe mensagens completas "
        "mesmo quando a rede as divide em vários segmentos. O custo é o estabelecimento "
        "da conexão e a latência de retransmissões; perdas também podem atrasar bytes "
        "posteriores no mesmo fluxo."
    )
    add_body(
        doc,
        "A porta convencional do esquema HTTP é TCP 80; para HTTPS, o esquema usa "
        "normalmente a porta TCP 443. A porta não substitui a identificação do protocolo: "
        "é uma convenção de destino. HTTPS combina HTTP com TLS para proteger a conexão; "
        "TLS não é uma propriedade de criptografia do HTTP em texto claro. HTTP/3 é uma "
        "versão distinta que usa QUIC sobre UDP, e não é o objeto desta implementação. "
        "No experimento, escolheu-se TCP 8080 para evitar privilégios administrativos e "
        "não conflitar com serviços comuns. O servidor fica restrito a 127.0.0.1, portanto "
        "o teste não depende de uma rede externa nem expõe o serviço a outros computadores."
    )

    add_heading(doc, "2.2 Funções de sessão", 2)
    add_body(
        doc,
        "O modelo TCP/IP não possui uma camada de sessão separada como a do modelo OSI. "
        "Ainda assim, é possível analisar essas funções no comportamento do HTTP/1.1 e "
        "do TCP. Uma conexão começa quando o cliente abre um socket TCP para o endereço "
        "e a porta do servidor; é identificada na rede pelo par de endereços e portas "
        "de origem e destino. O TCP estabelece o estado da conexão e a encerra por meio "
        "de fechamento ordenado ou após uma falha."
    )
    add_body(
        doc,
        "A semântica do HTTP é sem estado: cada requisição pode ser compreendida sem "
        "armazenar no protocolo uma conversa anterior (IETF, 2022a). Isso facilita "
        "balanceamento e recuperação de servidores, mas não significa que aplicações "
        "não possam manter estado. Quando necessário, aplicações usam mecanismos como "
        "cookies e identificadores próprios. O servidor didático deste trabalho não "
        "implementa login, cookies nem estado de usuário."
    )
    add_body(
        doc,
        "HTTP/1.1 permite conexões persistentes por padrão: várias requisições e respostas "
        "podem usar o mesmo fluxo TCP, até que uma das partes solicite fechamento com "
        "Connection: close ou a conexão falhe. Isso reduz novas aberturas de TCP e pode "
        "diminuir latência, mas mantém recursos do servidor ocupados por mais tempo. "
        "A demonstração reutiliza a mesma conexão para GET / e GET /missing, depois "
        "solicita seu encerramento. A falha de uma conexão não informa, por si só, se "
        "uma operação chegou a ser executada; clientes precisam considerar a semântica "
        "do método antes de repetir uma operação. Por isso, a demonstração usa GET "
        "para consulta e POST para enviar dados, mas não repete requisições "
        "automaticamente após uma falha."
    )

    add_heading(doc, "2.3 Funções de apresentação", 2)
    add_body(
        doc,
        "Também não há uma camada de apresentação autônoma na arquitetura TCP/IP. "
        "HTTP/1.1 oferece sintaxe textual para a linha inicial e os campos de cabeçalho, "
        "com nomes de campos insensíveis a maiúsculas e minúsculas; a separação entre "
        "cabeçalhos e conteúdo é indicada por uma linha vazia formada por CRLF. O corpo "
        "é uma sequência de octetos, não necessariamente texto. Assim, o protocolo "
        "consegue transportar diferentes formatos sem interpretar sua estrutura interna."
    )
    add_body(
        doc,
        "O tipo de mídia é indicado por Content-Type. Nesta demonstração, o corpo é JSON "
        "codificado em UTF-8 e declarado como application/json; charset=utf-8. O JSON "
        "representa objetos, textos, números, booleanos e valores nulos de forma "
        "independente de linguagem. Content-Length informa o tamanho do corpo em octetos "
        "(bytes), e não o número visual de caracteres; essa distinção é importante para "
        "acentos codificados em UTF-8. No POST /echo, o cliente serializa um objeto "
        "Python em JSON, codifica o texto em UTF-8 e calcula Content-Length sobre os "
        "bytes resultantes. O servidor usa esse comprimento para ler exatamente o corpo "
        "antes de aguardar a próxima requisição na conexão persistente. Em HTTP/1.1, "
        "Transfer-Encoding: chunked pode delimitar conteúdo de tamanho ainda não "
        "conhecido; esta implementação não aceita essa modalidade e fecha a conexão "
        "com erro explícito. Codificação de conteúdo, como gzip, é uma questão "
        "diferente da delimitação da mensagem. A linha vazia encerra os cabeçalhos, "
        "mas não sinaliza o fim do corpo: como o conteúdo pode conter quaisquer bytes, "
        "o receptor precisa de um enquadramento explícito. Content-Length é simples "
        "quando o tamanho já é conhecido; chunked facilita transmitir partes cujo "
        "tamanho só é conhecido durante a geração, mas requer lógica adicional no parser."
    )
    add_body(
        doc,
        "HTTP simples não cifra nem autentica criptograficamente o conteúdo. Quando "
        "confidencialidade e integridade em trânsito são necessárias, HTTPS usa TLS; "
        "o TLS negocia parâmetros criptográficos e protege registros com mecanismos "
        "criptográficos autenticados (IETF, 2018). Isso traz segurança, mas também "
        "handshake, processamento e requisitos de certificados. A implementação local "
        "não inclui TLS e, portanto, serve somente a um ambiente de teste."
    )

    add_heading(doc, "2.4 Decisões da camada de aplicação", 2)
    add_body(
        doc,
        "HTTP utiliza o paradigma cliente-servidor e a troca requisição-resposta. "
        "Uma requisição HTTP/1.1 contém uma linha com método, alvo e versão, seguida "
        "por campos de cabeçalho e, quando aplicável, corpo. A resposta começa com "
        "versão, código numérico e frase de motivo, seguida por campos e conteúdo. "
        "O campo Host é obrigatório em requisições HTTP/1.1 e permite que um servidor "
        "hospede vários nomes no mesmo endereço IP. O exemplo abaixo é esquemático: "
        "o valor de Content-Length varia conforme os bytes exatos do corpo e da resposta."
    )
    add_code(
        doc,
        "POST /echo HTTP/1.1\\r\\n"
        "Host: 127.0.0.1:8080\\r\\n"
        "Content-Type: application/json; charset=utf-8\\r\\n"
        "Content-Length: [bytes do corpo]\\r\\n"
        "Connection: keep-alive\\r\\n"
        "\\r\\n"
        "{\"mensagem\":\"Olá, HTTP/1.1\",\"numero\":7}"
    )
    add_body(
        doc,
        "Depois de ler os bytes indicados e validar o tipo de mídia, o servidor "
        "decodifica o JSON e envia uma resposta independente, também delimitada por "
        "Content-Length:"
    )
    add_code(
        doc,
        "HTTP/1.1 200 OK\\r\\n"
        "Content-Type: application/json; charset=utf-8\\r\\n"
        "Content-Length: [bytes da resposta]\\r\\n"
        "Connection: keep-alive\\r\\n"
        "\\r\\n"
        "{\"mensagem\":\"JSON recebido com sucesso.\", ...}"
    )
    add_body(
        doc,
        "Os métodos identificam a operação, sem definir a implementação interna. GET "
        "solicita uma representação e é definido como método seguro e idempotente, "
        "o que permite certas estratégias de repetição e cache. POST costuma submeter "
        "dados para processamento; PUT substitui ou cria a representação no alvo; "
        "DELETE solicita remoção. Códigos de estado agrupam resultados: 2xx indica "
        "sucesso, 3xx redirecionamento, 4xx erro associado à requisição e 5xx falha "
        "do servidor. O exemplo retorna 200 para operações válidas, 404 para caminho "
        "inexistente, 400 para JSON malformado, 405 para método não aceito, 413 para "
        "corpo acima do limite e 415 para tipo de mídia inadequado. A resposta 405 "
        "inclui Allow: GET, POST. GET é seguro e idempotente por definição semântica; "
        "POST pode alterar estado e não deve ser repetido cegamente após falhas. Essa "
        "distinção mostra que métodos padronizados carregam semântica além de serem "
        "rótulos textuais."
    )
    add_body(
        doc,
        "A interoperabilidade decorre de uma sintaxe comum, semântica documentada, "
        "campos padronizados e tipos de mídia declarados. Clientes e servidores podem "
        "ser implementados separadamente desde que respeitem as especificações. A "
        "extensibilidade por campos e formatos tem a vantagem de permitir evolução, "
        "mas exige que implementações tratem corretamente campos desconhecidos, "
        "delimitação de mensagens e diferenças de suporte."
    )

    add_heading(doc, "3 TUTORIAL DE CONFIGURAÇÃO E UTILIZAÇÃO")
    add_heading(doc, "3.1 Arquivos e parâmetros", 2)
    add_body(
        doc,
        "O material fornecido contém server.py (servidor), client.py (cliente), "
        "README.md (passos de execução) e este relatório. O código usa somente módulos "
        "da biblioteca padrão do Python 3 e não requer instalação de pacotes. A "
        "configuração padrão vincula o servidor a 127.0.0.1:8080. O endereço de loopback "
        "restringe o teste ao computador local; a porta 8080 é uma escolha didática "
        "não privilegiada, em lugar da porta convencional 80. O servidor limita "
        "cabeçalhos a 16 KiB e corpos a 65.536 bytes para demonstrar validação de "
        "entrada e reduzir o risco de consumo excessivo de memória, além de encerrar "
        "uma conexão após 20 requisições para limitar sua duração. Se a porta 8080 "
        "estiver ocupada, use 8081 nos dois comandos; os dois lados precisam apontar "
        "para a mesma porta para abrir a conexão TCP. O enunciado pede tutorial "
        "reproduzível, comandos e configuração, mas não exige a implementação de um "
        "software completo. O cliente e servidor foram incluídos como demonstração "
        "complementar para tornar observável o enquadramento do payload."
    )
    add_heading(doc, "3.2 Execução passo a passo", 2)
    add_body(
        doc,
        "Abra um terminal na pasta do material e inicie o servidor. Mantenha esse "
        "terminal aberto; ele registra as requisições recebidas."
    )
    add_code(doc, "python3 server.py --host 127.0.0.1 --port 8080")
    add_body(
        doc,
        "Em um segundo terminal, na mesma pasta, execute o cliente. Em sistemas Windows, "
        "caso o comando python3 não exista, use py."
    )
    add_code(doc, "python3 client.py --host 127.0.0.1 --port 8080")
    add_body(
        doc,
        "O cliente envia três requisições no mesmo socket TCP: GET / solicita a "
        "resposta JSON de boas-vindas; GET /missing exercita a resposta 404; POST /echo "
        "envia um objeto JSON com Content-Type e Content-Length. As respostas esperadas "
        "são 200, 404 e 200. As duas primeiras usam Connection: keep-alive; o POST final "
        "solicita Connection: close. No servidor, as três linhas devem aparecer sob a "
        "mesma conexão recebida. O corpo do POST contém o texto acentuado “Olá”, útil "
        "para observar que o tamanho é medido em bytes UTF-8. Opcionalmente, outro "
        "cliente como curl pode consultar o servidor:"
    )
    add_code(doc, "curl -v http://127.0.0.1:8080/status")
    add_body(
        doc,
        "O comando curl -v exibe detalhes da mensagem enviada e da resposta recebida. "
        "Para exercitar POST /echo com um cliente independente, use:"
    )
    add_code(
        doc,
        "curl -v -H 'Content-Type: application/json' "
        "--data-binary '{\"mensagem\":\"Olá\"}' "
        "http://127.0.0.1:8080/echo"
    )
    add_body(
        doc,
        "No cliente próprio, Content-Length é calculado em bytes após a codificação "
        "UTF-8 e usado para delimitar o corpo. Os cabeçalhos Connection e Host "
        "demonstram, respectivamente, o gerenciamento da conexão e a identificação "
        "do destino HTTP/1.1. A demonstração faz requisições sequenciais, não usa "
        "pipeline e processa clientes um por vez; a simplicidade favorece a observação, "
        "mas limita o desempenho e a interoperabilidade."
    )
    add_heading(doc, "3.3 Registros de configuração e execução", 2)
    add_body(
        doc,
        "As figuras a seguir mostram um trecho do código-fonte e a saída obtida ao "
        "executar servidor e cliente. O código da primeira figura foi renderizado "
        "diretamente do arquivo server.py; as duas últimas correspondem à execução "
        "local da demonstração preparada para este trabalho. Elas não são capturas "
        "do computador do aluno. Se o professor exigir imagens feitas no próprio "
        "computador, execute os comandos do tutorial e substitua as duas figuras de "
        "terminal por capturas originais."
    )
    add_figure_image(
        doc,
        os.path.join(FIGURE_DIR, "codigo_payload.png"),
        "Figura 1 – Código de leitura, validação e processamento do payload",
        "trecho do arquivo server.py, renderizado diretamente do código-fonte",
    )
    add_figure_image(
        doc,
        os.path.join(FIGURE_DIR, "servidor_http11.png"),
        "Figura 2 – Saída do servidor ao processar as requisições",
        "execução local do servidor HTTP/1.1",
    )
    add_figure_image(
        doc,
        os.path.join(FIGURE_DIR, "cliente_http11.png"),
        "Figura 3 – Mensagens e respostas observadas pelo cliente",
        "execução local do cliente HTTP/1.1",
    )

    add_heading(doc, "4 DISCUSSÃO E LIMITAÇÕES")
    add_body(
        doc,
        "O experimento torna visíveis escolhas que, em aplicações cotidianas, ficam "
        "ocultas por bibliotecas de alto nível. A conexão TCP fornece fluxo confiável "
        "e ordenado; o HTTP define os limites e o significado das mensagens; Content-Type "
        "declara o formato do corpo; Content-Length permite delimitar tanto a requisição "
        "POST quanto a resposta sem fechar a conexão. A persistência reduz a necessidade "
        "de abrir uma conexão TCP para cada recurso, enquanto a semântica sem estado "
        "mantém requisições independentes no nível do protocolo."
    )
    add_body(
        doc,
        "A implementação é propositalmente parcial. Ela processa mensagens sequenciais "
        "e aceita apenas GET e POST para rotas específicas; entende Content-Length, "
        "mas não implementa codificação chunked, TLS, autenticação, compressão, cache, "
        "pipeline, concorrência, limites completos de tempo ou toda a validação definida "
        "pelos RFCs. Um servidor de produção deve usar uma implementação madura, com "
        "tratamento robusto de entrada não confiável, concorrência, registros, "
        "configuração de segurança e testes de conformidade. O escopo reduzido facilita "
        "a observação do protocolo, mas reduz interoperabilidade e segurança."
    )
    add_body(
        doc,
        "A restrição a 127.0.0.1 e a porta 8080 é deliberada: facilita reproduzir o "
        "teste e limita sua exposição. Alterar o endereço para 0.0.0.0 permitiria "
        "acesso por outras interfaces da máquina, mas não é necessário para a atividade "
        "e aumentaria o risco. Não se deve publicar este servidor de demonstração na "
        "Internet."
    )

    add_heading(doc, "5 CONCLUSÃO")
    add_body(
        doc,
        "HTTP/1.1 mostra como as decisões de uma camada de aplicação dependem das "
        "propriedades oferecidas pelas camadas inferiores. TCP fornece entrega "
        "confiável e ordenada, enquanto HTTP define requisições, respostas e seus "
        "limites. A conexão persistente reduz reaberturas de transporte, mas exige "
        "delimitação inequívoca das mensagens; a semântica sem estado simplifica o "
        "processamento distribuído, enquanto aplicações podem acrescentar estado "
        "quando necessário. A representação em octetos e o uso explícito de tipos "
        "de mídia permitem transportar conteúdos diversos; TLS, quando usado com "
        "HTTPS, acrescenta proteção criptográfica que não existe no HTTP simples."
    )
    add_body(
        doc,
        "A execução prática confirma esses conceitos por meio de mensagens visíveis, "
        "códigos 200 e 404, JSON em UTF-8 e três requisições em uma conexão, "
        "incluindo POST com corpo delimitado. As "
        "funções de sessão e apresentação não correspondem a camadas autônomas na "
        "arquitetura TCP/IP, mas podem ser analisadas como responsabilidades distribuídas "
        "entre transporte, HTTP e mecanismos complementares. Assim, o protocolo "
        "equilibra interoperabilidade e extensibilidade com custos de conexão, "
        "complexidade de implementação e necessidade de proteção adicional em "
        "ambientes não confiáveis. O recorte pelo payload facilita compreender que "
        "o corpo não é um protocolo autônomo: é o conteúdo cuja representação e "
        "delimitação são coordenadas pelos cabeçalhos e pelo formato da mensagem HTTP."
    )

    add_heading(doc, "REFERÊNCIAS")
    add_reference(
        doc,
        "INTERNET ENGINEERING TASK FORCE (IETF). RFC 9110: HTTP Semantics. "
        "[S. l.]: IETF, 2022a. Disponível em: https://www.rfc-editor.org/rfc/rfc9110.html. "
        "Acesso em: 2 out. 2026.",
    )
    add_reference(
        doc,
        "INTERNET ENGINEERING TASK FORCE (IETF). RFC 9112: HTTP/1.1. "
        "[S. l.]: IETF, 2022b. Disponível em: https://www.rfc-editor.org/rfc/rfc9112.html. "
        "Acesso em: 2 out. 2026.",
    )
    add_reference(
        doc,
        "INTERNET ENGINEERING TASK FORCE (IETF). RFC 9293: Transmission Control "
        "Protocol (TCP). [S. l.]: IETF, 2022c. Disponível em: "
        "https://www.rfc-editor.org/rfc/rfc9293.html. Acesso em: 2 out. 2026.",
    )
    add_reference(
        doc,
        "INTERNET ENGINEERING TASK FORCE (IETF). RFC 8446: The Transport Layer "
        "Security (TLS) Protocol Version 1.3. [S. l.]: IETF, 2018. Disponível em: "
        "https://www.rfc-editor.org/rfc/rfc8446.html. Acesso em: 2 out. 2026.",
    )

    doc.core_properties.title = "Payload em HTTP/1.1: formato, delimitação e processamento do corpo da mensagem"
    doc.core_properties.subject = "Trabalho acadêmico de Arquitetura TCP/IP"
    doc.core_properties.author = "Gabriel Peruzzi Rodrigues"
    doc.save(OUTPUT)
    print(f"Documento gerado: {OUTPUT}")


if __name__ == "__main__":
    main()