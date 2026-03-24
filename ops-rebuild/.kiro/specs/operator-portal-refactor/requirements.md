# Requirements Document

## Introduction

Dự án `operator-portal-refactor` là bản rebuild toàn diện của `operator-portal` — một Next.js admin portal
phục vụ nghiệp vụ vận hành nội bộ. Mục tiêu là giữ nguyên toàn bộ nghiệp vụ hiện có, đồng thời nâng cấp
kiến trúc component, design system, và khả năng tái sử dụng code.

**Nghiệp vụ hiện tại:**
- Vehicle: Quản lý xe đã xác minh, danh sách xe, yêu cầu cập nhật xe
- Loyalty: Quản lý thành viên, giao dịch điểm thưởng, yêu cầu phê duyệt
- E-Voucher: Phát hành voucher điện tử theo chương trình
- Ecommerce: Quản lý sản phẩm (attribute sets, attributes, categories, products) và đơn hàng
- Merchant: Quản lý merchant
- System: Quản lý người dùng hệ thống
- Approval Request: Luồng phê duyệt đa cấp cho loyalty transaction và vehicle

**Vấn đề cần giải quyết:**
- Nhiều file component gần giống nhau (list, detail, columns cho từng domain)
- Không có design system thống nhất — UI chưa chuyên nghiệp
- ShadcnUI được dùng trực tiếp, không có wrapper layer để customize
- Component không đủ generic — khó mở rộng và tái sử dụng

---

## Glossary

- **Portal**: Ứng dụng Next.js (App Router) dành cho operator nội bộ
- **Design_System**: Tập hợp token màu sắc, typography, spacing và component wrapper trên ShadcnUI
- **Plugin_Component**: Component nhận config dạng JSON/object/ReactNode thay vì hardcode logic bên trong
- **GenericList**: Component danh sách tổng quát nhận `searchFn`, `columns`, `filterSchema` làm config
- **GenericDetail**: Component chi tiết tổng quát nhận `sections` config để render các field
- **ActionDialog**: Dialog thực hiện action có trạng thái idle/loading/success/error
- **ApprovalRequest**: Yêu cầu phê duyệt cho các thao tác nhạy cảm (cập nhật/thu hồi giao dịch, cập nhật xe)
- **PaginationDataTable**: Bảng dữ liệu có phân trang, drag-drop cột, pin cột, ẩn/hiện cột, sort cột
- **FilterConfig**: Cấu hình bộ lọc dạng JSON mô tả các field lọc (type, label, accessor, options)
- **Role**: Quyền truy cập theo format `domain:resource:action` (vd: `loyalty:transaction:admin`)
- **Cursor_Pagination**: Phân trang theo cursor (next/prev) thay vì page number
- **Offset_Pagination**: Phân trang theo page number và limit
- **Vehicle**: Xe đã được xác minh trong hệ thống, có thông tin đăng kiểm, đăng ký, dịch vụ
- **LoyaltyTransaction**: Giao dịch tích/tiêu điểm của khách hàng
- **Evoucher**: Voucher điện tử được phát hành theo chương trình
- **Merchant**: Đối tác kinh doanh trong hệ thống
- **GenericDetailById**: Component tổng quát thay thế toàn bộ `detail-by-id.tsx` per domain — nhận `queryKey`, `queryFn`, `render` prop, tự xử lý loading/error/empty states
- **StatusBadge**: Component tổng quát thay thế `status.tsx` per domain — nhận `statusMap` config (Record<string, BadgeVariant>) và `translationNamespace`
- **PageConfig**: Convention object per domain chứa `roles` và `titleKey`, được import vào Next.js page file thay vì hardcode

---

## Requirements

### Requirement 1: Design System và ShadcnUI Wrapper Layer

**User Story:** As a developer, I want a unified design system with a wrapper layer over ShadcnUI, so that I can
customize the visual appearance consistently across the entire portal without modifying ShadcnUI source files.

#### Acceptance Criteria

1. THE Design_System SHALL define CSS custom properties (design tokens) for primary color, secondary color,
   destructive color, muted color, border radius, and font sizes in `globals.css`
2. WHEN a developer uses a wrapped component (e.g., `<AppButton>`, `<AppCard>`, `<AppBadge>`), THE Design_System
   SHALL apply the portal's custom visual style automatically without requiring additional className props
3. THE Design_System SHALL provide wrapper components for at minimum: Button, Card, Badge, Input, Select, Dialog,
   Table, Tabs, Alert
4. WHERE a wrapper component receives a `variant` prop, THE Design_System SHALL map portal-specific variants
   (e.g., `"primary"`, `"danger"`, `"ghost"`) to the underlying ShadcnUI variants
5. THE Design_System SHALL support both light and dark themes via `next-themes` with consistent token values
6. WHEN a developer needs to override a specific style, THE Design_System SHALL allow passing `className` prop
   to any wrapper component to extend (not replace) the default styles via `cn()` utility
7. THE Design_System SHALL export all wrapper components from a single barrel file `components/ui/index.ts`

---

### Requirement 2: Plugin-Style Generic Components

**User Story:** As a developer, I want plugin-style generic components that accept JSON/object config or ReactNode,
so that I can build new feature pages by composing config rather than duplicating component files.

#### Acceptance Criteria

1. THE GenericList SHALL accept a `searchFn` prop of type `(filter: TFilter) => Promise<SearchResult<TItem>>`
   and render results in a `PaginationDataTable`
2. THE GenericList SHALL accept a `filterSchema` prop of type `FilterConfig` describing filter fields
   (type, label, accessor, options) and render the filter UI automatically
3. WHEN `filterSchema` is provided, THE GenericList SHALL persist active filter fields and values to a Zustand
   store keyed by `storageKey`
4. THE GenericList SHALL accept a `columns` prop of type `ColumnDef<TItem>[]` and pass it to the data table
5. THE GenericList SHALL accept a `transformFilter` prop to modify the filter before calling `searchFn`
6. THE GenericList SHALL accept a `headerActions` prop of type `ReactNode` to render action buttons in toolbar
7. THE GenericDetail SHALL accept a `sections` prop — an array of section configs, each with `title` and `fields`
8. WHEN a field config has `element: (data, t) => ReactNode`, THE GenericDetail SHALL call and render the result
9. WHEN a field config has `isDisplay: (data) => boolean` returning false, THE GenericDetail SHALL skip that field
10. THE ActionDialog SHALL accept `trigger: ReactNode`, `confirm: ReactNode`, `form: UseFormReturn<T>`, and
    `onValidForm: (values: T) => Promise<unknown>` props
11. WHEN `onValidForm` resolves successfully, THE ActionDialog SHALL transition to success state and optionally
    auto-close after 2 seconds if `autoCloseOnSuccess` is true
12. IF `onValidForm` rejects, THEN THE ActionDialog SHALL transition to error state and display the error message
13. THE Plugin_Component pattern SHALL support both primitive config (`{ label: "text" }`) and ReactNode config
    (`{ label: <span>text</span> }`) for all configurable display fields
14. THE `GenericDetailById<T>` SHALL accept `queryKey: QueryKey`, `queryFn: () => Promise<T | null>`, and
    `render: (data: T) => ReactNode` props
15. WHEN `queryFn` is loading, THE `GenericDetailById` SHALL display `MainSpinner`
16. WHEN `queryFn` returns an error, THE `GenericDetailById` SHALL display `MainError` with the error
17. WHEN `queryFn` returns null or undefined, THE `GenericDetailById` SHALL display `MainAlert` with a "not
    found" message configurable via `emptyMessage` prop
18. THE `StatusBadge` component SHALL accept a `status: string` prop, a `statusMap: Record<string, BadgeVariant>`
    prop mapping status values to Badge variants, and a `translationNamespace: string` prop for i18n label lookup
19. WHEN a status value is not found in `statusMap`, THE `StatusBadge` SHALL render the raw status string as
    plain text fallback
20. EACH domain page file SHALL import a `pageConfig` object (containing `roles: Role[]` and `titleKey: string`)
    from a co-located `page-config.ts` file instead of hardcoding roles and translation keys directly in the
    page component
21. THE `GenericList` domain wrapper files SHALL be replaced by a `[domain]-list-config.ts` file exporting
    `{ defaultFilter, filterSchema, columns, storageKey }` as a plain config object — no React component
    wrapper needed

---

### Requirement 3: Data Table với Drag-Drop, Pin, và Column Management

**User Story:** As an operator, I want a data table with drag-and-drop column reordering, column pinning, and
column visibility management, so that I can customize the table layout to fit my workflow.

#### Acceptance Criteria

1. THE PaginationDataTable SHALL support drag-and-drop column reordering using `@dnd-kit/core` restricted to
   horizontal axis
2. THE PaginationDataTable SHALL support column pinning to left or right via a per-column dropdown menu (`...`)
   in the column header
3. THE PaginationDataTable SHALL support toggling column visibility via a "Quản lý bảng" sheet panel
4. WHEN `storageKey` is provided, THE PaginationDataTable SHALL persist column order, column visibility, and
   column pinning state to a Zustand store keyed by `storageKey`
5. WHEN the page is reloaded, THE PaginationDataTable SHALL restore column layout from the Zustand store
6. THE PaginationDataTable SHALL render a "Mặc định cột" reset button when column layout differs from default
7. THE PaginationDataTable SHALL support `meta.hiddenByDefault: true` on column definitions to hide by default
8. THE PaginationDataTable SHALL support `meta.sticky: true` on column definitions to pin to right by default
9. WHEN pagination total changes, THE PaginationDataTable SHALL display total record count formatted with
   Vietnamese locale (`Intl.NumberFormat("vi-VN")`)
10. THE PaginationDataTable SHALL support a "Go to page" input that navigates directly to the specified page
11. THE PaginationDataTable SHALL support sorting a column via a sort control in the column header dropdown
    menu (`...`), alongside the existing pin column options
12. WHEN a column sort is applied, THE PaginationDataTable SHALL pass the sort state (column id + direction)
    to the parent via an `onSortChange` callback prop
13. FOR ALL column layout states, saving to Zustand store then restoring SHALL produce an equivalent state
    (round-trip property)

---

### Requirement 4: Bộ lọc Tổng quát (Generic Filter)

**User Story:** As an operator, I want a flexible filter bar that supports multiple field types and remembers
my active filters, so that I can quickly find the records I need.

#### Acceptance Criteria

1. THE GenericFilter SHALL support field types: `input`, `input-number`, `select`, `multi-select`, `date`,
   `date-range`, `boolean`, `read-only`
2. WHEN a user presses Enter in an `input` or `input-number` field, THE GenericFilter SHALL trigger search
3. THE GenericFilter SHALL show only the first 3 filter fields by default; additional fields accessible via "+"
4. WHEN a user removes an active filter field, THE GenericFilter SHALL clear that field's value and re-search
5. WHEN `storageKey` is provided, THE GenericFilter SHALL persist the list of active fields to a Zustand store
   keyed by `storageKey`; this state is NOT persisted to sessionStorage or localStorage
6. WHEN the filter value changes externally (e.g., from URL params), THE GenericFilter SHALL sync internal state
7. WHEN a filter field has a value, THE GenericFilter SHALL automatically add it to the active fields list
8. THE GenericFilter SHALL reset `page` to 1 whenever any filter value changes
9. WHEN a user logs out and logs back in, THE GenericFilter SHALL reset all active filter fields to the default
   state (first 3 fields only, no persisted values from the previous session)

---

### Requirement 5: Authentication và Authorization

**User Story:** As an operator, I want to log in securely and only see menu items and pages I have permission
to access, so that the portal is both secure and uncluttered.

#### Acceptance Criteria

1. THE Portal SHALL use `next-auth` with a credentials provider to authenticate operators via username/password
2. WHEN an unauthenticated user accesses any protected route, THE Portal SHALL redirect to the login page
3. WHEN a user's session expires, THE Portal SHALL redirect to the login page with a session-expired message
4. THE Portal SHALL use a `HasAnyRole` component that renders children only if the user has at least one role
5. WHEN a user navigates to a route they do not have permission for, THE Portal SHALL display a 403 page
6. THE Portal SHALL expose a `mustHasAnyRole(roles)` server-side utility that throws a redirect if unauthorized
7. THE Sidebar SHALL only render menu groups and items for which the current user has at least one matching role
8. IF the authentication API returns an error, THEN THE Portal SHALL display the error message on the login form

---

### Requirement 6: Layout và Navigation

**User Story:** As an operator, I want a consistent layout with a collapsible sidebar and breadcrumb navigation,
so that I can navigate the portal efficiently.

#### Acceptance Criteria

1. THE Portal SHALL render a collapsible sidebar using ShadcnUI `Sidebar` components with a trigger in header
2. THE Sidebar SHALL display menu groups with labels, each containing menu items with icons and titles
3. WHEN a menu item has sub-items, THE Sidebar SHALL render it as a collapsible group using `Collapsible`
4. THE Portal SHALL render breadcrumbs in the header that reflect the current route path
5. WHEN the route matches a `breadcrumbChildren` pattern in `sidebarItems`, THE Portal SHALL display the label
6. THE Portal SHALL display a dark/light mode toggle button in the header
7. THE Portal SHALL display the current user's name and a logout button in the sidebar footer via `NavUser`
8. WHEN the user clicks logout, THE Portal SHALL show a confirmation dialog before signing out

---

### Requirement 7: Vehicle Management

**User Story:** As a vehicle admin, I want to search, view, and update verified vehicles, so that I can manage
vehicle data accuracy in the system.

#### Acceptance Criteria

1. WHEN a user with `vehicle:viewer` or `vehicle:admin` role navigates to `/vehicle`, THE Portal SHALL display
   a vehicle search page with filter fields: plate number, frame number, engine number, verify status
2. THE Vehicle_List SHALL use cursor-based pagination (next/prev) to navigate through results
3. WHEN a user clicks on a vehicle row, THE Portal SHALL navigate to `/vehicle/detail/[id]`
4. THE Vehicle_Detail SHALL display vehicle information in sections: basic info, model info, inspections,
   registrations, services, and custom attributes
5. WHERE the user has `vehicle:admin` role, THE Vehicle_Detail SHALL display an "Cập nhật" button to submit
   an update approval request
6. WHEN a vehicle update approval request is submitted, THE Portal SHALL call the approval API and display
   success/error feedback via ActionDialog
7. THE Vehicle_Plate component SHALL render plates with yellow background for commercial vehicles (color "V")
   and white background for others
8. THE Vehicle_List at `/vehicle/list` SHALL use offset pagination and display all vehicles with column management

---

### Requirement 8: Loyalty Transaction Management

**User Story:** As a loyalty admin, I want to view, update, and revoke loyalty transactions, so that I can
correct errors and maintain data integrity.

#### Acceptance Criteria

1. WHEN a user with `loyalty:transaction:viewer` or `loyalty:transaction:admin` role navigates to
   `/loyalty/transaction/list`, THE Portal SHALL display a paginated list of loyalty transactions
2. THE Loyalty_Transaction_List SHALL support filters: transaction ID, status, date range, customer name,
   phone, license plate, invoice number
3. WHEN a user clicks on a transaction row, THE Portal SHALL navigate to `/loyalty/transaction/detail/[id]`
4. THE Loyalty_Transaction_Detail SHALL display transaction info, customer info, vehicle info, and invoice info
5. WHERE the user has `loyalty:transaction:admin` role, THE Loyalty_Transaction_Detail SHALL display "Cập nhật"
   and "Thu hồi" action buttons
6. WHEN a user submits an update request, THE Portal SHALL create an `UPDATE_LOYALTY_TRANSACTION` approval
   request via ActionDialog
7. WHEN a user submits a revoke request, THE Portal SHALL create a `REVOKE_LOYALTY_TRANSACTION` approval
   request with a reason code via ActionDialog
8. IF the approval API returns an error, THEN THE ActionDialog SHALL display the error message and remain open

---

### Requirement 9: Approval Request Management

**User Story:** As a loyalty admin, I want to view and act on approval requests, so that I can approve or
reject pending changes to loyalty transactions and vehicles.

#### Acceptance Criteria

1. WHEN a user with `loyalty:transaction:admin` role navigates to `/loyalty/request/list`, THE Portal SHALL
   display approval requests in two tabs: "Cập nhật" (UPDATE) and "Thu hồi" (REVOKE)
2. THE Approval_Request_List SHALL support filters: request ID, status, date range, created by, customer name,
   phone, license plate
3. WHEN a user clicks on a request row, THE Portal SHALL navigate to `/loyalty/request/detail/[id]`
4. THE Approval_Request_Detail SHALL display request metadata (id, type, status, created_at, created_by,
   revision) and the proposed data diff
5. WHERE the request status is `PUBLISHED`, THE Approval_Request_Detail SHALL display "Phê duyệt" and
   "Từ chối" action buttons
6. WHEN a user approves a request, THE Portal SHALL call the approval API and display success/error feedback
7. WHEN a user rejects a request, THE Portal SHALL require a rejection reason before calling the API
8. THE Approval_Request_Status component SHALL render status badges with distinct colors: PUBLISHED=blue,
   APPROVED=green, REJECTED=red, COMPLETED=emerald, FAILED=destructive
9. FOR ALL approval request status transitions, the displayed status SHALL match the API response status

---

### Requirement 10: E-Voucher Issuance Management

**User Story:** As an evoucher admin, I want to view and manage evoucher issuance records, so that I can
track voucher distribution to customers.

#### Acceptance Criteria

1. WHEN a user with `evoucher:admin` role navigates to `/evoucher/issuance/list`, THE Portal SHALL display
   a paginated list of evoucher issuance records
2. THE Evoucher_List SHALL support filters: phone number, voucher code, merchant code, serial code
3. WHEN a user clicks on an issuance row, THE Portal SHALL navigate to `/evoucher/issuance/detail/[id]`
4. THE Evoucher_Detail SHALL display issuance details including program info, customer phone, quantity, status
5. THE Evoucher_Layout SHALL provide a program selector that persists the selected evoucher program in Zustand
6. WHEN no evoucher program is selected, THE Evoucher_List SHALL display a prompt to select a program first
7. WHERE the user has `evoucher:admin` role, THE Evoucher_Detail SHALL display an export button

---

### Requirement 11: Ecommerce Product Management

**User Story:** As an ecommerce product admin, I want to manage product attribute sets, attributes, categories,
and products, so that I can maintain the product catalog.

#### Acceptance Criteria

1. WHEN a user with `ecommerce:product:viewer` or `ecommerce:product:admin` role navigates to
   `/ecommerce/product/attribute-sets`, THE Portal SHALL display a paginated list of attribute sets
2. THE Product_AttributeSet_List SHALL support filters: code, name, status
3. WHEN a user navigates to `/ecommerce/product/attributes`, THE Portal SHALL display a paginated list of
   product attributes with filters: code, name, data type
4. WHEN a user navigates to `/ecommerce/product/categories`, THE Portal SHALL display a paginated list of
   product categories with filters: code, name, status
5. WHEN a user navigates to `/ecommerce/product/list`, THE Portal SHALL display a paginated list of products
   with filters: code, name, status, category
6. WHEN a user clicks on a product row, THE Portal SHALL navigate to `/ecommerce/product/detail/[id]` showing
   product details including media, attributes, and category
7. WHERE the user has `ecommerce:product:admin` role, THE Product_Detail SHALL display edit and status toggle

---

### Requirement 12: Ecommerce Order Management

**User Story:** As an ecommerce order admin, I want to view and manage customer orders, so that I can track
order status and handle customer issues.

#### Acceptance Criteria

1. WHEN a user with `ecommerce:order:viewer` or `ecommerce:order:admin` role navigates to
   `/ecommerce/order/list`, THE Portal SHALL display a paginated list of orders
2. THE Order_List SHALL support filters: order ID, status, order type, customer phone, customer name,
   plate number, date range
3. WHEN a user clicks on an order row, THE Portal SHALL navigate to `/ecommerce/order/detail/[id]`
4. THE Order_Detail SHALL display order summary (subtotal, discount, tax, total), order items, discounts
   applied, and customer/vehicle info
5. THE Order_Status component SHALL render status badges with distinct colors per `OrderStatusEnum` value
6. WHERE the user has `ecommerce:order:admin` role, THE Order_Detail SHALL display order management actions

---

### Requirement 13: Loyalty Member Management

**User Story:** As a loyalty member admin, I want to search and view loyalty member profiles, so that I can
assist customers with their loyalty accounts.

#### Acceptance Criteria

1. WHEN a user with `loyalty:member:viewer` or `loyalty:member:admin` role navigates to `/loyalty/member`,
   THE Portal SHALL display a member search page
2. THE Member_Search SHALL support filters: customer ID, phone number, name, national ID
3. WHEN a user clicks on a member row, THE Portal SHALL navigate to the member detail page
4. THE Member_Detail SHALL display member profile info, loyalty point balance, and transaction history
5. WHERE the user has `loyalty:member:admin` role, THE Member_Detail SHALL display point adjustment actions

---

### Requirement 14: API Proxy Layer

**User Story:** As a developer, I want a server-side API proxy layer, so that backend API credentials are
never exposed to the browser and all requests are authenticated.

#### Acceptance Criteria

1. THE Portal SHALL implement Next.js API route handlers under `/app/api/` that proxy requests to backend
2. WHEN a client-side component calls a portal API route, THE API_Proxy SHALL attach the user's session token
3. THE API_Proxy SHALL use `httpClient` (axios instance with interceptors) for all upstream calls
4. WHEN an upstream API returns a non-2xx status, THE API_Proxy SHALL forward the error status and body
5. THE API_Proxy SHALL log all requests and responses with `X-Request-ID`, execution time, and status
6. THE Portal SHALL implement proxy routes for: `/api/auth`, `/api/vehicles`, `/api/loyalty`, `/api/orders`,
   `/api/vouchers`, `/api/rewards`, `/api/users`, `/api/batches`, `/api/files`, `/api/images`, `/api/product`
7. IF an upstream service is unreachable, THEN THE API_Proxy SHALL return a 503 status with a descriptive error

---

### Requirement 15: Internationalization (i18n)

**User Story:** As a developer, I want all user-facing strings managed through next-intl, so that the portal
can be easily localized and strings are consistent.

#### Acceptance Criteria

1. THE Portal SHALL use `next-intl` with Vietnamese (`vi`) as the default and only locale
2. THE Portal SHALL organize translation files by domain: `auth.json`, `dialog.json`, `diff.json`, `page.json`,
   `pagination.json`, `sidebar.json`, `type.json`, `validation.json`
3. WHEN a component needs a translated string, THE Portal SHALL use `useTranslations(namespace)` hook or
   `getTranslations(namespace)` server function
4. THE `type.json` file SHALL contain translations for all enum values: approval request types/statuses,
   loyalty transaction types/statuses, order types/statuses, vehicle verify statuses
5. THE `sidebar.json` file SHALL contain translations for all sidebar menu item titles
6. THE `page.json` file SHALL contain page titles for all routes used in breadcrumbs and `<title>` metadata

---

### Requirement 16: Error Handling và Loading States

**User Story:** As an operator, I want clear loading indicators and error messages, so that I always know
the state of the application.

#### Acceptance Criteria

1. WHEN a data fetch is in progress, THE Portal SHALL display a `MainSpinner` component centered in content
2. WHEN a data fetch fails, THE Portal SHALL display a `MainError` component with the error message and retry
3. WHEN an API action fails, THE Portal SHALL display a toast notification with the error message via `sonner`
4. WHEN an API action succeeds, THE Portal SHALL display a success toast notification
5. THE `ApiErrorDialog` component SHALL display detailed API error information in a dialog for debugging
6. IF a page-level error occurs, THEN THE Portal SHALL display a user-friendly error page with "Go back" button
7. WHEN a skeleton loading state is needed, THE Portal SHALL use `MainSkeleton` with appropriate dimensions

---

### Requirement 17: File và Image Handling

**User Story:** As an operator, I want to view and upload files and images associated with records, so that
I can manage supporting documentation.

#### Acceptance Criteria

1. THE Portal SHALL provide a `FileUpload` component that accepts file input and uploads via `/api/files`
2. THE Portal SHALL provide a `FileViewer` component that renders a list of file URLs as downloadable links
3. THE Portal SHALL provide an `ImagePreviewer` component that displays images with zoom capability
4. THE Portal SHALL provide an `ImageMagnifier` component for detailed image inspection
5. WHEN an image URL is from MinIO, THE Portal SHALL proxy the image through `/api/images` to avoid CORS
6. THE `ImagesZoomable` component SHALL render a carousel of zoomable images using `embla-carousel`
7. THE `PdfZoomable` component SHALL render PDF files with zoom controls

---

### Requirement 18: Reusable Form Components

**User Story:** As a developer, I want reusable form components for common input patterns, so that forms
across the portal are consistent and easy to build.

#### Acceptance Criteria

1. THE Portal SHALL provide a `DatePicker` component wrapping `react-day-picker` with Vietnamese locale
2. THE Portal SHALL provide a `DateRangePicker` component for selecting a start and end date
3. THE Portal SHALL provide a `DateTimePicker` component for selecting both date and time
4. THE Portal SHALL provide a `DateInputPicker` component that accepts manual text input with date validation
5. THE Portal SHALL provide a `Combobox` component for searchable single-select with async option loading
6. THE Portal SHALL provide a `MultiSelect` component for selecting multiple values from a list
7. WHEN a date input is invalid, THE Portal SHALL display a validation error message below the field
8. THE `NotesSection` component SHALL render a textarea for notes with character count display

---

### Requirement 19: System User Management

**User Story:** As a system admin, I want to manage portal user accounts and their roles, so that I can
control who has access to which features.

#### Acceptance Criteria

1. WHEN a user with `system:user:admin` role navigates to `/system/user`, THE Portal SHALL display a paginated
   list of system users
2. THE User_List SHALL support filters: username, email, role
3. WHEN a user clicks on a user row, THE Portal SHALL display user details including assigned roles
4. WHERE the current user has `system:user:admin` role, THE User_List SHALL display create, edit, deactivate
5. WHEN creating or editing a user, THE Portal SHALL display a form with: username, email, password, roles
6. IF a username or email already exists, THEN THE Portal SHALL display a validation error on the form

---

### Requirement 20: Performance và Code Quality

**User Story:** As a developer, I want the refactored portal to have minimal code duplication and good
performance, so that it is maintainable and fast.

#### Acceptance Criteria

1. THE Portal SHALL use `React.memo`, `React.useCallback`, and `React.useMemo` for components and callbacks
   that are passed as props or used in dependency arrays
2. THE Portal SHALL use `@tanstack/react-query` for all data fetching with appropriate `queryKey` arrays
3. WHEN a list filter changes, THE Portal SHALL invalidate only the relevant query cache entries
4. THE Portal SHALL use Zustand for client-side global state (filter field persistence, column layout
   persistence, evoucher program selection); filter and column layout state is scoped to the current session
   and resets on logout — no sessionStorage or localStorage is used for these states
5. THE Portal SHALL not duplicate domain-specific list/detail/columns files — each domain SHALL use
   `GenericList` and `GenericDetail` with domain-specific config objects
6. THE Portal SHALL use TypeScript strict mode with no `any` types in component props or service functions
7. WHEN a new domain feature is added, THE Portal SHALL require only: a config file, a columns definition,
   and a service client — no new generic infrastructure code
