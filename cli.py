#!/usr/bin/env python3
"""Interact with the database using natural language via the GPT API."""

import json
import os
import sys

import openai

from tool import agregar, obtener, eliminar

MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
API_KEY = os.getenv("OPENAI_API_KEY")


def main() -> None:
    if API_KEY is None:
        raise RuntimeError("OPENAI_API_KEY environment variable not set")
    openai.api_key = API_KEY

    if len(sys.argv) < 2:
        print("Uso: cli.py <consulta>")
        return
    query = " ".join(sys.argv[1:])

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
        print("Respuesta inesperada:", content)
        return

    action = data.get("action")
    if action == "agregar":
        result = agregar(data.get("texto", ""))
    elif action == "obtener":
        result = obtener(int(data.get("id")))
    elif action == "eliminar":
        result = eliminar(int(data.get("id")))
    else:
        result = f"Accion no soportada: {action}"
    print(result)


if __name__ == "__main__":
    main()
