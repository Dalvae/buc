# Plan de Desarrollo del Frontend (Revisión Final)

## 1. Estado Actual y Tareas Completadas

Hemos completado con éxito las fases fundamentales del desarrollo, estableciendo una arquitectura robusta y las funcionalidades principales para todos los roles.

-   **[COMPLETADO] Fase de Theming:** Sistema de temas `light`/`dark`/`brand` implementado y funcional.
-   **[COMPLETADO] Fase de Autenticación:** Flujo de Login/Registro con gestión de estado persistente (Zustand).
-   **[COMPLETADO] Fase de Navegación y Rutas:** Navegación condicional (Auth/App), rutas protegidas (`AuthGuard`, `AdminGuard`) y enrutamiento dinámico para la administración.
-   **[COMPLETADO] Fase de Configuración de Usuario:** Pantalla de perfil con cambio de tema, actualización de nombre y eliminación de cuenta.
-   **[COMPLETADO] Fase de Administración (Núcleo):**
    -   Gestión de la Compañía Demo (listar y mover usuarios en lote).
    -   Gestión de Compañías Reales (CRUD de Usuarios y Áreas).
    -   Asignación de áreas a usuarios.
    -   Constructor de Asignaciones de Auditoría a partir de plantillas.
-   **[COMPLETADO] Fase de Auditor (Núcleo):**
    -   Vista "Mis Asignaciones".
    -   Pantalla para responder a las auditorías con renderizado dinámico de preguntas.

## 2. Tareas Pendientes: Pulido y Finalización

Esta fase se centra en completar las funcionalidades, pulir la experiencia de usuario y asegurar la estabilidad de la aplicación.

### 2.1. Completar el `QuestionRenderer`

-   **Objetivo:** Dar soporte a todos los tipos de preguntas definidos en el backend.
-   **Tareas:**
    1.  **Implementar `MULTIPLE_CHOICE_MULTIPLE`:**
        -   Renderizar una lista de componentes `<Checkbox>` de Tamagui para permitir la selección múltiple.
        -   El estado de la respuesta será un array de strings.
    2.  **Implementar `RATING_SCALE`:**
        -   Renderizar un componente `<Slider>` de Tamagui o una serie de botones para representar la escala (ej. 1 a 5).
        -   La respuesta será un número.
    3.  **Implementar `SECTION_HEADER`:**
        -   Renderizar un componente de solo lectura, como un `H3` o `H4` con un `Separator`, para dividir visualmente la auditoría. No tendrá un valor de respuesta.

### 2.2. Implementar Funcionalidades Faltantes en Administración

-   **Objetivo:** Completar las acciones pendientes en los módulos de administración.
-   **Tareas:**
    1.  **Activar/Desactivar Usuario:**
        -   Crear un hook `useUpdateUserStatus`.
        -   Conectar el botón "Desactivar" en la `UserManagementView` a este hook, mostrando un diálogo de confirmación.
    2.  **Crear Compañía:**
        -   Crear un hook `useCreateCompany`.
        -   En la página `/admin`, añadir un botón "Nueva Compañía" que abra un `Sheet` con un formulario para crearla.
    3.  **Gestión de Plantillas de Auditoría (CRUD):**
        -   Crear una nueva sección en la página `/admin` para gestionar las plantillas.
        -   Implementar los hooks y vistas para crear, editar y eliminar `AuditTemplate` y sus `QuestionTemplate`s. Esta es una tarea mayor que puede requerir su propio "Constructor de Plantillas".

### 2.3. Pulido de la Interfaz de Usuario (UI/UX)

-   **Objetivo:** Mejorar la experiencia de usuario y la consistencia visual.
-   **Tareas:**
    1.  **Indicadores de Carga y Éxito:**
        -   Asegurarse de que todos los botones que ejecutan una mutación muestren un estado de carga (`isPending`).
        -   Utilizar el componente `<Toast>` de Tamagui para mostrar notificaciones de éxito (ej. "Perfil actualizado correctamente") o de error de forma no intrusiva.
    2.  **Manejo de Estados Vacíos:**
        -   En todas las listas (usuarios, áreas, asignaciones), mostrar un mensaje amigable cuando la lista esté vacía (ej. "No hay usuarios en esta compañía. ¡Añade uno!").
    3.  **Consistencia en Formularios:**
        -   Crear componentes de formulario reutilizables (ej. `FormField`, `FormSelect`) para estandarizar la apariencia de etiquetas, inputs y mensajes de error en toda la aplicación.
    4.  **Implementar Calendario:**
        -   Reemplazar el `Input` de texto para `due_date` en el constructor de asignaciones por un componente de calendario real. Se puede usar una librería como `react-native-calendars` que es compatible con web.

## 3. Fase Final: Verificación y Build

-   **Objetivo:** Asegurar que la aplicación está libre de errores y lista para ser desplegada.
-   **Tareas:**
    1.  **Linting Completo:**
        -   Ejecutar `yarn biome check --apply .` en el directorio `frontend` para corregir cualquier problema de formato y estilo.
    2.  **Build de Producción (Next.js):**
        -   Ejecutar `yarn web:prod` y asegurar que el build se completa sin errores.
    3.  **Build de Producción (Expo):**
        -   Ejecutar `yarn native:prebuild` y asegurar que el pre-build de Expo se completa sin errores.

Este plan nos da una ruta clara hacia la finalización del proyecto.