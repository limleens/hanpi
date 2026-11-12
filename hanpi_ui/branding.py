"""Shared, bundled typefaces, including before Gradio authentication."""
from base64 import b64encode
from pathlib import Path


def embedded_fonts():
    root=Path(__file__).parent/'fonts'
    rules=[]
    for name,family,weights in (
        ('fredoka','Fredoka','300 700'),
        ('plus-jakarta-sans','Plus Jakarta Sans','200 800'),
    ):
        data=b64encode((root/f'{name}-latin-wght-normal.woff2').read_bytes()).decode('ascii')
        rules.append(f"@font-face{{font-family:'{family}';font-style:normal;font-weight:{weights};"
                     f"font-display:swap;src:url(data:font/woff2;base64,{data}) format('woff2');}}")
    return '\n'.join(rules)+'\n'


FONT_CSS=embedded_fonts()
