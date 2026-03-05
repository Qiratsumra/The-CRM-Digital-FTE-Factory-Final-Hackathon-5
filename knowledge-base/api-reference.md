# NovaSaaS API Reference

Complete API documentation for integrating with NovaSaaS.

## Authentication

All API requests require an API key in the header:

```
Authorization: Bearer YOUR_API_KEY
```

Generate API keys in **Settings > API > API Keys**.

## Base URL

```
https://api.novasaas.com/v1
```

## Rate Limits

| Plan | Requests/minute | Requests/day |
|------|-----------------|--------------|
| Free | 60 | 1,000 |
| Pro | 300 | 10,000 |
| Enterprise | 1,000 | 100,000 |

## Endpoints

### Projects

#### List Projects

```http
GET /projects
```

**Response:**
```json
{
  "projects": [
    {
      "id": "proj_123",
      "name": "Website Redesign",
      "created_at": "2026-02-18T10:00:00Z"
    }
  ]
}
```

#### Create Project

```http
POST /projects
Content-Type: application/json

{
  "name": "New Project",
  "description": "Project description"
}
```

### Tasks

#### List Tasks

```http
GET /projects/{project_id}/tasks
```

#### Create Task

```http
POST /projects/{project_id}/tasks
Content-Type: application/json

{
  "title": "Task title",
  "description": "Task description",
  "assignee_id": "user_456",
  "due_date": "2026-02-25",
  "priority": "high"
}
```

#### Update Task

```http
PATCH /tasks/{task_id}
Content-Type: application/json

{
  "status": "completed",
  "title": "Updated title"
}
```

#### Delete Task

```http
DELETE /tasks/{task_id}
```

### Users

#### List Team Members

```http
GET /team
```

#### Add Team Member

```http
POST /team
Content-Type: application/json

{
  "email": "user@example.com",
  "role": "member"
}
```

## Error Handling

All errors follow this format:

```json
{
  "error": {
    "code": "invalid_request",
    "message": "Detailed error message",
    "field": "affected_field"
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `unauthorized` | 401 | Invalid or missing API key |
| `forbidden` | 403 | Insufficient permissions |
| `not_found` | 404 | Resource not found |
| `rate_limit` | 429 | Rate limit exceeded |
| `invalid_request` | 400 | Invalid request parameters |

## Webhooks

Configure webhooks in **Settings > API > Webhooks**.

### Available Events

- `project.created`
- `project.updated`
- `task.created`
- `task.updated`
- `task.completed`
- `user.added`

### Webhook Payload

```json
{
  "event": "task.created",
  "timestamp": "2026-02-18T10:00:00Z",
  "data": {
    "id": "task_789",
    "project_id": "proj_123",
    "title": "New task"
  }
}
```

## SDKs

Official SDKs available for:
- JavaScript/TypeScript: `npm install @novasaas/sdk`
- Python: `pip install novasaas`
- Go: `go get github.com/novasaas/go-sdk`
