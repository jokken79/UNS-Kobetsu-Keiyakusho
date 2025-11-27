# UNS-Kobetsu Project Memory

This file maintains persistent context across Claude sessions. Update it after major decisions.

## Project Overview

- **Name**: UNS Kobetsu Keiyakusho Management System
- **Purpose**: Managing 個別契約書 (individual dispatch contracts) for 労働者派遣法第26条 compliance
- **Status**: In Development
- **Last Updated**: 2025-11-27

## Architecture Decisions

### 2025-11-27: Elite Agent System Adoption
- **Context**: Need for structured development workflow with specialized agents
- **Decision**: Adopted elite agent system from claude-agents-elite repository
- **Rationale**: Provides systematic approach with planner, coder, tester, stuck agents
- **Consequences**: All development tasks should follow agent delegation workflow

### Stack Selection
- **Backend**: FastAPI + SQLAlchemy + PostgreSQL
  - Rationale: Python ecosystem familiar, FastAPI modern and fast, SQLAlchemy 2.0 for async support
- **Frontend**: Next.js 15 + React 18 + TypeScript
  - Rationale: App Router for modern patterns, TypeScript for type safety
- **Database**: PostgreSQL 15
  - Rationale: JSON support for flexible fields, robust for production

## Technology Choices

| Area | Choice | Rationale |
|------|--------|-----------|
| Backend Framework | FastAPI 0.115+ | Modern Python web framework with automatic OpenAPI |
| ORM | SQLAlchemy 2.0+ | Industry standard, async support |
| Database | PostgreSQL 15 | Reliable, JSON support, robust |
| Cache | Redis 7 | Fast in-memory cache |
| Frontend Framework | Next.js 15 | App Router, SSR/SSG capabilities |
| UI Library | React 18+ | Component ecosystem, hooks |
| Styling | Tailwind CSS | Utility-first, rapid development |
| State (Server) | React Query | Caching, background updates |
| State (Client) | Zustand | Lightweight, simple API |
| Testing (BE) | pytest | Python standard |
| Testing (FE) | Vitest | Fast, Vite-compatible |

## Patterns & Conventions

### Backend Patterns
- Service layer pattern: Business logic in `services/`, not routes
- Dependency injection via FastAPI's `Depends()`
- Pydantic schemas for all validation
- Contract number format: `KOB-YYYYMM-XXXX`

### Frontend Patterns
- React Query for all API data (server state)
- Zustand only for client-side state
- Centralized API client in `lib/api.ts`
- TypeScript types mirror Pydantic schemas

### Naming Conventions
- Tables: snake_case plural (kobetsu_keiyakusho, factories)
- Models: PascalCase singular (KobetsuKeiyakusho, Factory)
- Routes: kebab-case (/api/v1/kobetsu)
- Components: PascalCase (KobetsuForm.tsx)

## Bugs Fixed

### [Template - Add bugs as they are fixed]
- **Date**: YYYY-MM-DD
- **Symptom**: What was observed
- **Root Cause**: What was actually wrong
- **Fix**: How it was resolved
- **Prevention**: How to avoid in future

## Failed Approaches

### [Template - Document failed approaches]
- **Date**: YYYY-MM-DD
- **What was tried**: Description
- **Why it failed**: Reason
- **Lesson learned**: Takeaway

## User Preferences

### Development Style
- Test after every implementation
- Delegate to specialized agents
- Validate with critic before risky changes
- Record all decisions in memory

### Communication
- Japanese terminology for business concepts
- English for technical terms
- Clear, concise explanations

## Ongoing Issues

### [Template - Track active issues]
- **Status**: open/investigating/blocked
- **Description**: What's wrong
- **Last activity**: Date and action

## Technical Debt

### Excel Migration Incomplete
- **Location**: Import system
- **Description**: Full Excel formula replication not complete
- **Priority**: Medium
- **Added**: 2025-11-27

## External Dependencies

| Dependency | Version | Notes |
|------------|---------|-------|
| FastAPI | 0.115+ | Core backend framework |
| SQLAlchemy | 2.0+ | ORM with async support |
| Pydantic | 2.0+ | Validation |
| Next.js | 15 | Frontend framework |
| PostgreSQL | 15 | Database |
| Redis | 7 | Cache |
| python-docx | latest | Document generation |

## Session History

### 2025-11-27 - Elite Agent System Setup
- Adapted elite agent system from claude-agents-elite repository
- Created 19 specialized agents for different tasks
- Set up orchestrator CLAUDE.md
- Created agents-registry.json for routing
- Initialized project memory

---

## How to Use This File

### At Session Start
Read this file to understand:
- What decisions were made and why
- What patterns to follow
- What issues exist
- What failed approaches to avoid

### During Development
Consult when:
- Making architectural decisions
- Choosing technologies
- Encountering similar problems

### After Major Work
Update with:
- New decisions and rationale
- Bugs fixed (with prevention notes)
- Failed approaches (with lessons)
- Session summary
