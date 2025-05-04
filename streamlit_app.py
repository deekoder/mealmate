# streamlit_app.py
import streamlit as st
from VegetarianMealPlanner import VegetarianMealPlanner
from recipe_agent import RecipeAgent
from utils import parse_meal_plan_to_dataframe, parse_grocery_list_to_dict, create_pivot_table, load_css
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Vegetarian Meal Planner",
    page_icon="🥗",
    layout="wide"
)

# Load custom CSS
load_css()

# Add session state for recipes
if 'recipes' not in st.session_state:
    st.session_state.recipes = {}
if 'recipe_agent' not in st.session_state:
    st.session_state.recipe_agent = None

st.title("🥗 Vegetarian Meal Planner for Pre-Diabetic")
st.markdown("""
Generate a weekly meal plan optimized for vegetarian pre-diabetic diet.
This app creates personalized meal plans with bulk cooking strategies and grocery lists.
""")

# Sidebar for API key and date selection
with st.sidebar:
    st.header("Configuration")
    
    # Get API key from secrets or user input
    if 'openai_api_key' in st.secrets:
        api_key = st.secrets.openai_api_key
        st.success("API Key loaded from secrets!")
    else:
        # Fallback to user input if not in secrets
        api_key = st.text_input("OpenAI API Key", type="password")
        if api_key:
            st.info("Consider adding your API key to `.streamlit/secrets.toml` for persistence")
        else:
            st.markdown("[Get API Key](https://platform.openai.com/api-keys)")
    
    # Initialize recipe agent when API key is provided
    if api_key and st.session_state.recipe_agent is None:
        st.session_state.recipe_agent = RecipeAgent(api_key)
    
    st.header("Date Selection")
    date_option = st.radio(
        "Choose date option:",
        ["This Week", "Custom Week", "Date Range"]
    )
    
    if date_option == "This Week":
        today = datetime.now()
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
    elif date_option == "Custom Week":
        selected_date = st.date_input("Select any date in the week", datetime.now())
        if selected_date.weekday() == 0:  # If it's Monday
            start_date = selected_date
        else:
            start_date = selected_date - timedelta(days=selected_date.weekday())
        end_date = start_date + timedelta(days=6)
    else:  # Date Range
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", datetime.now())
        with col2:
            end_date = st.date_input("End Date", datetime.now() + timedelta(days=6))
    
    st.markdown(f"**Selected Week:** {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}")

# Main content
if api_key:
    if st.button("Generate Meal Plan", type="primary"):
        with st.spinner("Generating your meal plan... This may take a moment."):
            try:
                # Create planner with custom dates
                planner = VegetarianMealPlanner(api_key)
                
                # Pass dates to generate_meal_plan
                meal_plan = planner.generate_meal_plan(start_date=start_date, end_date=end_date)
                grocery_list = planner.extract_grocery_list()
                
                # Store meal plan in session state
                st.session_state.meal_plan = meal_plan
                st.session_state.grocery_list = grocery_list
                
                # Display success message
                st.success("Meal plan generated successfully!")
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.error(f"Error details: {type(e).__name__}")
    
    # Display meal plan if it exists
    if 'meal_plan' in st.session_state:
        st.markdown("## 📅 Your Weekly Meal Plan")
        st.markdown(f"**Period:** {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}")
        
        # Parse and display meal plan as table
        df_meals = parse_meal_plan_to_dataframe(st.session_state.meal_plan)
        
        # Display table
        if not df_meals.empty:
            # Create a unique identifier for each meal
            df_meals['unique_id'] = df_meals.apply(lambda row: f"{row['Day']}_{row['Meal']}_{row['Meal Name']}", axis=1)
            
            # Create and display pivot table
            pivot_df = create_pivot_table(df_meals)
            st.dataframe(pivot_df, use_container_width=True, hide_index=True)
            
            # Generate Recipe Section
            st.markdown("""
            <div class="section-header">
                <h2>👨‍🍳 Recipe Generation</h2>
                <p class="section-subtitle">Generate detailed recipes for each meal</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Create list view for recipes
            for idx, (_, meal) in enumerate(df_meals.iterrows()):
                # Create recipe list item
                st.markdown(f"""
                <div class="recipe-list-item">
                    <div class="recipe-info">
                        <div class="recipe-info-title">{meal['Meal Name']}</div>
                        <div class="recipe-info-meta">{meal['Day']} • {meal['Meal'].split('(')[0].strip()}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Create columns for buttons and status
                col1, col2, col3, col4 = st.columns([2, 2, 2, 3])
                
                unique_key = f"recipe_{meal['unique_id']}"
                
                with col1:
                    # Generate/Refresh Recipe button
                    button_text = "Get Recipe" if meal['unique_id'] not in st.session_state.recipes else "Refresh Recipe"
                    button_type = "primary" if meal['unique_id'] not in st.session_state.recipes else "secondary"
                    
                    if st.button(button_text, key=unique_key, type=button_type, use_container_width=True):
                        with st.spinner(f"Generating recipe for {meal['Meal Name']}..."):
                            if st.session_state.recipe_agent:
                                recipe = st.session_state.recipe_agent.generate_recipe(meal['Meal Name'])
                                st.session_state.recipes[meal['unique_id']] = recipe
                                st.rerun()
                
                with col2:
                    # Watch Video button (placeholder for future implementation)
                    if st.button("Watch Video", key=f"video_{unique_key}", disabled=True, use_container_width=True):
                        st.info("Coming soon! Video tutorials will be available here.")
                
               # Replace the Copy button section (around line 155-170) with this fixed code:

                with col3:
                    # Copy to Clipboard button (only show if recipe exists)
                    if meal['unique_id'] in st.session_state.recipes:
                        if st.button("Copy", key=f"copy_{unique_key}", use_container_width=True):
                            st.toast("Recipe copied to clipboard!")
                            # Note: JavaScript clipboard access is limited in Streamlit
                            # We'll use a simpler approach with a copy hint
                            st.code(st.session_state.recipes[meal['unique_id']], language="text")
                
                with col4:
                    # Status indicator
                    if meal['unique_id'] in st.session_state.recipes:
                        st.markdown('<span class="recipe-status-badge status-ready-badge">✓ Recipe Ready</span>', unsafe_allow_html=True)
                    else:
                        st.markdown('<span class="recipe-status-badge status-pending-badge">Not Generated</span>', unsafe_allow_html=True)
                
                # Display recipe if it exists
                if meal['unique_id'] in st.session_state.recipes:
                    with st.expander("📖 View Recipe", expanded=False):
                        st.markdown(f"""
                        <div class="recipe-content-wrapper">
                            <div class="recipe-content-text">
                            {st.session_state.recipes[meal['unique_id']]}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Add download button
                        st.download_button(
                            label="⬇️ Download Recipe",
                            data=st.session_state.recipes[meal['unique_id']],
                            file_name=f"recipe_{meal['Meal Name'].replace(' ', '_')}.txt",
                            mime="text/plain",
                            key=f"download_{meal['unique_id']}",
                            use_container_width=True
                        )
                
                # Add spacing between list items
                st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)
            
            # Add divider before next section
            st.markdown('<div class="recipe-section-divider"></div>', unsafe_allow_html=True)
            
        else:
            st.warning("Could not parse the meal plan into a table. Showing raw text:")
            st.text(st.session_state.meal_plan)
        
        # Download buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            st.download_button(
                label="📥 Meal Plan",
                data=st.session_state.meal_plan,
                file_name=f"meal_plan_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.txt",
                mime="text/plain"
            )
        
        with col2:
            st.download_button(
                label="📥 Grocery List",
                data=st.session_state.grocery_list,
                file_name=f"grocery_list_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.txt",
                mime="text/plain"
            )
        
        # Recipe export
        if st.session_state.recipes:
            with col3:
                all_recipes = "\n\n".join([f"## {meal_id}\n{recipe}" for meal_id, recipe in st.session_state.recipes.items()])
                st.download_button(
                    label="📥 All Recipes",
                    data=all_recipes,
                    file_name=f"all_recipes_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.txt",
                    mime="text/plain"
                )
        
        # Display grocery list as organized sections
        st.markdown("## 🛒 Grocery List")
        grocery_categories = parse_grocery_list_to_dict(st.session_state.grocery_list)
        
        if grocery_categories:
            # Create tabs for each grocery category
            category_tabs = st.tabs(list(grocery_categories.keys()))
            
            for tab, (category, items) in zip(category_tabs, grocery_categories.items()):
                with tab:
                    if items:
                        for item in items:
                            st.markdown(f"• {item}")
                    else:
                        st.write("No items in this category")
        else:
            st.text(st.session_state.grocery_list)
        
        # Add summary statistics with compact styling
        st.markdown("## 📊 Summary")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Meals", len(df_meals))
        with col2:
            st.metric("Days Covered", len(df_meals['Day'].unique()))
        with col3:
            meal_types = df_meals['Meal'].value_counts()
            st.metric("Meal Types", len(meal_types))
        with col4:
            if st.session_state.recipes:
                st.metric("Recipes Generated", len(st.session_state.recipes))
else:
    st.warning("Please enter your OpenAI API key to get started.")

# Footer
st.markdown("---")
st.markdown("*Created for AI Class Project | MIT License*")