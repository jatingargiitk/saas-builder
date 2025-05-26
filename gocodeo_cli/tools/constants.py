# Reference code description template for CRM projects
CRM_REFERENCE_CODE_DESCRIPTION = """
The description of the reference code for the CRM project is as follows:
                1. **Technology Stack**:
                - Next.js (React Framework)
                - TypeScript
                - Tailwind CSS for styling
                - Database migrations support
                2. **Project Structure**:
                ```
                my-crm-saas/
                ├── src/
                │   ├── app/           # Next.js app directory (routing and pages)
                │   ├── components/    # Reusable React components
                │   ├── lib/          # Utility functions and shared logic
                │   ├── types/        # TypeScript type definitions
                │   ├── styles/       # Global styles and CSS modules
                │   └── middleware.ts # Next.js middleware for request handling
                ├── migrations/       # Database migration files
                ├── tsconfig.json    # TypeScript configuration
                ├── tailwind.config.js # Tailwind CSS configuration
                ├── next.config.js   # Next.js configuration
                └── package.json     # Project dependencies and scripts
                ```
                3. **Key Architectural Components**:
                - **App Directory**: Uses Next.js 13+ app directory structure for routing and pages
                - **Components**: Modular React components for UI elements
                - **Types**: TypeScript type definitions for type safety
                - **Lib**: Shared utilities and business logic
                - **Middleware**: Request handling and authentication
                - **Migrations**: Database schema management
                4. **Application Routes**:
                - `/` - Main landing page
                - `/auth` - Authentication related pages
                - `/dashboard` - Main dashboard area
                - `/profile` - User profile management
                - `/settings` - Application settings
                - `/api` - API routes for backend functionality
                5. **Component Architecture**:
                - **UI Components**: Reusable UI elements in the `ui` directory
                - **Feature Components**: Organized by feature areas:
                    - `auth/` - Authentication related components
                    - `dashboard/` - Dashboard specific components
                    - `layout/` - Layout components
                    - `profile/` - Profile management components
                    - `settings/` - Settings related components
                - **Activity Log**: Dedicated component for activity tracking
                - Clear separation of concerns
                - Type safety with TypeScript
                - Component-based architecture
                - Feature-based organization
                - API routes for backend functionality
                - Database migration support
                - Modern styling with Tailwind CSS
                """ 