---
name: Snack Overflow
description: A live office-pantry dashboard for shared inventory, snack voting, and activity.
colors:
  primary: "#6258d9"
  primary-dark: "#4f45c0"
  background: "#f7f7fb"
  surface: "#ffffff"
  ink: "#24233b"
  muted: "#85849a"
  line: "#e9e9f0"
  plum-panel: "#292747"
  green: "#309265"
  orange: "#b87932"
  warning: "#bd8219"
  danger: "#cf6470"
typography:
  display:
    fontFamily: "Segoe UI, Helvetica Neue, Arial, sans-serif"
    fontSize: "clamp(31px, 4vw, 42px)"
    fontWeight: 800
    lineHeight: 1.16
    letterSpacing: "-1.8px"
  headline:
    fontFamily: "Segoe UI, Helvetica Neue, Arial, sans-serif"
    fontSize: "clamp(24px, 3vw, 32px)"
    fontWeight: 800
    lineHeight: 1.2
    letterSpacing: "-1.15px"
  title:
    fontFamily: "Segoe UI, Helvetica Neue, Arial, sans-serif"
    fontSize: "16px"
    fontWeight: 700
  body:
    fontFamily: "Segoe UI, Helvetica Neue, Arial, sans-serif"
    fontSize: "13px"
    fontWeight: 400
  label:
    fontFamily: "Segoe UI, Helvetica Neue, Arial, sans-serif"
    fontSize: "10px"
    fontWeight: 700
    letterSpacing: "1.4px"
rounded:
  sm: "8px"
  md: "9px"
  lg: "13px"
  xl: "16px"
spacing:
  sm: "8px"
  md: "12px"
  lg: "17px"
  xl: "24px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "#ffffff"
    rounded: "{rounded.md}"
    padding: "9px 13px"
    height: "39px"
  button-secondary:
    backgroundColor: "#f1f0ff"
    textColor: "#514bb1"
    rounded: "{rounded.md}"
    padding: "9px 13px"
    height: "39px"
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.lg}"
    padding: "17px"
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sm}"
    padding: "0 11px"
    height: "42px"
---

# Design System: Snack Overflow

## Overview

**Creative North Star: "The Pantry Ledger"**

Snack Overflow is a practical, shared pantry tool. Its current interface prioritizes quick scanning, clear inventory status, and straightforward member and administrator actions. The visual implementation is professional, calm, and efficient, with compact labels, readable hierarchy, and light surfaces that keep the live pantry information central.

This document records the visual system that is actually implemented in `frontend/src/style.css`. The user has also specified a future design direction: warm neutral surfaces, deep navy navigation, and orange and green accents. That direction is not yet implemented and is not represented by the normative tokens below. Do not apply a redesign as part of setup or unrelated work.

**Key Characteristics:**
- Compact, task-focused dashboard hierarchy.
- Cool near-white surfaces with a violet primary accent.
- Subtle borders and low-elevation cards.
- Responsive navigation and inventory grids.
- Existing UI behavior and live API data remain authoritative.

## Colors

The current palette is Pantry Violet and Cool Mist: violet drives actions and active states, supported by cool light surfaces and restrained semantic accents.

### Primary
- **Pantry Violet** (#6258d9): Primary actions, active navigation, focus treatments, and data emphasis.
- **Deep Violet** (#4f45c0): Hover state for primary actions.

### Secondary
- **Deep Plum Panel** (#292747): Dark background for the login illustration panel; it is not the dashboard navigation color.
- **Pantry Orange** (#b87932): Sweet-category icon accent.
- **Stock Green** (#309265): Positive stock and restock accents.

### Neutral
- **Cool Mist** (#f7f7fb): Application canvas.
- **White Surface** (#ffffff): Cards, controls, and sidebar.
- **Pantry Ink** (#24233b): Primary text.
- **Muted Lavender Gray** (#85849a): Supporting text.
- **Soft Divider** (#e9e9f0): Borders and separators.

### Named Rules
**The Current-Token Rule.** Keep these values aligned with the existing CSS. The future direction—warm neutrals, deep navy navigation, and orange/green accents—has no settled hex values and must not be presented as implemented styling.

## Typography

**Display Font:** Segoe UI (with Helvetica Neue, Arial, sans-serif fallbacks)  
**Body Font:** Segoe UI (with Helvetica Neue, Arial, sans-serif fallbacks)

**Character:** A familiar, clean sans-serif keeps operational labels and inventory details easy to scan. Strong weights and compact sizes distinguish headings and metadata without introducing a separate display face.

### Hierarchy
- **Display** (800, clamp(31px, 4vw, 42px), line-height 1.16): Login and registration headlines.
- **Headline** (800, clamp(24px, 3vw, 32px), line-height 1.2): Main dashboard title.
- **Title** (700, 16px): Snack names and compact section headings.
- **Body** (400, 13px in common supporting copy): Descriptions, form content, and status details.
- **Label** (700, 10px, 1.4px tracking, uppercase where used): Eyebrows and section metadata.

## Layout

The desktop dashboard reserves a fixed 248px sidebar and centers the remaining content in a maximum 1440px working area. At 1100px the sidebar narrows to 220px and the snack grid becomes two columns. At 760px navigation moves above the dashboard, metrics become two columns, and the login illustration is hidden. At 520px the snack grid becomes one column and filters stack for touch-sized controls. The layout uses compact gaps (8–17px in repeated controls and cards) with larger spacing around major sections.

## Elevation & Depth

The interface uses subtle layered surfaces: white cards sit just above the cool canvas with thin borders and restrained shadows. Stronger elevation is reserved for interactive hover emphasis and modal dialogs; color and border changes carry most state feedback.

### Shadow Vocabulary
- **Card Resting:** `0 5px 16px rgba(45, 43, 79, .025)` for snack and analysis cards.
- **Interactive Lift:** `0 12px 35px rgba(37, 35, 75, .055)` for hovered cards.
- **Dialog Elevation:** `0 24px 70px rgba(27, 26, 50, .2)` for the snack editor modal.

## Shapes

Controls use gently rounded corners (8–9px), cards use a larger radius (13px), and dialogs use 16px corners. Borders are thin and low-contrast. Status pills and profile badges use fully rounded ends; avoid introducing sharp-edged geometry that conflicts with these existing forms.

## Components

### Buttons
- **Shape:** Compact rounded rectangles (9px radius).
- **Primary:** Pantry Violet background with white text; 9px 13px padding and a 39px minimum height.
- **Secondary:** Soft violet surface with violet text for supporting administrative actions.
- **Hover / Focus:** Primary actions deepen on hover; keyboard focus uses a visible violet outline.

### Chips
- **Style:** Small, fully rounded status pills with a colored dot and a pale semantic background.
- **State:** Stocked is green, running-low is amber, and gone is muted red; status is always conveyed by text as well as color.

### Cards / Containers
- **Corner Style:** 13px for snack cards and analysis panels.
- **Background:** White against the cool light application canvas.
- **Shadow Strategy:** Low-contrast resting shadow; stronger ambient shadow on hover.
- **Border:** 1px soft divider.
- **Internal Padding:** 17px for snack cards and 21px for analysis panels.

### Inputs / Fields
- **Style:** White surface, thin cool-gray border, 8px radius, and 42px height for standard fields.
- **Focus:** Border shift with a visible violet focus treatment.
- **Error / Disabled:** Errors use a pale red surface; disabled controls visibly reduce opacity and do not imply success.

### Navigation
- **Style:** White desktop sidebar with quiet text and a pale-violet active state. At 760px it becomes a full-width top navigation row; keep labels readable and controls usable at narrow widths.

### Snack Status
Inventory status is paired with the current quantity and category. Preserve clear distinction between stocked, running-low, and gone states, including their text labels.

## Do's and Don'ts

### Do:
- **Do** treat the frontmatter values as the current implementation's tokens.
- **Do** preserve real API data, role-specific actions, and the existing application flows during visual work.
- **Do** honor warm neutrals, deep navy navigation, and orange/green accents when a future visual redesign is explicitly requested; settle exact values as part of that work.

### Don't:
- **Don't** claim the future palette is already implemented or silently change the current CSS during setup.
- **Don't** replace live dashboard data with sample values or bypass backend authorization.
- **Don't** remove responsive breakpoints, visible stock-state text, or keyboard focus indicators.
