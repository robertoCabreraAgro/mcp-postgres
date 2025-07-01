import os
import re
import warnings

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain.chains import create_sql_query_chain
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SAWarning

# Ignorar advertencias de SQLAlchemy que no son críticas
warnings.filterwarnings("ignore", category=SAWarning)

# --- 1. Carga de Configuración y Conexión ---
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
# El modo DEBUG es útil para ver la consulta SQL generada
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

# Asegurarse de que las variables de entorno están cargadas
if not OPENAI_API_KEY or not DATABASE_URL:
    print(
        "🚨 Error: Asegúrate de que las variables de entorno OPENAI_API_KEY y DATABASE_URL están definidas en tu archivo .env"
    )
    exit()

# Configuración del LLM y conexión a la base de datos
LLM = ChatOpenAI(model="gpt-4o", temperature=0, api_key=OPENAI_API_KEY)
engine = create_engine(DATABASE_URL)


# --- 2. Definición del Dominio de Inventario y Prompts ---
INVENTORY_DOMAIN = {
    "tables": [
        "stock_quant",
        "stock_move",
        "stock_warehouse",
        "stock_location",
        "product_product",
        "product_template",
    ],
    # CORRECCIÓN: La variable para la pregunta del usuario DEBE ser {input} para ser compatible con `create_sql_query_chain`.
    "prompt": """
Eres un experto en el módulo de Inventario de Odoo 18.0 para PostgreSQL.
Basado en el esquema de la base de datos a continuación, las reglas y la pregunta del usuario, genera una consulta SQL válida para PostgreSQL.

**Esquema de la Base de Datos:**
{table_info}

**Reglas Importantes:**
- Genera SOLO la consulta SQL, sin explicaciones, sin markdown, solo el código SQL.
- Limita tus resultados a {top_k} filas a menos que el usuario lo pida explícitamente.
- Las tablas y campos usan snake_case (ej: product_template, stock_quant).
- Los campos de texto traducibles (como 'name') son de tipo jsonb. Para obtener el nombre preferido del producto, usa:
  `COALESCE(name->>'es_ES', name->>'en_US')`
- Para búsquedas de texto no exactas, usa el operador ILIKE con '%'.

**Sobre ubicaciones y almacenes:**
- `stock_quant` apunta a `stock_location` a través de `location_id`.
- `stock_location` es una estructura jerárquica. La jerarquía se representa en `parent_path`, que contiene los IDs de sus ancestros.
- `stock_warehouse` define su ubicación raíz con `lot_stock_id`.
- Para consultar el inventario dentro de un almacén (incluyendo sububicaciones), filtra ubicaciones (`stock_location`) cuyo `parent_path` contenga el ID de la ubicación principal (`lot_stock_id`) del almacén (`stock_warehouse`).
- Este filtro debe hacerse así:
  `sl.parent_path LIKE '%' || sw.lot_stock_id || '/%' OR sl.id = sw.lot_stock_id`

**Relaciones clave:**
- `stock_quant.product_id` → `product_product.id`
- `product_product.product_tmpl_id` → `product_template.id`
- `stock_quant.location_id` → `stock_location.id`
- `stock_warehouse.lot_stock_id` → `stock_location.id`

**Consideraciones especiales sobre almacenes:**
- El campo `stock_warehouse.code` es el identificador técnico único del almacén. El campo `stock_warehouse.name` es un nombre descriptivo para humanos.
- Si el usuario menciona el nombre visible de un almacén (por ejemplo, "CODAGEM" o "OBREGON"), asume que se refiere a `stock_warehouse.name`.
- Si estás filtrando por `stock_warehouse`, verifica si la condición debe aplicarse sobre `code` o sobre `name`, según el contexto de la pregunta del usuario.

**Pregunta del Usuario:**
{input}

**Consulta SQL:**
""",
}

# Prompt para convertir los resultados de la BD en una respuesta en lenguaje natural
system_prompt_postprocess = """
Eres un asistente de inventario amigable y servicial.
Tu tarea es tomar la pregunta original del usuario y los resultados de la base de datos y formular una respuesta clara, concisa y en lenguaje natural.

- Resume los hallazgos de forma amable.
- Si los resultados son una lista, formatéalos de manera legible (por ejemplo, con viñetas).
- Si no hay resultados (`result` está vacío o es `None`), informa al usuario educadamente que no encontraste información para su consulta.
- Responde siempre en el mismo idioma de la pregunta del usuario.

**Pregunta Original del Usuario:**
{question}

**Resultados de la Base de Datos:**
{result}

**Respuesta Final:**
"""

# Prompt para el modo de chat general
system_prompt_chat = """
Eres un asistente conversacional amigable. Tu propósito es saludar, conversar y responder preguntas generales.
Si un usuario te hace una pregunta que parece ser sobre datos específicos (como "cuántos productos hay", "dame el stock de X"), debes indicarle amablemente que puede hacer ese tipo de preguntas directamente para que el sistema de inventario las responda.
Por ejemplo, si preguntan "¿Sabes cuántas mesas tenemos?", podrías responder: "¡Hola! Para saber el stock de un producto, puedes preguntarme directamente, por ejemplo: 'muéstrame el stock de las mesas'".
"""


# --- 3. Funciones de Utilidad y Seguridad ---


def classify_intent(user_input: str) -> str:
    """Clasifica si la entrada es una consulta de datos o una conversación."""
    keywords_sql = [
        "muestrame",
        "consultar",
        "cuantos",
        "cuales",
        "listar",
        "productos",
        "stock",
        "inventario",
        "almacen",
        "existencias",
        "dame",
        "busca",
        "select",
        "where",
        "join",
        "hay",
    ]
    if any(keyword in user_input.lower().split() for keyword in keywords_sql):
        return "INVENTORY_QUERY"
    return "CHAT"


def extract_sql_from_markdown(text: str) -> str:
    """Extrae el código SQL de un bloque de markdown si está presente."""
    match = re.search(r"```(?:sql)?\n(.*?)\n```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


def validate_sql(sql: str) -> bool:
    """Valida que la consulta sea un SELECT seguro."""
    sql_clean = sql.strip().lower()
    if not sql_clean.startswith("select"):
        print("🚨 Fallo de validación: La consulta no comienza con SELECT.")
        return False

    forbidden_keywords = [
        "insert",
        "update",
        "delete",
        "drop",
        "alter",
        "create",
        "truncate",
        "grant",
        "revoke",
    ]
    if any(kw in sql_clean.split() for kw in forbidden_keywords):
        print(
            f"🚨 Fallo de validación: La consulta contiene una palabra clave prohibida."
        )
        return False

    return True


def run_query(sql_query: str):
    """Ejecuta una consulta SQL y devuelve los resultados como una lista de tuplas."""
    if not validate_sql(sql_query):
        raise ValueError("Consulta SQL no válida o insegura.")

    if DEBUG:
        print(f"⚙️ SQL Ejecutando:\n{sql_query}\n")

    with engine.connect() as connection:
        result = connection.execute(text(sql_query))
        return result.fetchall()


# --- 4. Cadenas de LangChain ---


def create_inventory_chain():
    """Crea la cadena de LangChain completa para consultas de inventario."""
    db = SQLDatabase(engine, include_tables=INVENTORY_DOMAIN["tables"])

    prompt_template = PromptTemplate.from_template(INVENTORY_DOMAIN["prompt"])

    # Cadena para generar la consulta SQL
    sql_query_chain = create_sql_query_chain(LLM, db, prompt=prompt_template)

    # Cadena para dar formato a la respuesta final en lenguaje natural
    answer_prompt = PromptTemplate.from_template(system_prompt_postprocess)
    answer_chain = answer_prompt | LLM | StrOutputParser()

    # CORRECCIÓN: Cadena completa que maneja el mapeo de `input` a `question`.
    chain = (
        # Guardamos la pregunta original en la clave 'question' para el prompt final.
        RunnablePassthrough.assign(question=lambda x: x["input"])
        # La clave 'input' original se pasa automáticamente a sql_query_chain.
        .assign(sql_query_raw=sql_query_chain)
        .assign(sql_query_clean=lambda x: extract_sql_from_markdown(x["sql_query_raw"]))
        .assign(result=lambda x: run_query(x["sql_query_clean"]))
        | answer_chain
    )

    return chain


# --- 5. Flujo Principal de la Consola ---


def main_console():
    """Inicia el bucle principal de la aplicación de consola."""
    print("--- 🤖 Asistente de Inventario Odoo (LangChain) ---")
    print(
        "Escribe tu consulta sobre inventario, una pregunta general o 'salir' para terminar.\n"
    )

    inventory_chain = create_inventory_chain()

    while True:
        user_input = input("💬 Tú: ")
        if user_input.lower() in ["salir", "exit", "quit"]:
            print("👋 ¡Adiós!")
            break

        try:
            intent = classify_intent(user_input)

            if intent == "INVENTORY_QUERY":
                print("🧠 Intención: Consulta de Inventario. Procesando...")

                # CORRECCIÓN: La clave de entrada debe ser 'input' para que `create_sql_query_chain` la acepte.
                final_answer = inventory_chain.invoke(
                    {"input": user_input, "top_k": 100}
                )

                print(f"\n✅ Pablos\n{final_answer}\n")

            elif intent == "CHAT":
                print("🧠 Intención: Chat General. Respondiendo...")

                chat_prompt = PromptTemplate.from_template(
                    "{system}\n\nUsuario: {question}"
                )
                chat_chain = chat_prompt | LLM | StrOutputParser()

                chat_response = chat_chain.invoke(
                    {"system": system_prompt_chat, "question": user_input}
                )
                print(f"\n✅ Asistente de Chat: {chat_response}\n")

        except Exception as e:
            print(f"💥 Ha ocurrido un error inesperado: {e}\n")
            if DEBUG:
                import traceback

                traceback.print_exc()


if __name__ == "__main__":
    main_console()
