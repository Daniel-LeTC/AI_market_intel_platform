# TASK: Implement UI Category Filter (Smart Grouping)
- Target: `scout_app/Market_Intelligence.py`, `scout_app/ui/common.py`
- Logic:
    1. Fetch unique `main_niche` list from `products` table.
    2. Add "Select Category" selectbox to Sidebar.
    3. Filter "Select Product" dropdown based on selected category.
    4. Sync selected category to "Mass Mode" (Tab 2) and "Showdown" (Tab 3) to automatically filter competitors.
- Constraint: Maintain Sidebar cleanliness and prevent UI lag.
