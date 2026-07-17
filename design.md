# Library Management System — Design Documentation

## Brand Identity

**Company:** AeroConnections  
**Product:** Library Management System  
**Version:** 1.4.0

### Mission Statement
A clean, professional library management interface for AeroConnections staff to track book inventory, loans, and overdue returns.

### Core Design Principles
1. **Clarity** — Information hierarchy is clear, actions are obvious
2. **Efficiency** — Common tasks require minimal clicks
3. **Professionalism** — Clean, modern aesthetic suitable for corporate environments
4. **Accessibility** — WCAG 2.1 AA compliant

---

## Brand Colors (AeroConnections)

### Primary Palette
| Name | Pantone | Hex | Usage |
|------|---------|-----|-------|
| Primary Red | Pantone 485 C | `#DA291C` | Primary buttons, links, accents, active states |
| Light Grey | Pantone Cool Grey 5 C | `#C8C9C7` | Borders, secondary elements |
| Dark Grey | Pantone Cool Grey 11 C | `#5B6770` | Navigation, body text, sidebar |
| White | - | `#FFFFFF` | Card surfaces, inputs, backgrounds |

### Semantic Colors
| Name | Hex | Usage |
|------|-----|-------|
| Success | `#059669` | Returned status, available |
| Warning | `#D97706` | Due soon (25+ days), pending states |
| Danger | `#DA291C` | Overdue (30+ days), errors |

### Status Color Mapping
| Status | Background | Text |
|--------|------------|------|
| Available | White | Success |
| On Loan | Light Grey | Dark Grey |
| Overdue | `#FEE2E2` | Danger |
| Returned | `#D1FAE5` | Success |

---

## Typography

### Font Stack
```css
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
```

### Type Scale
| Name | Size | Weight | Usage |
|------|------|--------|-------|
| Display | 2.5rem (40px) | 700 | Page titles |
| H1 | 2rem (32px) | 700 | Section headings |
| H2 | 1.5rem (24px) | 600 | Card titles |
| H3 | 1.25rem (20px) | 600 | Subsections |
| Body | 1rem (16px) | 400 | Primary content |
| Small | 0.875rem (14px) | 400 | Secondary text |
| Caption | 0.75rem (12px) | 500 | Labels, badges |

---

## Spacing System

### Base Unit
`4px` (0.25rem)

### Spacing Scale
| Token | Value | Usage |
|-------|-------|-------|
| `space-1` | 4px | Tight gaps |
| `space-2` | 8px | Icon gaps |
| `space-4` | 16px | Standard padding |
| `space-6` | 24px | Section gaps |
| `space-8` | 32px | Page margins |

### Border Radius
| Token | Value | Usage |
|-------|-------|-------|
| `radius-sm` | 4px | Badges, small buttons |
| `radius-md` | 8px | Inputs, cards |
| `radius-lg` | 12px | Modals, large cards |

---

## Components

### Navigation Bar

#### Top Navigation (Desktop)
- Background: White with backdrop blur
- Height: 64px
- Logo: Left-aligned
- Navigation links: Center
- User menu: Right-aligned

#### Navigation Links
- Background: Transparent
- Active: Background `#DA291C` (Red), text white
- Hover: Background `rgba(91,103,112,0.1)`

### Buttons

#### Primary Button (AeroConnections Red)
- Background: `#DA291C`
- Text: White, weight 500
- Padding: 12px 16px
- Border Radius: 8px
- Hover: Darken to `#B8231A`

#### Floating Action Button (FAB)
- Position: Fixed bottom-right (24px)
- Size: 56px × 56px
- Background: Gradient `#DA291C` to `#B8231A`
- Shadow: `0 4px 20px rgba(218, 41, 28, 0.4)`

### Form Inputs

#### Text Input
- Height: 40px
- Border: 1px `#C8C9C7`
- Border Radius: 10px
- Padding: 10px 16px
- Background: White
- Focus: Border `#DA291C`, ring `rgba(218,41,28,0.1)`

#### Select Dropdown
- Same styling as text input
- Custom chevron icon
- Appearance: none (for consistent styling)

### Status Badges

| Status | Background | Text |
|--------|------------|------|
| Available | `#D1FAE5` | `#059669` |
| On Loan | `#C8C9C7` | `#5B6770` |
| Due Soon | `#FEF3C7` | `#D97706` |
| Overdue | `#FEE2E2` | `#DA291C` |
| Returned | `#D1FAE5` | `#059669` |

### Cards

#### Content Card
- Background: White
- Border: 1px `#C8C9C7`
- Border Radius: 12px
- Padding: 20px
- Shadow: `0 1px 3px rgba(0,0,0,0.05)`

#### Stat Card
- Background: White
- Border Radius: 12px
- Padding: 20px
- Icon: Circle with brand color background

---

## Page Layouts

### Dashboard
```
┌────────────────────────────────────────────────────────────┐
│ AeroConnections Logo                          Admin | User  │
├──────────────────────────────────────────────────────────┤
│ Books   Loans   Borrowers   Returns   Activity             │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  Dashboard                                                │
│  Browse and manage your library collection                │
│                                                           │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌────────┐         │
│  │ Books   │ │ Active  │ │Due Soon │ │Overdue │         │
│  │   12    │ │   10    │ │    2    │ │   3    │         │
│  └─────────┘ └─────────┘ └─────────┘ └────────┘        │
│                                                           │
│  Overdue Books (3)           Due Soon (2)               │
│  ┌──────────────────────┐    ┌──────────────────────┐   │
│  │ Book Title          │    │ Book Title           │   │
│  │ #01-1 - Name - 35d │    │ #03-2 - Name - 28d  │   │
│  └──────────────────────┘    └──────────────────────┘   │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

### Responsive Breakpoints

| Breakpoint | Width | Layout |
|------------|-------|--------|
| Mobile | < 640px | Single column |
| Tablet | 640px - 1024px | Condensed nav |
| Desktop | > 1024px | Full navigation |

---

## Data Models

### Book
| Field | Type | Notes |
|-------|------|-------|
| book_id | CharField | Auto-generated (01, 02...), editable |
| title | CharField | Book title |
| author | CharField | Author name |
| isbn | CharField | ISBN |
| created_at | DateTime | Auto |

### BookCopy
| Field | Type | Notes |
|-------|------|-------|
| copy_id | CharField | Unique ID (e.g., 01-1, 01-2) |
| book | ForeignKey | Link to Book |
| status | ChoiceField | Available, On Loan, Damaged, Lost, Retired |
| condition | CharField | Condition notes |
| created_at | DateTime | Auto |

### Borrower
| Field | Type | Notes |
|-------|------|-------|
| full_name | CharField | Borrower's full name |
| email | EmailField | Unique email |
| phone | CharField | Phone number |
| employment_type | ChoiceField | Permanent, Intern, Temporary |
| is_active | BooleanField | Active/deactivated |
| created_at | DateTime | Auto |

### Loan
| Field | Type | Notes |
|-------|------|-------|
| book_copy | ForeignKey | Link to BookCopy |
| copy_id_snapshot | CharField | Snapshot of copy ID |
| book_title_snapshot | CharField | Snapshot of book title |
| borrower_name | CharField | Borrower's name |
| checkout_date | DateField | Checkout date |
| due_date | DateField | Checkout + duration |
| return_date | DateField | Actual return date |
| status | ChoiceField | Active, Returned, Overdue |
| notes | TextField | Optional return notes |
| created_by | ForeignKey | Staff user |

### ReturnNote
| Field | Type | Notes |
|-------|------|-------|
| loan | ForeignKey | Link to Loan |
| book_copy | ForeignKey | Link to BookCopy |
| borrower_name | CharField | Snapshot of borrower |
| note | TextField | Return notes (optional) |
| image | ImageField | Damage photo (optional) |
| created_by | ForeignKey | Staff user |
| created_at | DateTime | Auto |

### ActivityLog (Immutable)
| Field | Type | Notes |
|-------|------|-------|
| action | ChoiceField | checkout, return, book_created, etc. |
| description | TextField | Activity description |
| timestamp | DateTime | Auto |
| user | ForeignKey | Staff user |

### LibrarySettings
| Field | Type | Notes |
|-------|------|-------|
| loan_duration_days | Integer | Default 30 days |
| due_soon_threshold | Integer | Default 25 days |
| max_books_per_borrower | Integer | Default 5 |
| webhook_url | URLField | Webhook URL |
| webhook_secret | CharField | Webhook secret |
| email_notifications_enabled | Boolean | Email toggle |
| google_sheets_id | CharField | Google Sheets ID |

### Branding
| Field | Type | Notes |
|-------|------|-------|
| company_name | CharField | Company name |
| library_name | CharField | Library name |
| logo | ImageField | Logo image |
| logo_invert | BooleanField | Invert logo for dark backgrounds |
| primary_color | CharField | Primary brand color |
| secondary_color | CharField | Secondary color |
| accent_color | CharField | Accent color |
| show_company_name | BooleanField | Toggle company name display |
| show_library_name | BooleanField | Toggle library name display |

---

## Icons

Using **Heroicons** (MIT licensed):
- Outline style for navigation
- Solid style for emphasis
- 20px default size

---

## Accessibility

- Focus: 2px outline `#DA291C`
- Touch targets: 44x44px minimum
- Contrast: 4.5:1 minimum
- Keyboard navigation: Full support
