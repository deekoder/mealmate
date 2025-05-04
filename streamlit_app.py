# streamlit_app.py
import streamlit as st
from meal_planner import VegetarianMealPlanner
import io
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

# Sidebar for API key and date selection
with st.sidebar:
    st.header("Configuration")
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
                
                # Display meal plan
                st.markdown("## 📅 Your Weekly Meal Plan")
                st.markdown(f"**Period:** {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}")
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
                
                # Display grocery list separately
                st.markdown("## 🛒 Grocery List")
                st.text(grocery_list)
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
else:
    st.warning("Please enter your OpenAI API key in the sidebar to get started.")

# Footer
st.markdown("---")
st.markdown("Created for AI Class Project | MIT License")