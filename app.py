# app.py
import streamlit as st
from datetime import datetime, timedelta
from components.sidebar import render_sidebar
from components.meal_plan_display import display_meal_plan
from components.recipe_manager import display_recipes
from components.grocery_display import display_grocery_list
from components.summary_display import display_summary
from utils.app_state import initialize_session_state

# Set page configuration
st.set_page_config(
    page_title="Vegetarian Meal Planner",
    page_icon="🥗",
    layout="wide"
)

# Load custom CSS
from utils.ui_helpers import load_css
load_css()

# Initialize session state
initialize_session_state()

# Display app title and intro
st.title("🥗 Vegetarian Meal Planner for Pre-Diabetics")
st.markdown("""
Generate a weekly meal plan optimized for vegetarian pre-diabetic diet.
This app creates personalized meal plans with bulk cooking strategies and grocery lists.
""")

# Render sidebar to get configuration
api_key, date_config, app_config = render_sidebar()

# Main content flow
if api_key:
    # Check if we need to generate a meal plan based on sidebar input
    if app_config.get("generate_plan", False):
        with st.spinner("Generating your meal plan... This may take a moment."):
            from VegetarianMealPlanner import VegetarianMealPlanner
            try:
                # Create planner with custom dates
                planner = VegetarianMealPlanner(api_key)
                
                # Use the CoT version of the meal planner if reasoning is enabled
                if app_config["show_reasoning"]:
                    try:
                        meal_plan_data = planner.generate_meal_plan_with_cot(
                            start_date=date_config["start_date"], 
                            end_date=date_config["end_date"],
                            complexity=app_config["meal_complexity"]
                        )
                        
                        # Store the raw meal plan data for reasoning display
                        st.session_state.meal_plan_data = meal_plan_data
                        
                        # The meal plan text is already set by the CoT method
                        meal_plan = planner.meal_plan
                        
                    except Exception as e:
                        st.error(f"Error in CoT generation: {str(e)}")
                        # Fallback to regular meal plan
                        meal_plan = planner.generate_meal_plan(
                            start_date=date_config["start_date"], 
                            end_date=date_config["end_date"]
                        )
                        st.session_state.meal_plan_data = None
                else:
                    # Use the original method if reasoning is not needed
                    meal_plan = planner.generate_meal_plan(
                        start_date=date_config["start_date"], 
                        end_date=date_config["end_date"]
                    )
                    st.session_state.meal_plan_data = None
                
                grocery_list = planner.extract_grocery_list()
                
                # Store meal plan in session state
                st.session_state.meal_plan = meal_plan
                st.session_state.grocery_list = grocery_list
                st.session_state.sidebar_date_range = date_config
                
                # Display success message
                st.success("Meal plan generated successfully!")
                st.experimental_rerun()
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
                import traceback
                st.error(traceback.format_exc())
    
    # Display meal plan if it exists
    if 'meal_plan' in st.session_state and st.session_state.meal_plan:
        # Display the meal plan
        meal_df = display_meal_plan(
            st.session_state.meal_plan, 
            date_config["start_date"], 
            date_config["end_date"],
            show_reasoning=app_config["show_reasoning"],
            meal_plan_data=st.session_state.meal_plan_data
        )
        
        # Display recipe section
        if meal_df is not None and not meal_df.empty:
            display_recipes(meal_df, app_config["enable_auto_evaluation"])
        
        # Display grocery list
        display_grocery_list(st.session_state.grocery_list)
        
        # Display summary statistics
        display_summary(meal_df)
    
else:
    st.warning("Please enter your OpenAI API key to get started.")

# Footer
st.markdown("---")
st.markdown("*Created for AI Class Project | MIT License*")