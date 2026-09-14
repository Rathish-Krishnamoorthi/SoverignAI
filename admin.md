Improve the existing Sovereign-X ADMIN frontend.

IMPORTANT:
This is the ADMIN-ONLY interface.

Do NOT add employee, engineer, operator, analyst, or normal-user modules to this page.

The Admin interface should contain ONLY functions required to administer and govern the Sovereign-X platform.

Do not redesign the employee dashboard.
Do not expose operational AI modules here.
Do not expose process monitoring, predictive maintenance, equipment intelligence, or normal engineering workflows.

The existing RBAC/authentication must determine who can access this page.

==================================================
ADMIN RESPONSIBILITIES
==================================================

The Sovereign-X Admin should be responsible for:

1. Local user management
2. Role and permission management
3. SOP/document governance
4. Audit logs
5. System/security configuration
6. Local storage/system status
7. Administrative activity

Nothing else should appear in the Admin navigation.

==================================================
ADMIN SIDEBAR
==================================================

Create a minimal Admin navigation:

ADMINISTRATION

01  Access Control
02  SOP Governance
03  Audit Logs
04  System Status
05  Security Configuration

Do NOT add:

- AI Assistant
- Process Intelligence
- Equipment Monitoring
- Predictive Maintenance
- Operations
- Engineering Dashboard
- Employee Dashboard
- Analytics

Those belong to other user roles.

At the bottom show:

LOCAL WORKSPACE

● SOVEREIGN / OFFLINE
NO CLOUD DATA EGRESS

==================================================
01 — ACCESS CONTROL
==================================================

This is the primary Admin module.

The Admin must be able to:

- Create local users
- View users
- Edit users
- Assign roles
- Change roles
- Enable/disable accounts
- Reset temporary passwords
- View account status
- View basic user activity

Do NOT create a separate employee-management module.

Use the existing RBAC system.

Supported roles should come from the backend.

Do not hard-code roles if the backend already provides them.

Display:

USER
ROLE
STATUS
CREATED
LAST ACTIVITY
ACTIONS

Example:

admin@plant.local
ADMIN
ACTIVE
14 Sep 2026
Today

employee@plant.local
ENGINEER
ACTIVE
14 Sep 2026
Yesterday

Actions:

View
Edit Role
Reset Password
Disable Account

Destructive actions require confirmation.

==================================================
02 — ROLE & PERMISSION MANAGEMENT
==================================================

Role management can exist inside Access Control rather than as a separate top-level module.

Allow Admin to:

- View available roles
- View permissions assigned to each role
- Assign/remove permissions if supported by backend
- Understand what each role can access

Example:

ADMIN
├── User Management
├── Role Management
├── SOP Governance
├── Audit Logs
├── System Configuration
└── Security Configuration

ENGINEER
├── Engineering modules
├── AI Assistant
└── Authorized SOP access

OPERATOR
└── Authorized operational modules

AUDITOR
└── Audit access

Do NOT allow the Admin frontend to invent permissions.

Only display permissions actually supported by the backend.

==================================================
03 — SOP GOVERNANCE
==================================================

The Admin should manage the governance of SOPs.

This is NOT an employee SOP usage page.

Admin functions:

- View uploaded SOPs
- View SOP metadata
- View SOP versions
- Review SOP status
- Approve SOPs if Admin has approval permission
- Reject SOPs
- Supersede SOP versions
- Archive SOPs
- View SOP audit history

Statuses:

UPLOADED
UNDER_REVIEW
APPROVED
ACTIVE
SUPERSEDED
ARCHIVED

Display:

SOP ID
TITLE
VERSION
DEPARTMENT
UNIT
STATUS
EFFECTIVE DATE
REVIEW DATE
APPROVER
ACTIONS

The Admin should NOT use the SOP module to perform normal operational work.

The purpose is governance and administration.

==================================================
04 — AUDIT LOGS
==================================================

Create an Admin-only Audit Logs page.

Display administrative and security activity.

Examples:

USER_CREATED
USER_DISABLED
ROLE_CHANGED
LOGIN_SUCCESS
LOGIN_FAILED
SOP_UPLOADED
SOP_APPROVED
SOP_REJECTED
SOP_SUPERSEDED
SOP_ARCHIVED
SYSTEM_CONFIGURATION_CHANGED
SECURITY_CONFIGURATION_CHANGED

Table:

TIMESTAMP
USER
ACTION
RESOURCE
STATUS
DETAILS

Add filters:

- Date
- User
- Action
- Resource
- Success/Failure

Add search.

Do not allow ordinary users to access this page.

Audit records should be read-only from the frontend.

==================================================
05 — SYSTEM STATUS
==================================================

Create an Admin-only system health page.

Show the status of local Sovereign-X infrastructure.

Example:

SYSTEM STATUS

API
● ONLINE

DATABASE
● ONLINE

OBJECT STORAGE
● ONLINE

VECTOR DATABASE
● ONLINE

LOCAL LLM
● ONLINE

OCR SERVICE
● ONLINE

AUTHENTICATION
● ONLINE

AIR-GAPPED MODE
● ENABLED

Do NOT display fake statuses.

Fetch real status from backend health endpoints.

If a service is unavailable:

● OFFLINE

and show a useful error description.

==================================================
06 — SECURITY CONFIGURATION
==================================================

Create a minimal Admin security configuration page.

Display/configure only settings that are actually supported by the backend.

Possible settings:

AIR-GAPPED MODE
[ ENABLED ]

SESSION TIMEOUT
[ value ]

PASSWORD POLICY
[ configuration ]

MAX LOGIN ATTEMPTS
[ value ]

AUDIT LOGGING
[ ENABLED ]

LOCAL IDENTITY STORE
[ ENABLED ]

Do NOT create fake settings.

If a setting is not implemented in the backend, show it as read-only or do not display it.

Sensitive secrets must NEVER be displayed.

Never display:

- JWT secret
- Database password
- MinIO secret key
- Encryption keys
- API keys
- LLM credentials

==================================================
ADMIN DASHBOARD
==================================================

Do NOT create a generic analytics dashboard.

Instead create a compact Admin Overview.

Show only administrative information:

┌──────────────────────────────────────────┐
│ ADMINISTRATION                           │
│ Sovereign-X System Control               │
└──────────────────────────────────────────┘

SYSTEM STATUS
● API
● DATABASE
● STORAGE
● LOCAL LLM
● AIR-GAPPED MODE

ADMINISTRATIVE SUMMARY

LOCAL USERS       12
ACTIVE USERS      10
PENDING SOPs       3
AUDIT EVENTS     248

RECENT ADMIN ACTIVITY

USER_CREATED
SOP_APPROVED
ROLE_CHANGED
LOGIN_FAILED

The values must come from real backend APIs.

Do not hard-code values.

==================================================
WHAT ADMIN SHOULD NOT SEE
==================================================

Remove/hide all employee operational modules from the Admin navigation.

The Admin page should NOT contain:

❌ Employee task dashboard
❌ Engineering workspace
❌ Process monitoring
❌ Equipment monitoring
❌ Predictive maintenance
❌ Production analytics
❌ AI engineering assistant
❌ Operational recommendations
❌ Sensor analysis
❌ Plant operations
❌ Normal SOP consumption
❌ Employee-specific workflows

Those modules should be displayed based on the user's role through RBAC.

==================================================
ROLE-BASED ROUTING
==================================================

Implement proper route protection.

Example:

/admin/*

must require:

role = ADMIN

If a non-admin attempts to access:

/admin/access-control
/admin/audit
/admin/sop-governance
/admin/system
/admin/security

return:

403 Forbidden

or redirect to their appropriate role dashboard.

Do not rely only on hiding navigation items.

The backend must also enforce authorization.

==================================================
ADMIN UI DESIGN
==================================================

Keep the existing Sovereign-X visual identity.

Use:

- Dark industrial theme
- Teal/cyan accent
- Thin borders
- Compact cards
- Technical typography
- Minimal glow
- High contrast
- Small radius
- Professional enterprise appearance

The Admin UI should feel like:

"SECURITY + SYSTEM GOVERNANCE CONSOLE"

not:

"EMPLOYEE DASHBOARD"

==================================================
FUNCTIONALITY FIRST
==================================================

Do not add decorative UI that has no backend functionality.

Every visible Admin action must map to an existing backend API.

If an API does not exist:

1. Do not fake the result.
2. Identify the missing API.
3. Add the backend endpoint only if required by the existing architecture.
4. Connect the frontend to the real endpoint.

Use the existing API/service layer wherever possible.

==================================================
DATA SECURITY
==================================================

The Admin frontend must never expose:

- Database credentials
- JWT secrets
- Encryption keys
- MinIO credentials
- Internal service credentials
- LLM credentials

Only expose safe system status and administrative metadata.

==================================================
IMPORTANT IMPLEMENTATION RULES
==================================================

Before modifying the UI:

1. Inspect the current Sovereign-X frontend.
2. Identify the existing Admin page.
3. Identify existing RBAC.
4. Identify existing authentication.
5. Identify available Admin APIs.
6. Identify existing reusable components.
7. Identify existing employee/engineer modules.

Do not duplicate existing functionality.

Do not create fake data.

Do not break existing authentication.

Do not modify employee dashboards unnecessarily.

Do not remove backend functionality belonging to other roles.

Only change the Admin frontend and the minimum backend APIs required to make Admin functionality work.

==================================================
FINAL ADMIN STRUCTURE
==================================================

The final Admin interface should be:

SOVEREIGN-X
│
└── ADMINISTRATION
    │
    ├── Overview
    │
    ├── Access Control
    │   ├── Users
    │   └── Roles & Permissions
    │
    ├── SOP Governance
    │
    ├── Audit Logs
    │
    ├── System Status
    │
    └── Security Configuration

That is the complete Admin scope.

Keep the Admin interface focused, functional, secure, and minimal.