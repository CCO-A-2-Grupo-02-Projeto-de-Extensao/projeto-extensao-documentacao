#!/usr/bin/env python3
"""Gera as imagens de evidencia (antes/depois) das correcoes de seguranca.

Os trechos sao extraidos do historico do git, entao a imagem reflete o codigo
real que estava versionado — nao uma reconstrucao manual.
"""

import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from pygments import highlight
from pygments.formatters import ImageFormatter
from pygments.lexers import get_lexer_by_name

TRECHOS = Path(__file__).parent / "trechos"
SAIDA = Path(__file__).parent / "evidencias"

FONTE_TITULO = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONTE_TEXTO = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

FUNDO = (255, 255, 255)
TINTA = (24, 24, 27)
TINTA_FRACA = (113, 113, 122)
VERMELHO = (190, 40, 45)
VERDE = (22, 128, 70)

MARGEM = 32
LARGURA = 1180

ACHADOS = [
    {
        "n": "01",
        "slug": "chave-criptografica-fixa",
        "titulo": "Chave criptográfica fixa no código",
        "owasp": "OWASP A04:2025 Cryptographic Failures  ·  CWE-321",
        "arquivo": "backend — src/main/java/clube_tamoios/security/JwtUtil.java",
        "risco": "O segredo que assina os tokens JWT estava versionado em repositório "
                 "público. Com ele, qualquer pessoa forja um token válido para qualquer "
                 "usuário e acessa a API autenticada.",
        "antes": ("01_antes.java", "java"),
        "depois": ("01_depois.java", "java"),
        "commit": "3d5813b",
    },
    {
        "n": "02",
        "slug": "credenciais-fixas-aplicacao",
        "titulo": "Credenciais fixas no código (aplicação)",
        "owasp": "OWASP A02:2025 Security Misconfiguration  ·  CWE-798",
        "arquivo": "backend — src/main/resources/application.properties",
        "risco": "Senha do banco e do usuário administrativo gravadas em texto puro no "
                 "arquivo de configuração versionado.",
        "antes": ("02_antes.properties", "properties"),
        "depois": ("02_depois.properties", "properties"),
        "commit": "3d5813b",
    },
    {
        "n": "03",
        "slug": "credencial-fixa-infraestrutura",
        "titulo": "Credencial fixa no código (infraestrutura)",
        "owasp": "OWASP A02:2025 Security Misconfiguration  ·  CWE-798",
        "arquivo": "infraestrutura — infra_arandu.sh",
        "risco": "Senha do banco RDS fixa no script de provisionamento, idêntica em "
                 "todos os ambientes criados. Passou a ser gerada aleatoriamente a cada "
                 "provisionamento.",
        "antes": ("03_antes.sh", "bash"),
        "depois": ("03_depois.sh", "bash"),
        "commit": "784e135",
    },
    {
        "n": "04",
        "slug": "token-em-log",
        "titulo": "Dado sensível gravado em log",
        "owasp": "OWASP A09:2025 Security Logging & Alerting Failures  ·  CWE-532",
        "arquivo": "backend — src/main/java/clube_tamoios/security/JwtFilter.java",
        "risco": "O filtro de autenticação imprimia o header Authorization completo a "
                 "cada requisição, expondo o token JWT nos logs do container.",
        "antes": ("04_antes.java", "java"),
        "depois": ("04_depois.java", "java"),
        "commit": "e47e03c",
    },
    {
        "n": "05",
        "slug": "logout-incompleto",
        "titulo": "Encerramento de sessão incompleto",
        "owasp": "OWASP A07:2025 Identification and Authentication Failures  ·  CWE-613",
        "arquivo": "frontend — src/components/Sidebar/Sidebar.jsx",
        "risco": "O botão \"Sair\" apenas navegava para a tela de login, sem remover o "
                 "token. A sessão continuava válida: bastava voltar para /dashboard para "
                 "reentrar, expondo a conta em máquinas compartilhadas.",
        "antes": ("05_antes.jsx", "jsx"),
        "depois": ("05_depois.jsx", "jsx"),
        "commit": "0b4af83",
    },
    {
        "n": "06",
        "slug": "sessao-invalida-sem-tratamento",
        "titulo": "Sessão inválida sem tratamento",
        "owasp": "OWASP A07:2025 Identification and Authentication Failures  ·  CWE-613",
        "arquivo": "frontend — src/services/api.js",
        "risco": "Não havia tratamento de resposta 401. Com token expirado ou revogado, "
                 "a aplicação mantinha o usuário na área autenticada exibindo tela vazia, "
                 "sem encerrar a sessão nem redirecionar ao login.",
        "antes": ("06_antes.js", "javascript"),
        "depois": ("06_depois.js", "javascript"),
        "commit": "e4cda2d",
    },
]


def render_codigo(caminho: Path, lexer_nome: str) -> Image.Image:
    codigo = caminho.read_text(encoding="utf-8").rstrip("\n")
    lexer = get_lexer_by_name(lexer_nome, stripnl=False)
    formatter = ImageFormatter(
        font_name="DejaVu Sans Mono",
        font_size=15,
        line_numbers=False,
        style="friendly",
        image_pad=14,
        line_pad=4,
    )
    png = highlight(codigo, lexer, formatter)
    return Image.open(io.BytesIO(png)).convert("RGB")


def quebrar(texto: str, fonte: ImageFont.FreeTypeFont, largura: int) -> list[str]:
    palavras, linhas, atual = texto.split(), [], ""
    for p in palavras:
        teste = f"{atual} {p}".strip()
        if fonte.getlength(teste) <= largura:
            atual = teste
        else:
            linhas.append(atual)
            atual = p
    if atual:
        linhas.append(atual)
    return linhas


def montar(achado: dict) -> Image.Image:
    f_titulo = ImageFont.truetype(FONTE_TITULO, 26)
    f_meta = ImageFont.truetype(FONTE_TEXTO, 15)
    f_arquivo = ImageFont.truetype(FONTE_TEXTO, 14)
    f_rotulo = ImageFont.truetype(FONTE_TITULO, 16)
    f_risco = ImageFont.truetype(FONTE_TEXTO, 15)
    f_rodape = ImageFont.truetype(FONTE_TEXTO, 13)

    img_antes = render_codigo(TRECHOS / achado["antes"][0], achado["antes"][1])
    img_depois = render_codigo(TRECHOS / achado["depois"][0], achado["depois"][1])

    largura_codigo = LARGURA - 2 * MARGEM - 6
    linhas_risco = quebrar(achado["risco"], f_risco, LARGURA - 2 * MARGEM)

    altura = (
        MARGEM + 34 + 26 + 24 + len(linhas_risco) * 22 + 26
        + 26 + img_antes.height + 30
        + 26 + img_depois.height + 28
        + 24 + MARGEM
    )

    tela = Image.new("RGB", (LARGURA, altura), FUNDO)
    d = ImageDraw.Draw(tela)
    y = MARGEM

    d.text((MARGEM, y), f"{achado['n']} · {achado['titulo']}", font=f_titulo, fill=TINTA)
    y += 34
    d.text((MARGEM, y), achado["owasp"], font=f_meta, fill=VERMELHO)
    y += 26
    d.text((MARGEM, y), achado["arquivo"], font=f_arquivo, fill=TINTA_FRACA)
    y += 24
    for linha in linhas_risco:
        d.text((MARGEM, y), linha, font=f_risco, fill=TINTA)
        y += 22
    y += 26

    for rotulo, img, cor in (
        ("ANTES", img_antes, VERMELHO),
        ("DEPOIS", img_depois, VERDE),
    ):
        d.text((MARGEM, y), rotulo, font=f_rotulo, fill=cor)
        y += 26
        if img.width > largura_codigo:
            nova_alt = int(img.height * largura_codigo / img.width)
            img = img.resize((largura_codigo, nova_alt), Image.LANCZOS)
        d.rectangle([MARGEM, y, MARGEM + 4, y + img.height], fill=cor)
        tela.paste(img, (MARGEM + 14, y))
        y += img.height + 30

    d.text(
        (MARGEM, altura - MARGEM - 4),
        f"Correção aplicada no commit {achado['commit']}",
        font=f_rodape,
        fill=TINTA_FRACA,
    )
    return tela


def main() -> None:
    SAIDA.mkdir(exist_ok=True)
    for achado in ACHADOS:
        img = montar(achado)
        destino = SAIDA / f"{achado['n']}-{achado['slug']}.png"
        img.save(destino)
        print(f"{destino.name}  {img.width}x{img.height}")


if __name__ == "__main__":
    main()
