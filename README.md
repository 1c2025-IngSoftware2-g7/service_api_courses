# ClassConnect - API Courses

## Contenidos
## Contenidos
1. Introducción
2. Arquitectura de componentes, Pre-requisitos, CI-CD, Test, Comandos, Despliegue en la nube
3. Test coverage
4. Base de datos
5. Funcionalidades

## 1. Introducción

Microservicio dedicado exclusivamente a Cursos. 

Historias de usuario realizadas: 
 - Creacion y gestión de cursos
 - Listado e inscripción a cursos
 - Inscripcion de estudiantes (Por el momento no está del todo completado)
 - Organización de modulos y recursos
 - Visualización de cursos


# 2. Arquitectura de componentes, Pre-requisitos, CI-CD, Test, Comandos, Despliegue en la nube

[Explicados en API Gateway](https://github.com/1c2025-IngSoftware2-g7/api_gateway)

# 3. Test coverage

[Coverage Course Service (codecov)](https://codecov.io/gh/1c2025-IngSoftware2-g7/service_api_courses)


# 4. Base de datos

## MongoDB 

El servicio de cursos utiliza MongoDB como base de datos, debido a su flexibilidad, escalabilidad horizontal y su capacidad para modelar estructuras de datos jerárquicas, altamente convenientes para representar cursos, módulos, recursos y relaciones dinámicas entre usuarios.

# 5. Funcionalidades

1. Creación y Gestión de Cursos

    Los cursos se representan como documentos con campos como nombre, descripción, docente titular, fecha de creación y estado (activo/cerrado).

    Se permite la actualización de sus atributos y metadatos.

2. Listado e Inscripción a Cursos

    Los usuarios pueden consultar cursos disponibles mediante filtros por nombre.

    Al inscribirse, se agrega una referencia al usuario dentro del curso.

3. Inscripción de Estudiantes

    Cada curso contiene una lista de estudiantes inscritos.

4. Organización de Módulos y Recursos

    Cada curso puede incluir módulos, con recursos, tareas y examenes.

5. Visualización de Cursos

Los usuarios acceden a los detalles del curso, incluyendo módulos, recursos, docentes y fechas relevantes.

6. Docentes Auxiliares

Los cursos pueden tener múltiples docentes asignados (un titular y auxiliares), con capacidad de agregar o quitar auxilixares.

7. Cursos Favoritos

    Tanto alumnos como docentes pueden marcar cursos como favoritos.

8. Visualización de Cursos Favoritos

    Los usuarios acceden a su listado de favoritos.

9. Feedback de Cursos (por Alumnos)

    Los alumnos registrados pueden dejar feedback en los cursos completados.

    Este feedback se almacena vinculado al curso y un comentario.

10. Feedback de Alumnos (por Docentes)

    Los docentes pueden evaluar el desempeño de los estudiantes inscritos.

    Se almacena vinculado al curso y al usuario, el docente puede agregar feedback de las tareas y examenes, al igual que una nota.

    Además, se puede poner una nota final al alumnos en un curso. Lo que demuestra que el alumno aprobó el curso.

11. Visualización de Feedbacks como Alumno

    Los alumnos pueden consultar las evaluaciones recibidas por parte de los docentes.

12. Visualización de Feedbacks del Curso

    Los docentes pueden acceder al feedback general de un curso, permitiendo evaluaciones de calidad y mejoras.

13. Apertura y Cierre de Cursos

    Los cursos poseen un estado (activo o cerrado) que define si aceptan nuevas inscripciones o solo están disponibles para los docente del curso.

    Este estado puede ser actualizado por sólo los docentes responsables.

14. Asignar correlativas a un Curso

    Un alumno sólo puede inscribirse a un curso si aprobó los cursos correlativos a este (en caso de tener correlatividad).
