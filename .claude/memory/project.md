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

### CRITICAL: Demo Authentication System
- **Status**: open
- **Location**: `backend/app/api/v1/auth.py:62-73`
- **Description**: Users stored in-memory `_demo_users` dict, not in database. Model `User` exists but is NOT used.
- **Impact**: Users lost on restart, no login page in frontend
- **Fix Required**: Implement auth using existing `User` model
- **Last activity**: 2025-11-27 - Identified in audit

### CRITICAL: Hardcoded Windows Path in Docker
- **Status**: open
- **Location**: `docker-compose.yml:103`
- **Description**: `E:/BASEDATEJP:/network_data` won't work on Linux/Docker
- **Impact**: Docker container fails to mount volume
- **Fix Required**: Use environment variable or make volume optional
- **Last activity**: 2025-11-27 - Identified in audit

### MEDIUM: Hardcoded API URL in Sync Page
- **Status**: open
- **Location**: `frontend/app/sync/page.tsx:16`
- **Description**: Bypasses `NEXT_PUBLIC_API_URL` env var with hardcoded localhost
- **Fix Required**: Use centralized api.ts client
- **Last activity**: 2025-11-27 - Identified in audit

### LOW: Redis Not Utilized
- **Status**: open
- **Location**: docker-compose.yml (configured), requirements.txt (installed)
- **Description**: Redis configured but not used for caching or session management
- **Fix Required**: Implement for token invalidation on logout
- **Last activity**: 2025-11-27 - Identified in audit

### Missing Frontend Pages
- **Status**: open
- **Description**: No login page (`/login`), no 404 page, no error boundaries
- **Impact**: Cannot authenticate users via UI
- **Last activity**: 2025-11-27 - Identified in audit

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

### 2025-11-27 - Full System Audit
- Activated explorer agents to analyze backend and frontend
- Identified 5 critical/medium/low issues:
  1. CRITICAL: Demo auth system (in-memory users, not database)
  2. CRITICAL: Windows path hardcoded in docker-compose
  3. MEDIUM: Hardcoded API URL in sync page
  4. LOW: Redis not utilized
  5. Missing: Login page, error boundaries
- Created .env file from .env.example
- Updated project memory with known issues
- Generated full diagnostic report

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
