# Buc - Audit Management System

**This project is proprietary software, and all rights are reserved by Diego Alvarez / Buc.**
It is showcased here solely as a portfolio piece to demonstrate development capabilities and engage with potential clients.
Unauthorized copying, reproduction, distribution, modification, or use of this code, in whole or in part, is strictly prohibited.

---

## Overview

**Buc** is a comprehensive web and mobile application designed for the end-to-end management of business audits. It allows organizations to define custom audit templates, assign audits to specific companies and areas, and maintain a detailed record of responses and progress.

The platform is built with a modern approach, featuring a FastAPI backend and a React frontend (with Tamagui for the UI) that runs on both web and mobile (iOS/Android) from a single codebase.

## Key Features

-   **Multi-Role Management:** A detailed permission system for Superusers, Administrators, Auditors, and Users.
-   **Centralized Administration:** Administrators can manage companies, areas, users, and audit templates from a central dashboard.
-   **Dynamic Audit Builder:** Allows for the creation of custom audit assignments from predefined templates, with the ability to edit questions on the fly.
-   **Complete Auditing Workflow:** Auditors can view their assignments, answer various question types (text, multiple-choice, rating scales, etc.), and submit their completed responses.
-   **Modern and Responsive UI:** Built with Tamagui, the interface is fast, consistent, and adapts to any screen size, from desktop to mobile.
-   **Dynamic Theming:** Users can switch between light and dark themes.

## Technologies Used

-   **Backend:** FastAPI, SQLModel, PostgreSQL
-   **Frontend:** React, Next.js (for web), Expo (for mobile), Tamagui (for UI), TanStack Query (for server state), Zustand (for global state).
-   **Languages:** Python, TypeScript.
-   **Containerization:** Docker.
