
import json
from datetime import date, datetime
from uuid import uuid4

# El archivo siempre estará junto a este script.
ARCHIVO_TAREAS = Path(__file__).with_name("tareas.json")from pathlib import Path

CARPETA_DATA = Path(__file__).with_name("data")
CARPETA_DATA.mkdir(exist_ok=True)

ARCHIVO_TAREAS = CARPETA_DATA / "tareas.json"

PRIORIDADES = {"baja", "media", "alta"}


def cargar_tareas():
    """Carga las tareas guardadas en JSON."""
    if not ARCHIVO_TAREAS.exists():
        return []

    try:
        with ARCHIVO_TAREAS.open("r", encoding="utf-8") as archivo:
            datos = json.load(archivo)

        if not isinstance(datos, list):
            raise ValueError("El JSON debe contener una lista.")

        return datos

    except (json.JSONDecodeError, OSError, ValueError) as error:
        raise RuntimeError(
            f"No se pudieron leer las tareas: {error}"
        ) from error


def guardar_tareas(tareas):
    """Guarda las tareas de forma persistente."""
    temporal = ARCHIVO_TAREAS.with_suffix(".tmp")

    with temporal.open("w", encoding="utf-8") as archivo:
        json.dump(
            tareas,
            archivo,
            ensure_ascii=False,
            indent=4
        )

    temporal.replace(ARCHIVO_TAREAS)


def organizar_tareas(
    accion,
    titulo=None,
    materia=None,
    fecha_limite=None,
    prioridad=None,
    tarea_id=None
):
    """
    Gestiona tareas universitarias.

    accion: crear, listar o completar
    titulo: nombre de la tarea
    materia: asignatura
    fecha_limite: formato AAAA-MM-DD
    prioridad: baja, media o alta
    tarea_id: identificador de la tarea
    """
    tareas = cargar_tareas()

    # LISTAR tareas pendientes
    if accion == "listar":
        pendientes = [
            tarea for tarea in tareas
            if not tarea["completada"]
        ]

        orden_prioridad = {
            "alta": 0,
            "media": 1,
            "baja": 2
        }

        pendientes.sort(
            key=lambda tarea: (
                orden_prioridad[tarea["prioridad"]],
                tarea["fecha_limite"] or "9999-12-31"
            )
        )

        if not pendientes:
            return "No tienes tareas pendientes."

        return json.dumps(
            pendientes,
            ensure_ascii=False,
            indent=2
        )

    # COMPLETAR una tarea
    if accion == "completar":
        if not tarea_id:
            return "Indica el ID de la tarea que deseas completar."

        for tarea in tareas:
            if tarea["id"] == tarea_id:
                if tarea["completada"]:
                    return f'La tarea "{tarea["titulo"]}" ya está completada.'

                tarea["completada"] = True
                tarea["completada_en"] = (
                    datetime.now().isoformat(timespec="seconds")
                )
                guardar_tareas(tareas)

                return f'Tarea completada: {tarea["titulo"]}.'

        return f"No existe ninguna tarea con ID {tarea_id}."

    # CREAR una tarea
    if accion == "crear":
        if not titulo or not titulo.strip():
            return "Falta el título de la tarea."

        if prioridad not in PRIORIDADES:
            return "Prioridad inválida: utiliza baja, media o alta."

        if fecha_limite:
            try:
                fecha = date.fromisoformat(fecha_limite)
                if fecha < date.today():
                    return (
                        "La fecha de entrega está en el pasado. "
                        "Confirma la fecha antes de registrar la tarea."
                    )
            except ValueError:
                return "Fecha inválida. Usa AAAA-MM-DD."

        tarea = {
            "id": uuid4().hex[:8],
            "titulo": titulo.strip(),
            "materia": materia or "General",
            "fecha_limite": fecha_limite,
            "prioridad": prioridad,
            "completada": False,
            "creada_en": datetime.now().isoformat(
                timespec="seconds"
            ),
            "completada_en": None
        }

        tareas.append(tarea)
        guardar_tareas(tareas)

        return (
            "Tarea guardada correctamente:\n"
            + json.dumps(tarea, ensure_ascii=False, indent=2)
        )

    return "Acción no válida. Usa crear, listar o completar."
