
import os
import json
from openai import OpenAI
from tools import organizar_tareas

# ==========================================
# CONFIGURACIÓN DEL AGENTE
# ==========================================

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise RuntimeError(
        "No se encontró OPENAI_API_KEY. "
        "Configúrala en la terminal antes de ejecutar el agente."
    )

client = OpenAI(api_key=api_key)

MODELO = "gpt-4.1-mini"

INSTRUCCIONES = """
Eres FocusBuddy, un asistente universitario inteligente.

Ayudas al estudiante a:
- Responder preguntas académicas.
- Explicar conceptos paso a paso.
- Organizar tareas y fechas de entrega.
- Consultar tareas pendientes.
- Marcar tareas como completadas.

HERRAMIENTAS:
Tienes la herramienta organizar_tareas.

Úsala cuando el estudiante:
- Quiera registrar una nueva tarea.
- Pregunte por sus tareas pendientes.
- Quiera completar una tarea existente.

REGLAS:
- No afirmes que guardaste una tarea si la herramienta falló.
- Al crear una tarea, solicita los datos que falten.
- No inventes fechas ni confirmes datos que no proporcionó
  el estudiante.
- Si no especifica prioridad, puedes proponer "media".
- Antes de completar una tarea, identifica claramente cuál es.
- Si hay varias tareas con nombres similares, pregunta cuál.
- Usa los resultados reales de las herramientas.
- Responde siempre en español.
- No marques tareas como completadas sin una petición clara.
"""

# ==========================================
# DEFINICIÓN DE LA TOOL PARA OPENAI
# ==========================================

TOOLS = [
    {
        "type": "function",
        "name": "organizar_tareas",
        "description": (
            "Crea tareas universitarias, lista tareas pendientes "
            "o marca una tarea como completada. "
            "Los cambios se guardan en un archivo JSON local."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "accion": {
                    "type": "string",
                    "enum": ["crear", "listar", "completar"]
                },
                "titulo": {
                    "type": ["string", "null"]
                },
                "materia": {
                    "type": ["string", "null"]
                },
                "fecha_limite": {
                    "type": ["string", "null"],
                    "description": "Fecha AAAA-MM-DD"
                },
                "prioridad": {
                    "type": ["string", "null"],
                    "enum": ["baja", "media", "alta", None]
                },
                "tarea_id": {
                    "type": ["string", "null"],
                    "description": "ID exacto de la tarea"
                }
            },
            "required": [
                "accion",
                "titulo",
                "materia",
                "fecha_limite",
                "prioridad",
                "tarea_id"
            ],
            "additionalProperties": False
        },
        "strict": True
    }
]


# ==========================================
# EJECUCIÓN DE LAS HERRAMIENTAS
# ==========================================

def ejecutar_tool(nombre, argumentos):
    if nombre == "organizar_tareas":
        return organizar_tareas(**argumentos)

    return "Error: herramienta desconocida."


# ==========================================
# CONVERSACIÓN Y CICLO DEL AGENTE
# ==========================================

historial = []


def responder(pregunta):
    historial.append({
        "role": "user",
        "content": pregunta
    })

    respuesta = client.responses.create(
        model=MODELO,
        instructions=INSTRUCCIONES,
        input=historial,
        tools=TOOLS
    )

    # El modelo puede pedir una o varias herramientas.
    while True:
        # Conservar la salida del modelo, incluidos los tool calls.
        historial.extend(respuesta.output)

        llamadas = [
            elemento
            for elemento in respuesta.output
            if elemento.type == "function_call"
        ]

        if not llamadas:
            return respuesta.output_text

        # Ejecutar cada herramienta y devolver su resultado a OpenAI.
        for llamada in llamadas:
            try:
                argumentos = json.loads(llamada.arguments)
                resultado = ejecutar_tool(
                    llamada.name,
                    argumentos
                )
            except Exception as error:
                resultado = (
                    f"No se pudo ejecutar la herramienta: {error}"
                )

            historial.append({
                "type": "function_call_output",
                "call_id": llamada.call_id,
                "output": str(resultado)
            })

        # El modelo recibe los resultados y redacta la respuesta final.
        respuesta = client.responses.create(
            model=MODELO,
            instructions=INSTRUCCIONES,
            input=historial,
            tools=TOOLS
        )


def main():
    print("\n🎓 FocusBuddy — Asistente universitario")
    print("Puedes pedirme que registre u organice tareas.")
    print("Escribe 'salir' para terminar.\n")

    while True:
        pregunta = input("Tú: ").strip()

        if pregunta.lower() == "salir":
            print("FocusBuddy: ¡Hasta pronto!")
            break

        if not pregunta:
            continue

        try:
            resultado = responder(pregunta)
            print("\nFocusBuddy:", resultado, "\n")
        except Exception as error:
            # Evitar que la conversación quede con un turno
            # incompleto si la API devuelve un error.
            if historial and historial[-1].get("role") == "user":
                historial.pop()

            print("\nError al consultar OpenAI:", error)


if __name__ == "__main__":
    main()
