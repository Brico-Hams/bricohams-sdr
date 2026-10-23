#!/usr/bin/env python3
"""Conserva HSTS en los bloques de tar1090 que anulan la herencia de add_header."""
import pathlib
import re
import sys

HEADER = 'add_header Strict-Transport-Security "max-age=15552000" always; '


def proteger(text):
    code = re.sub(
        r"""'(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*"|\#.*""",
        lambda match: " " * len(match[0]),
        text,
    )
    scopes = [{"first": None, "hsts": False}]
    stack = [scopes[0]]
    for token in re.finditer(r"[{}]|\badd_header\s+([A-Za-z0-9_-]+)", code):
        if token[0] == "{":
            scope = {"first": None, "hsts": False}
            scopes.append(scope)
            stack.append(scope)
        elif token[0] == "}":
            if len(stack) == 1:
                raise ValueError("Cierre de bloque nginx inesperado")
            stack.pop()
        else:
            if stack[-1]["first"] is None:
                stack[-1]["first"] = token.start()
            if token[1].lower() == "strict-transport-security":
                stack[-1]["hsts"] = True
    if len(stack) != 1:
        raise ValueError("Bloque nginx sin cerrar")
    offsets = [scope["first"] for scope in scopes
               if scope["first"] is not None and not scope["hsts"]]
    for offset in sorted(offsets, reverse=True):
        text = text[:offset] + HEADER + text[offset:]
    return text


if __name__ == "__main__":
    path = pathlib.Path(sys.argv[1])
    text = path.read_text(encoding="utf-8")
    result = proteger(text)
    if result != text:
        path.write_text(result, encoding="utf-8")
