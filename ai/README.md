# AI Knowledgebase — UtilityLib

This directory contains AI/agent instruction files for the UtilityLib project.

## Files

- **[AGENTS.md](./AGENTS.md)** — Comprehensive development guide for AI agents (Claude, Copilot, Cursor, Hermes, etc.). Covers architecture, conventions, module reference, and pitfalls.
- **[README.md](./README.md)** — This file. Overview of the AI knowledgebase.

## Purpose

These files ensure that any AI working on UtilityLib follows the same conventions, understands the class hierarchy, and doesn't break the lazy-import pattern or other critical design decisions.

## How to Update

When you add a new module, fix a pitfall, or change a convention:
1. Update `AGENTS.md` with the new information
2. Keep it concise — only document what an AI wouldn't guess from reading the code
3. Update the module reference table when adding new classes
