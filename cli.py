import os
import re
from dotenv import load_dotenv
import openai
from sqlalchemy import create_engine, text

# 1️⃣ Cargar configuración
load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
API_KEY = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

client = openai.OpenAI(api_key=API_KEY)
engine = create_engine(DATABASE_URL)

# 2️⃣ Prompts

system_prompt_sql = """
Eres un generador de consultas SQL para una base de datos PostgreSQL de Odoo 18.
Convierte preguntas naturales a consultas SELECT.
Reglas:
- Las tablas usan snake_case: (ej: product_template, res_users, account_move).
- Los campos traducibles (ej: name) están en jsonb, usa name->>'en_US'.
- Las búsquedas de texto usan ILIKE.
- Solo genera SQL válido, sin explicaciones, sin comentarios, sin resultado simulado.
"""

system_prompt_postprocess = """
Eres un asistente que entrega resultados al usuario basados en datos de la base de datos.

Recibes:
- La pregunta original del usuario.
- Los datos crudos resultado de la consulta.

Devuelve:
- Una respuesta natural, amigable y clara mostrando los resultados.
- Si no hay resultados, indícalo de forma educada.
"""

system_prompt_chat = """
Eres un asistente conversacional amigable.
Puedes:
- Saludar, conversar y responder preguntas generales.
- Si te preguntan algo de la base de datos, indícale que puede usar comandos de consulta.
"""

# 3️⃣ Clasificación de intención

def classify_intent(user_input):
    keywords_sql = ['mostrar', 'consultar', 'productos', 'clientes', 'ventas', 'pedidos', 'orden', 'facturas', 'SELECT', 'WHERE', 'JOIN']
    for keyword in keywords_sql:
        if keyword.lower() in user_input.lower():
            return 'SQL'
    return 'CHAT'

# 4️⃣ Validación de seguridad básica

def validate_sql(sql):
    sql_clean = sql.strip().lower()
    if not sql_clean.startswith("select"):
        return False
    if any(kw in sql_clean for kw in ['insert', 'update', 'delete', 'drop', 'alter', 'create', 'truncate']):
        return False
    return True

# 5️⃣ Consola principal

def main_console():
    print("--- MCP Odoo18 SQL+Chat ---")
    print("Escribe tu consulta o 'exit' para salir.\n")

    while True:
        user_input = input("💬 You: ")
        if user_input.lower() in ["salir", "exit", "quit"]:
            print("👋 Adiós!")
            break

        try:
            intent = classify_intent(user_input)

            if intent == 'SQL':
                # Generar el SQL
                sql_response = client.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt_sql},
                        {"role": "user", "content": user_input}
                    ]
                )
                sql_code = sql_response.choices[0].message.content.strip()
                sql_code = re.sub(r'```sql\s*|\s*```', '', sql_code, flags=re.IGNORECASE).strip()

                if not validate_sql(sql_code):
                    print("⚠ SQL no permitido o peligroso.")
                    print(f"SQL generado: {sql_code}")
                    continue

                # Ejecutar SQL
                with engine.connect() as connection:
                    result = connection.execute(text(sql_code))
                    rows = result.fetchall()

                # Preparar datos crudos
                if not rows:
                    result_text = "No results"
                else:
                    result_text = "\n".join(["\t".join(map(str, row)) for row in rows])

                # Post-procesar la respuesta final natural
                final_response = client.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt_postprocess},
                        {"role": "user", "content": f"Consulta original: {user_input}\nResultados:\n{result_text}"}
                    ]
                )

                print(final_response.choices[0].message.content)

            elif intent == 'CHAT':
                chat_response = client.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt_chat},
                        {"role": "user", "content": user_input}
                    ]
                )
                print(chat_response.choices[0].message.content)

        except Exception as e:
            print(f"💥 Error: {e}\n")

if __name__ == "__main__":
    main_console()
