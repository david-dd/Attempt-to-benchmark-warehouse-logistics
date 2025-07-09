# Attempt-to-benchmark-warehouse-logistics

This repository provides a modular and open-source simulation framework for evaluating warehouse layouts and routing strategies under standardized conditions. It was developed to support reproducible benchmarking in warehouse logistics by separating experimental logic from scenario-specific contributions.

## 🔍 Motivation

Research on warehouse optimization is often hampered by proprietary tools, non-reproducible environments, and undocumented assumptions. This project addresses these issues by providing a transparent, extensible, and community-oriented framework. It enables researchers to systematically develop, execute, and compare warehouse picking strategies within clearly defined environments.

## 🧩 System Architecture

The framework is composed of three interoperable modules:

- **Module 1 – Layout Design Tool**  
  A web-based GUI for defining warehouse topologies, including aisle structures, storage areas, and picker positions.

- **Module 2 – Simulation Core**  
  A Python-based engine that loads defined layouts and scenarios, executes multi-agent simulations, and outputs detailed trajectories and KPIs.

- **Module 3 – Visualization Module**  
  An interactive web interface to visualize picker movements and compare routing strategies qualitatively.

User contributions include layouts (`.json`), scenario definitions (`.pkl`), and routing algorithms (`.py`). These are processed by the framework to generate simulation traces (`.json`) and aggregated performance results (`.txt`).

### 📊 Modular Interaction Overview

![Warehouse System Overview](https://github.com/david-dd/Attempt-to-benchmark-warehouse-logistics/blob/main/documation/Warehouse.png)

### 📦 Class-Level Structure (UML)

![UML Class Diagram](https://github.com/david-dd/Attempt-to-benchmark-warehouse-logistics/blob/main/documation/uml_classes.png)

## 🚀 Getting Started

See the `documation/` and `Appendix.pdf` for setup instructions, installation steps, and examples of use.

## 📄 License

This project is released under an open-source license. Feel free to fork, extend, and cite.

