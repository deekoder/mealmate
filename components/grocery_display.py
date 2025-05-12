# components/grocery_display.py
import streamlit as st
from utils.data_processing import parse_grocery_list_to_dict

def display_grocery_list(grocery_list_text):
    """
    Display the grocery list organized by categories.
    
    Args:
        grocery_list_text: Raw text of the grocery list
    """
    st.markdown("## 🛒 Grocery List")
    try:
        grocery_categories = parse_grocery_list_to_dict(grocery_list_text)
        
        if grocery_categories:
            # Create tabs for each grocery category
            try:
                category_tabs = st.tabs(list(grocery_categories.keys()))
                
                for tab, (category, items) in zip(category_tabs, grocery_categories.items()):
                    with tab:
                        if items:
                            for item in items:
                                st.markdown(f"• {item}")
                        else:
                            st.write("No items in this category")
                
                # Add download button for grocery list
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.download_button(
                        label="📥 Grocery List",
                        data=grocery_list_text,
                        file_name=f"grocery_list.txt",
                        mime="text/plain"
                    )
            except Exception as e:
                st.error(f"Error displaying grocery categories: {str(e)}")
                # Fallback to simple display
                st.text(grocery_list_text)
        else:
            st.text(grocery_list_text)
    except Exception as e:
        st.error(f"Error parsing grocery list: {str(e)}")
        st.text(grocery_list_text)