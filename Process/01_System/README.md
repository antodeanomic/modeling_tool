# System

High-level diagrams showing user interaction with the system.

## Purpose
This directory captures how users interact with the system and how the system integrates with external components. Diagrams here focus on **external** perspectives: what the user sees, what the system does, and integration points.

## Contents

### Main Entry Diagram
- **00_Main/system_main.csv** - Starting point for navigating system-level diagrams

### Sequence Diagrams
- **10_Diagrams/sequence_user_login.csv** - Authentication flow from user login through permission checking
- **10_Diagrams/sequence_data_pipeline.csv** - Data upload process from user submission through indexing

### Structure Diagrams
- **10_Diagrams/system_components.csv** - High-level system components and boundaries
- **10_Diagrams/system_data_flow.csv** - System-level data flow relationships
- **10_Diagrams/system_layers.csv** - Layered view of user-facing and internal services
- **10_Diagrams/system_storage.csv** - Storage-related system elements
- **10_Diagrams/system_user_interaction.csv** - User interaction surface and key touchpoints

### Reusable Definitions
- **20_Definitions/actors.csv** - Shared actor definitions
- **20_Definitions/packages.csv** - Shared package/component definitions

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
