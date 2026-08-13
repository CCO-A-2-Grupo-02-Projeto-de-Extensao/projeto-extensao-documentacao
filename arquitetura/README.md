# Diagrama de Arquitetura

Gera o diagrama `arquitetura_arandu.png` a partir do `diagrama_arandu.py`.

## Pré-requisitos

- Python 3
- Graphviz instalado no sistema (comando `dot` disponível no PATH)
  - Ubuntu/Debian: `sudo apt install graphviz`

## Como rodar

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python diagrama_arandu.py
```

O arquivo `arquitetura_arandu.png` será gerado/atualizado na mesma pasta.

Para sair do ambiente virtual: `deactivate`
