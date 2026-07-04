# Architecture

## Goals

- Modular widget system
- Home Assistant first
- Reusable renderer
- Event driven refresh
- HACS compatible

## Core Components

- DashboardContext
- WidgetManager
- Renderer
- Formatter
- Widgets

Each widget is responsible only for producing its own output. The renderer is responsible for layout. The context provides Home Assistant state to all widgets without each widget querying Home Assistant individually.
