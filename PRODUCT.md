# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Office pantry members use the app to see what snacks are available, vote for favorites, consume stock, and review their own activity. Administrators manage snack inventory and review usage and favorite-snack analytics.

## Product Purpose

Snack Overflow helps a shared office pantry stay visible and manageable. Success means members can make informed choices from current stock data while administrators can maintain inventory and understand pantry activity.

## Positioning

The product combines live pantry inventory, member voting, stock actions, and role-specific activity and analytics in one shared office-pantry workflow.

## Operating Context

Members and administrators use the React + Vite web frontend, which communicates with the existing Flask API backed by PostgreSQL. Members have a personal activity history; administrators have inventory-management controls and an all-time analysis view.

## Capabilities and Constraints

- Members can browse snacks using server-backed category, status, name-search, and pagination controls; vote or unvote; consume available stock; and view their own activity history.
- Administrators can add, edit, delete, and restock snacks, and view pantry usage and favorite-snack analytics.
- Authentication, authorization, stock updates, votes, activity, and dashboard data remain owned by the existing backend and database.
- The frontend must use live API data and preserve role-specific permissions. It must not fabricate dashboard metrics or API responses.
- Keep the existing React + Vite, Flask, and PostgreSQL architecture.

## Evidence on Hand

The current frontend entry point is `frontend/src/main.jsx`; the application and existing visual implementation are in `frontend/src/App.jsx` and `frontend/src/style.css`. The frontend API client is `frontend/src/api.js`. These are the incumbent implementation and should be inspected before future UI changes.

## Product Principles

- Show pantry information from the real API rather than invented sample data.
- Keep member and administrator responsibilities distinct in the interface and enforced backend.
- Make stock actions and activity reflect the persisted pantry state.
- Preserve existing application behavior when making visual or documentation changes.
