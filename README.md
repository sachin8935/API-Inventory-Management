# Inventory Management System API

This Python microservice, built with FastAPI, provides a REST API for managing inventory.

## Requirements

- **Docker & Docker Compose** (for containerization)
- **Python 3.12** & **MongoDB 7.0** (for local development)
- **Public key** (OpenSSH encoded) for JWT (if authentication is enabled)
- **MongoDB Compass** (for GUI database interaction)

## Setup Instructions

### Docker Setup

1. **Create Environment Files**:
   ```bash
   cp inventory_management_system_api/.env.example inventory_management_system_api/.env
   cp inventory_management_system_api/logging.example.ini inventory_management_system_api/logging.ini
   ```
   pip install .[dev]
