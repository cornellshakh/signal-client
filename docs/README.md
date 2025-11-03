# Signal Client Library Documentation

Welcome to the complete technical documentation for the `signal-client` library. This collection of documents serves as a comprehensive knowledge base, detailing the architecture, core concepts, and usage of the library.

Whether you are a developer looking to build a bot or an LLM seeking to understand the codebase, this documentation provides the necessary context and information.

## Table of Contents

### Getting Started

- **[Getting Started Tutorial](./07_getting_started_tutorial.md)**
  - A step-by-step guide to building and running your first Signal bot.

### Core Concepts & Architecture

- **[Architecture Overview](./01_architecture.md)**
  - A high-level look at the system design, including a component and data flow diagram.
- **[Core Concepts](./02_core_concepts.md)**
  - An explanation of the fundamental ideas in the library, such as `Command` and `Context`.

### In-Depth Guides

- **[Data Models (Schemas)](./03_domain_layer.md)**
  - A deep dive into the core data models of the library (e.g., `Message`, `Group`, `Contact`).
- **[Services Layer](./04_services_layer.md)**
  - A detailed look at the services that contain the core application logic.
- **[Infrastructure Layer](./05_infrastructure_layer.md)**
  - An overview of the components that handle communication with external systems like the Signal API.

- **[Writing Asynchronous Commands](./writing_async_commands.md)**
  - Best practices for writing non-blocking, high-performance commands.
- **[Coding Standards](./coding_standards.md)**
  - The mandatory coding standards for contributing to this project.

### API Reference

- **[API Reference](./06_api_reference.md)**
  - A detailed reference for all public-facing classes and methods, including `SignalClient` and `Context`.
- **[Configuration Reference](./08_configuration.md)**
  - A complete list of all the available configuration options.
