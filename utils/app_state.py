# utils/app_state.py
import streamlit as st
from datetime import datetime, timedelta

def initialize_session_state():
    """Initialize all required session state variables"""
    # Recipe state
    if 'recipes' not in st.session_state:
        st.session_state.recipes = {}
    
    # Recipe agent
    if 'recipe_agent' not in st.session_state:
        st.session_state.recipe_agent = None
    
    # Reasoning display toggle
    if 'show_reasoning' not in st.session_state:
        st.session_state.show_reasoning = False
    
    # Meal plan data
    if 'meal_plan_data' not in st.session_state:
        st.session_state.meal_plan_data = None
    
    # Meal plan text
    if 'meal_plan' not in st.session_state:
        st.session_state.meal_plan = ""
    
    # Grocery list
    if 'grocery_list' not in st.session_state:
        st.session_state.grocery_list = ""
    
    # Evaluations
    if 'evaluations' not in st.session_state:
        st.session_state.evaluations = {}
    
    # Evaluation manager
    if 'evaluation_manager' not in st.session_state:
        st.session_state.evaluation_manager = None
    
    # Date range from sidebar
    if 'sidebar_date_range' not in st.session_state:
        today = datetime.now()
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
        st.session_state.sidebar_date_range = {
            "start_date": start_date,
            "end_date": end_date
        }

def get_meal_by_id(meal_id):
    """Helper function to retrieve a meal by its ID"""
    if 'meal_plan_df' not in st.session_state or st.session_state.meal_plan_df is None:
        return None
    
    for _, meal in st.session_state.meal_plan_df.iterrows():
        if meal['unique_id'] == meal_id:
            return meal
    
    return None