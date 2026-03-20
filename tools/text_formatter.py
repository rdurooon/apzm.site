"""
Sistema de formatação de texto com suporte a:
- ** para negrito
- -- para itálico
- __ para sublinhado
- ~~ para riscado
- || para censurado (texto preto)
"""

import re
from html import escape


def format_text_to_html(text: str) -> str:
    """
    Converte texto com símbolos de formatação para HTML.
    
    Símbolos:
    - **texto** -> <strong>texto</strong>
    - --texto-- -> <em>texto</em>
    - __texto__ -> <u>texto</u>
    - ~~texto~~ -> <s>texto</s>
    - ||texto|| -> <span class="censored">texto</span>
    """
    if not text:
        return ""
    
    # Escapar HTML para evitar injeção
    text = escape(text)
    
    # Ordem importa: fazer replacements de dentro para fora para evitar conflitos
    # Negrito
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    
    # Itálico
    text = re.sub(r'--(.+?)--', r'<em>\1</em>', text)
    
    # Sublinhado
    text = re.sub(r'__(.+?)__', r'<u>\1</u>', text)
    
    # Riscado
    text = re.sub(r'~~(.+?)~~', r'<s>\1</s>', text)
    
    # Censurado (com classe CSS para estilização)
    text = re.sub(r'\|\|(.+?)\|\|', r'<span class="text-censored">\1</span>', text)
    
    return text


def sanitize_formatting_text(text: str) -> str:
    """
    Sanitiza o texto de formatação, removendo caracteres perigosos.
    Mantém os símbolos de formatação intactos.
    """
    if not text:
        return ""
    
    # Remove caracteres de controle (exceto quebras de linha)
    text = ''.join(char for char in text if ord(char) >= 32 or char == '\n')
    
    return text.strip()
