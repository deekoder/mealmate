# streamlit_app.py
import streamlit as st
from VegetarianMealPlanner import VegetarianMealPlanner
import pandas as pd
import re
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Vegetarian Meal Planner",
    page_icon="🥗",
    layout="wide"
)

st.title("🥗 Vegetarian Meal Planner for Pre-Diabetic")
st.markdown("""
Generate a weekly meal plan optimized for vegetarian pre-diabetic diet.
This app creates personalized meal plans with bulk cooking strategies and grocery lists.
""")

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

# Sidebar for API key and date selection
with st.sidebar:
    st.header("Configuration")
    
    # API key input field
    api_key = st.text_input("OpenAI API Key", type="password")
    st.markdown("[Get API Key](https://platform.openai.com/api-keys)")
    
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
                
                # Display meal plan as table
                st.markdown("## 📅 Your Weekly Meal Plan")
                st.markdown(f"**Period:** {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}")
                
                # Parse and display meal plan as table
                df_meals = parse_meal_plan_to_dataframe(meal_plan)
                
                # Display table
                if not df_meals.empty:
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
                    
                    # Display the table with enhanced styling
                    st.dataframe(pivot_df, use_container_width=True, hide_index=True)
                    
                    # Add custom CSS for table styling
                    st.markdown("""
                    <style>
                    .stDataFrame {
                        font-size: 14px;
                    }
                    .stDataFrame th {
                        background-color: #4CAF50;
                        color: white;
                        font-weight: bold;
                        border: 1px solid #ddd;
                        padding: 8px;
                    }
                    .stDataFrame td {
                        border: 1px solid #ddd;
                        padding: 8px;
                    }
                    .stDataFrame tr:nth-child(even) {
                        background-color: #f2f2f2;
                    }
                    .stDataFrame tr:hover {
                        background-color: #ddd;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("Could not parse the meal plan into a table. Showing raw text:")
                    st.text(meal_plan)
                
                # Download buttons
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        label="📥 Download Meal Plan",
                        data=meal_plan,
                        file_name=f"meal_plan_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.txt",
                        mime="text/plain"
                    )
                
                with col2:
                    st.download_button(
                        label="📥 Download Grocery List",
                        data=grocery_list,
                        file_name=f"grocery_list_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.txt",
                        mime="text/plain"
                    )
                
                # Display grocery list as organized sections
                st.markdown("## 🛒 Grocery List")
                grocery_categories = parse_grocery_list_to_dict(grocery_list)
                
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
                    st.text(grocery_list)
                
                # Add summary statistics
                if not df_meals.empty:
                    st.markdown("## 📊 Summary")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Meals", len(df_meals))
                    with col2:
                        st.metric("Days Covered", len(df_meals['Day'].unique()))
                    with col3:
                        meal_types = df_meals['Meal'].value_counts()
                        st.metric("Meal Types", len(meal_types))
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.error(f"Error details: {type(e).__name__}")
else:
    st.warning("Please enter your OpenAI API key in the sidebar to get started.")

# Footer
st.markdown("---")
st.markdown("Created for AI Class Project | MIT License")