# Guía de Despliegue

Este documento proporciona las instrucciones para desplegar el backend, frontend y compilar la aplicación móvil del proyecto Buc.

## 1. Despliegue del Backend (VPS con PostgreSQL)

Estos pasos asumen que tienes un servidor VPS (ej. Ubuntu) con acceso `sudo` y PostgreSQL instalado.

### 1.1. Requisitos Previos

-   Un servidor VPS.
-   `git`, `python3`, `python3-venv` y `pip` instalados.
-   PostgreSQL instalado y en ejecución.

### 1.2. Configuración de la Base de Datos

1.  **Accede a PostgreSQL:**
    ```bash
    sudo -u postgres psql
    ```

2.  **Crea la base de datos y el usuario:** Reemplaza `buc_user` y `your_strong_password` con tus propios valores.
    ```sql
    CREATE DATABASE buc;
    CREATE USER buc_user WITH PASSWORD 'your_strong_password';
    ALTER ROLE buc_user SET client_encoding TO 'utf8';
    ALTER ROLE buc_user SET default_transaction_isolation TO 'read committed';
    ALTER ROLE buc_user SET timezone TO 'UTC';
    GRANT ALL PRIVILEGES ON DATABASE buc TO buc_user;
    \q
    ```

### 1.3. Despliegue de la Aplicación

1.  **Clona el repositorio:**
    ```bash
    git clone <URL_DEL_REPOSITORIO>
    cd buc
    ```

2.  **Crea y activa el entorno virtual:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Genera y instala las dependencias:**
    ```bash
    pip install uv
    uv pip install -r backend/pyproject.toml --no-cache-dir
    ```

4.  **Crea el archivo `.env`:** En la raíz del proyecto, crea un archivo `.env` y llénalo con tus variables de entorno. Un ejemplo:
    ```env
    # Backend
    SECRET_KEY=tu_super_secreto_aqui
    FIRST_SUPERUSER=admin@example.com
    FIRST_SUPERUSER_PASSWORD=tu_contraseña_de_admin
    
    # Base de Datos
    POSTGRES_SERVER=localhost
    POSTGRES_PORT=5432
    POSTGRES_USER=buc_user
    POSTGRES_PASSWORD=your_strong_password
    POSTGRES_DB=buc
    
    # CORS - Reemplaza con el dominio de tu frontend en Vercel
    BACKEND_CORS_ORIGINS=["https://tu-proyecto.vercel.app"] 
    ```

5.  **Ejecuta las migraciones de la base de datos:**
    ```bash
    cd backend
    alembic upgrade head
    cd ..
    ```

6.  **Inicia el servidor con Gunicorn:**
    ```bash
    gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 backend.app.main:app
    ```
    Se recomienda gestionar este proceso con `systemd` para que se reinicie automáticamente.

## 2. Despliegue del Frontend (Vercel)

1.  **Conecta tu Repositorio:** En tu dashboard de Vercel, importa el proyecto desde tu repositorio de GitHub.
2.  **Configuración del Proyecto:** Vercel detectará automáticamente que es un monorepo con Next.js. La configuración por defecto debería funcionar.
3.  **Variables de Entorno:** En la configuración de tu proyecto en Vercel, ve a "Settings" > "Environment Variables" y añade la siguiente variable:
    -   `VITE_API_URL`: La URL pública de tu backend en el VPS (ej. `https://api.tu-dominio.com`).

Vercel se encargará de construir y desplegar tu frontend automáticamente en cada `push` a la rama principal.

## 3. Build de la Aplicación Móvil (EAS)

Para compilar los archivos `.apk`/`.aab` (Android) y `.ipa` (iOS) necesitas usar Expo Application Services (EAS).

1.  **Instala el CLI de EAS:**
    ```bash
    npm install -g eas-cli
    ```

2.  **Inicia sesión y configura:**
    ```bash
    eas login
    cd frontend
    eas project:init
    ```

3.  **Construye la aplicación:**
    -   Para Android:
        ```bash
        eas build -p android
        ```
    -   Para iOS (requiere una cuenta de desarrollador de Apple):
        ```bash
        eas build -p ios
        ```

4.  **Descarga los artefactos:** Una vez que el build termine, EAS te proporcionará un enlace para descargar el archivo compilado, listo para ser subido a Google Play Store o Apple App Store.
