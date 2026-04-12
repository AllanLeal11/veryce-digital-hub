from crewai import Crew, Task, Process
from agents import (
    coordinador, ventas, analista, desarrollador,
    project_manager, soporte, marketing, disenador, admin
)

def create_crew(task_description: str):
    task = Task(
        description=task_description,
        expected_output="Respuesta completa y organizada del equipo",
        agent=coordinador
    )

    crew = Crew(
        agents=[coordinador, ventas, analista, desarrollador, 
                project_manager, soporte, marketing, disenador, admin],
        tasks=[task],
        process=Process.sequential,   # o hierarchical si quieres que el coordinador dirija
        verbose=2,
        memory=True
    )
    return crew