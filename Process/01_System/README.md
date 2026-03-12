# System

High-level diagrams showing user interaction with the system.

## Purpose
This directory captures how users interact with the system and how the system integrates with external components. Diagrams here focus on **external** perspectives: what the user sees, what the system does, and integration points.

## Contents

### Sequence Diagrams
- **sequence_user_login.csv** - Authentication flow from user login through permission checking
- **sequence_data_pipeline.csv** - Data upload process from user submission through indexing

### Structure Diagrams
- **system_structure.csv** - High-level system components and relationships (PLACEHOLDER)

## Layer Filtering
Sequence diagrams are organized by layers:
- **UI** - User-facing interface components
- **API** - External API gateway
- **Business Logic** - Internal processing services
- **Data Access** - Database and storage systems

Use the "Display Layers" filter in the viewer to focus on specific layers.

## Design Principles
1. Show interactions from the **user's perspective**
2. Emphasize **external integrations** and **system boundaries**
3. Demonstrate **multi-layer flows** with filtering capability
4. Include information notes for key transitions and status
