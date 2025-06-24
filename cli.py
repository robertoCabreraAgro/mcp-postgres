#!/usr/bin/env python3
"""Interact with the database using natural language via the GPT API."""

import json
import os
import sys
from typing import Optional

import openai

from tool import agregar, obtener, eliminar

MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
API_KEY = os.getenv("OPENAI_API_KEY")


def handle_query(query: str) -> str:
    """Send a natural language query to GPT and run the mapped tool."""
    system_prompt = (
        "Convierte la solicitud del usuario en un objeto JSON que indique la accion\n"
        '{"action": "agregar", "texto": "..."} | '
        '{"action": "obtener", "id": 1} | '
        '{"action": "eliminar", "id": 1}.\n'
        "Responde solo con el JSON."
    )

    resp = openai.ChatCompletion.create(
        model=MODEL,
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": query}],
    )
    content = resp.choices[0].message.content
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return f"Respuesta inesperada: {content}"

    action = data.get("action")
    if action == "agregar":
        return agregar(data.get("texto", ""))
    if action == "obtener":
        return obtener(int(data.get("id")))
    if action == "eliminar":
        return eliminar(int(data.get("id")))
    return f"Accion no soportada: {action}"


def main() -> None:
    """Run queries provided via CLI or interactively."""
    if API_KEY is None:
        raise RuntimeError("OPENAI_API_KEY environment variable not set")
    openai.api_key = API_KEY

    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        print(handle_query(query))
        return

    print("Escribe consultas en lenguaje natural. 'salir' para terminar.")
    while True:
        try:
            query = input("GPT> ")
        except EOFError:
            break
        if query.strip().lower() in {"salir", "exit", "quit"}:
            break
        result = handle_query(query)
        print(result)


if __name__ == "__main__":
    main()
