# 🌐 Niches API

A FastAPI-powered backend for managing *niches* and their associated *keywords*. Designed for async operation using SQLAlchemy 2.0+, `asyncpg`, and PostgreSQL. Ideal for powering automated marketing or Pinterest workflows.

---

## 🚀 Features

- CRUD for `niches` and `keywords`
- Async SQLAlchemy ORM with PostgreSQL
- JSON-based REST API (v1)
- Relationship support (`Niche` ↔ `Keyword`)
- Docker-ready with dev seed option

---

## 🧪 API Endpoints (v1)

Base route: `/v1/niches`

### 🔍 Niches

| Method | Endpoint             | Description                |
|--------|----------------------|----------------------------|
| GET    | `/`                  | List all niches            |
| POST   | `/`                  | Create a new niche         |
| GET    | `/{niche_id}`        | Get a niche by ID          |
| PUT    | `/{niche_id}`        | Update a niche             |
| DELETE | `/{niche_id}`        | Delete a niche             |

---

### 🧩 Keywords

| Method | Endpoint                       | Description                        |
|--------|--------------------------------|------------------------------------|
| GET    | `/{niche_id}/keywords`         | List all keywords for a niche      |
| POST   | `/{niche_id}/keywords`         | Add a keyword to a niche           |
| PUT    | `/keywords/{keyword_id}`       | Update a keyword                   |
| DELETE | `/keywords/{keyword_id}`       | Delete a keyword                   |

---

## 🧑‍💻 Example Requests & Responses

### ➕ Create Niche with Keywords

**POST** `/v1/niches`

**Request:**
```json
{
  "name": "Travel & Adventure",
  "domain": "wanderlustdaily.com",
  "default_budget": 1200,
  "keywords": [
    { "keyword": "backpacking" },
    { "keyword": "budget travel" }
  ]
}
