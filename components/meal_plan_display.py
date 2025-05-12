# components/meal_plan_display.py
import streamlit as st
from utils.data_processing import parse_meal_plan_to_dataframe, create_pivot_table, generate_unique_id
import traceback

def display_meal_plan(meal_plan, start_date, end_date, show_reasoning=False, meal_plan_data=None):
    """
    Display the meal plan including reasoning if enabled.
    
    Args:
        meal_plan: Text of the meal plan
        start_date: Start date of the meal plan
        end_date: End date of the meal plan
        show_reasoning: Whether to show nutritional reasoning
        meal_plan_data: Structured data with reasoning if available
        
    Returns:
        DataFrame of parsed meal data
    """
    st.markdown("## 📅 Your Weekly Meal Plan")
    st.markdown(f"**Period:** {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}")
    
    # Display reasoning if enabled and available
    if show_reasoning and meal_plan_data:
        _display_meal_plan_reasoning(meal_plan_data)

    # Parse and display meal plan as table
    try:
        df_meals = parse_meal_plan_to_dataframe(meal_plan)
        
        # Display table
        if not df_meals.empty:
            try:
                # Create a unique identifier for each meal
                df_meals['unique_id'] = df_meals.apply(generate_unique_id, axis=1)
                
                # Save the original dataframe in session state for recipe generation
                st.session_state.meal_plan_df = df_meals.copy()
                
                # Create and display pivot table
                pivot_df = create_pivot_table(df_meals)
                
                # Ensure columns are in the right order
                desired_columns = ['Day']
                meal_columns = ['Breakfast', 'Lunch', 'Dinner', 'Snack']
                for col in meal_columns:
                    if col in pivot_df.columns:
                        desired_columns.append(col)
                
                # Reorder columns if possible
                if all(col in pivot_df.columns for col in desired_columns):
                    pivot_df = pivot_df[desired_columns]
                
                st.dataframe(pivot_df, use_container_width=True, hide_index=True)
                
                # Add download button for meal plan
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.download_button(
                        label="📥 Meal Plan",
                        data=meal_plan,
                        file_name=f"meal_plan_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.txt",
                        mime="text/plain"
                    )
                
                return df_meals
            except Exception as e:
                st.error(f"Error creating table view: {str(e)}")
                st.error(traceback.format_exc())
                # Fallback to simpler display
                st.dataframe(df_meals, use_container_width=True)
                return df_meals
        else:
            st.warning("Could not parse the meal plan into a table. Showing raw text:")
            st.text(meal_plan)
            return None
    except Exception as e:
        st.error(f"Error parsing meal plan: {str(e)}")
        st.error(traceback.format_exc())
        st.text(meal_plan)
        return None

def _display_meal_plan_reasoning(meal_plan_data):
    """Display the nutritional reasoning behind the meal plan"""
    reasoning_data = meal_plan_data.get('reasoning', {})
    
    if reasoning_data:
        with st.expander("💡 Nutritional Reasoning & Strategy", expanded=True):
            # Create tabs for different aspects of reasoning
            reasoning_tabs = st.tabs([
                "Pre-Diabetic Strategy", 
                "Vegetarian Nutrition", 
                "Meal Variety"
            ])
            
            # Process and display each reasoning aspect
            with reasoning_tabs[0]:
                diabetic_text = reasoning_data.get("pre_diabetic_considerations", 
                                reasoning_data.get("nutritional_considerations", ""))
                
                # Add visual enhancements
                highlight_terms = [
                    ("glycemic index", "📊 **glycemic index**"),
                    ("blood sugar", "🩸 **blood sugar**"),
                    ("carbohydrates", "🌾 **carbohydrates**"),
                    ("fiber", "🌱 **fiber**"),
                    ("protein", "💪 **protein**"),
                    ("fat", "🥑 **fat**"),
                ]
                
                enhanced_text = str(diabetic_text)
                for term, replacement in highlight_terms:
                    enhanced_text = enhanced_text.replace(term, replacement)
                
                st.markdown(enhanced_text)
                
                # Add educational info box
                st.info("""
                **Why This Matters**: Pre-diabetic diets focus on managing blood sugar while ensuring complete nutrition. 
                Low glycemic foods, adequate protein, and fiber-rich choices help maintain stable glucose levels.
                """)
            
            with reasoning_tabs[1]:
                veg_text = reasoning_data.get("vegetarian_considerations", 
                           reasoning_data.get("protein_sources", ""))
                
                if not veg_text:
                    veg_text = """
                    This meal plan ensures complete vegetarian nutrition by:
                    
                    - **Diverse protein sources** including legumes, tofu, tempeh, dairy, nuts, and seeds
                    - **Complete amino acid profiles** through complementary proteins
                    - **Strategic inclusion of foods rich in iron, B12, zinc, and calcium** that can be lacking in vegetarian diets
                    - **Healthy fat sources** from nuts, seeds, avocados, and olive oil
                    """
                
                st.markdown(str(veg_text))
                
                # Visual element - protein sources table
                st.subheader("Key Protein Sources in Your Meal Plan")
                protein_sources = {
                    "Source": ["Legumes", "Dairy", "Tofu/Tempeh", "Nuts & Seeds", "Whole Grains"],
                    "Protein (g/serving)": ["7-9", "8-10", "10-20", "5-7", "3-5"],
                    "Complete Protein": ["No*", "Yes", "Yes", "No*", "No*"],
                    "Key Benefits": ["Fiber, Iron", "Calcium, B12", "All Amino Acids", "Healthy Fats", "Fiber, B Vitamins"]
                }
                st.dataframe(protein_sources, use_container_width=True)
                st.caption("* Incomplete proteins can be combined to form complete protein profiles")
            
            with reasoning_tabs[2]:
                variety_text = reasoning_data.get("meal_variety", 
                               reasoning_data.get("meal_balance", ""))
                
                if not variety_text:
                    variety_text = """
                    The meal plan incorporates variety through:
                    
                    - **Diverse cuisines and flavor profiles** to prevent menu fatigue
                    - **Different cooking techniques** to vary textures and taste experiences
                    - **Strategic leftovers planning** for efficiency without repetition
                    - **Seasonal ingredients** for freshness and nutritional diversity
                    - **Balance of different food groups** across the week
                    """
                
                st.markdown(str(variety_text))