# utils.py
import re
import pandas as pd
import streamlit as st  # Added import for streamlit

def parse_meal_plan_to_dataframe(meal_plan):
    """Parse the meal plan text into a structured dataframe"""
    days_data = []
    current_day = None
    current_date = None
    current_meal_type = None
    
    lines = meal_plan.split('\n')
    for line in lines:
        # Match day headers (e.g., "### Day 1 - Monday, November 4")
        day_match = re.match(r'### Day \d+ - (\w+), (\w+ \d+)', line)
        if day_match:
            current_day = day_match.group(1)
            current_date = day_match.group(2)
            continue
        
        # Match meal types (e.g., "**Breakfast (7:00 AM)**")
        meal_match = re.match(r'\*\*([A-Za-z]+\s*\(\d+:\d+\s*[AP]M\))\*\*', line)
        if meal_match:
            current_meal_type = meal_match.group(1)
            continue
        
        # Match meal name (e.g., "- Meal: [Meal Name]")
        meal_name_match = re.match(r'- Meal:\s*(.*)', line)
        if meal_name_match and current_day and current_date and current_meal_type:
            meal_name = meal_name_match.group(1)
            if meal_name != "[Meal Name]" and meal_name != "[Snack Name]":  # Skip placeholders
                days_data.append({
                    'Day': current_day,
                    'Date': current_date,
                    'Meal': current_meal_type,
                    'Meal Name': meal_name
                })
    
    return pd.DataFrame(days_data)

def parse_grocery_list_to_dict(grocery_list):
    """Parse grocery list into categories"""
    categories = {}
    current_category = None
    
    lines = grocery_list.split('\n')
    for line in lines:
        # Match category headers (e.g., "### Produce")
        category_match = re.match(r'###\s*(.*)', line)
        if category_match:
            current_category = category_match.group(1)
            categories[current_category] = []
            continue
        
        # Match items (e.g., "- Item 1")
        item_match = re.match(r'-\s*(.*)', line.strip())
        if item_match and current_category:
            item = item_match.group(1)
            if item != 'Item 1' and item != 'Item 2':  # Skip placeholders
                categories[current_category].append(item)
    
    return categories

def create_pivot_table(df_meals):
    """Create a pivot table from the meals dataframe"""
    # Create pivot table
    pivot_df = df_meals.pivot_table(
        index=['Day', 'Date'], 
        columns='Meal', 
        values='Meal Name', 
        aggfunc='first',
        fill_value=''
    ).reset_index()
    
    # Reorder columns to follow daily meal sequence
    meal_order = ['Breakfast', 'Snack', 'Lunch', 'Dinner']
    
    # Get actual columns in the dataframe that match our meal types
    available_meals = []
    for meal_type in meal_order:
        matching_cols = [col for col in pivot_df.columns if meal_type in col]
        available_meals.extend(matching_cols)
    
    # Sort pivot_df columns by order of days
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    pivot_df['sort_day'] = pivot_df['Day'].map({day: i for i, day in enumerate(days_order)})
    pivot_df = pivot_df.sort_values('sort_day')
    pivot_df = pivot_df.drop('sort_day', axis=1)
    
    # Organize columns
    new_column_order = ['Day', 'Date'] + available_meals
    new_column_order = [col for col in new_column_order if col in pivot_df.columns]
    pivot_df = pivot_df[new_column_order]
    
    return pivot_df

def load_css(file_path="styles.css"):
    """Load CSS from file"""
    try:
        with open(file_path, 'r') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"CSS file not found: {file_path}")