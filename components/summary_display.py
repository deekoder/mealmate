# components/summary_display.py
import streamlit as st

def display_summary(df_meals):
    """
    Display summary statistics about the meal plan.
    
    Args:
        df_meals: DataFrame with meal data
    """
    st.markdown("## 📊 Summary")
    try:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            try:
                st.metric("Total Meals", len(df_meals) if df_meals is not None else 0)
            except Exception as e:
                st.metric("Total Meals", 0)
        
        with col2:
            try:
                if df_meals is not None and 'Day' in df_meals.columns:
                    st.metric("Days Covered", len(df_meals['Day'].unique()))
                elif df_meals is not None and 'Date' in df_meals.columns:
                    st.metric("Days Covered", len(df_meals['Date'].unique()))
                else:
                    st.metric("Days Covered", 0)
            except Exception as e:
                st.metric("Days Covered", 0)
        
        with col3:
            try:
                if df_meals is not None and 'Meal' in df_meals.columns:
                    meal_types = df_meals['Meal'].value_counts()
                    st.metric("Meal Types", len(meal_types))
                else:
                    st.metric("Meal Types", 0)
            except Exception as e:
                st.metric("Meal Types", 0)
        
        with col4:
            try:
                recipes_count = len(st.session_state.recipes) if hasattr(st.session_state, 'recipes') else 0
                evals_count = len(st.session_state.evaluations) if hasattr(st.session_state, 'evaluations') else 0
                st.metric("Recipes Generated", f"{recipes_count} ({evals_count} evaluated)")
            except Exception as e:
                st.metric("Recipes Generated", 0)
    except Exception as e:
        st.error(f"Error displaying summary: {str(e)}")