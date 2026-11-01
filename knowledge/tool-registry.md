# Tool Registry

A tool registry gives AI agents structured access to capabilities.

Each tool has:
- id, name, description
- input schema (JSON Schema)
- output schema
- safety rules
- example usage
- tags for discovery

AI agents should prefer using tools over reimplementing.
