# utils.py
import re
import pandas as pd
import streamlit as st  # Added import for streamlit
import os


def parse_meal_plan_to_dataframe(meal_plan_text):
    """Parse the meal plan text into a structured DataFrame."""
    # Check if meal_plan_text is None or empty
    if not meal_plan_text:
        return pd.DataFrame(columns=['Day', 'Date', 'Meal', 'Meal Name'])
    
    # Initialize lists to store data
    days = []
    dates = []
    meals = []
    meal_names = []
    
    # Regular expressions for parsing
    day_pattern = r'---\s+(\w+),\s+(\w+\s+\d+,\s+\d+)\s+---'  # Match both day name and date
    meal_pattern = r'(Breakfast|Lunch|Dinner|Snack):\s+(.+?)(?=\n\nLunch:|\\nLunch:|\\n\\nLunch:|\n\nDinner:|\\nDinner:|\\n\\nDinner:|\n\nSnack:|\\nSnack:|\\n\\nSnack:|\n\nBatch|\n\n---|$)'
    
    # Find all days in the text
    day_matches = re.finditer(day_pattern, meal_plan_text)
    
    for day_match in day_matches:
        day = day_match.group(1)  # Extract day name
        date = day_match.group(2)  # Extract date
        
        # Find the current day's section
        start_pos = day_match.end()
        next_day = re.search(day_pattern, meal_plan_text[start_pos:])
        
        if next_day:
            day_section = meal_plan_text[start_pos:start_pos + next_day.start()]
        else:
            day_section = meal_plan_text[start_pos:]
        
        # Find all meals in the current day's section
        meal_matches = re.finditer(meal_pattern, day_section, re.DOTALL)
        
        for meal_match in meal_matches:
            meal_type = meal_match.group(1)  # Breakfast, Lunch, etc.
            meal_content = meal_match.group(2).strip()
            
            # Split by 'Note:' to get just the meal name
            meal_parts = meal_content.split('Note:')
            meal_name = meal_parts[0].strip()
            
            # Add to lists
            days.append(day)
            dates.append(date)
            meals.append(meal_type)
            meal_names.append(meal_name)
    
    # Create DataFrame
    if days and meals and meal_names:
        df = pd.DataFrame({
            'Day': days,
            'Date': dates,
            'Meal': meals,
            'Meal Name': meal_names
        })
        return df
    
    # Fallback method if the parsing didn't work
    # This is a simplified parsing approach that will work with most meal plan formats
    fallback_days = []
    fallback_dates = []
    fallback_meals = []
    fallback_meal_names = []
    
    # Try simpler pattern matches
    simple_day_pattern = r'---\s+(.*?)---'
    simple_meal_pattern = r'(Breakfast|Lunch|Dinner|Snack):\s+([^\n]+)'
    
    day_matches = re.finditer(simple_day_pattern, meal_plan_text)
    
    for day_match in day_matches:
        day_header = day_match.group(1).strip()
        
        # Try to extract day name and date from the header
        try:
            day_parts = day_header.split(',', 1)
            day = day_parts[0].strip()
            date = day_parts[1].strip() if len(day_parts) > 1 else "Unknown Date"
        except:
            day = "Unknown Day"
            date = "Unknown Date"
        
        # Find the current day's section
        start_pos = day_match.end()
        next_day = re.search(simple_day_pattern, meal_plan_text[start_pos:])
        
        if next_day:
            day_section = meal_plan_text[start_pos:start_pos + next_day.start()]
        else:
            day_section = meal_plan_text[start_pos:]
        
        # Find meals with simpler pattern
        meal_matches = re.finditer(simple_meal_pattern, day_section)
        
        for meal_match in meal_matches:
            meal_type = meal_match.group(1)
            meal_name = meal_match.group(2).strip()
            
            fallback_days.append(day)
            fallback_dates.append(date)
            fallback_meals.append(meal_type)
            fallback_meal_names.append(meal_name)
    
    # Use fallback data if available
    if fallback_days and fallback_meals and fallback_meal_names:
        df = pd.DataFrame({
            'Day': fallback_days,
            'Date': fallback_dates,
            'Meal': fallback_meals,
            'Meal Name': fallback_meal_names
        })
        return df
    
    # If all parsing methods fail, create a default DataFrame to avoid errors
    default_data = []
    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    meal_types = ['Breakfast', 'Lunch', 'Dinner', 'Snack']
    
    # Extract date range from meal plan if possible
    period_match = re.search(r'Period:\s+(\w+\s+\d+,\s+\d+)\s+to\s+(\w+\s+\d+,\s+\d+)', meal_plan_text)
    if period_match:
        start_date = period_match.group(1)
        end_date = period_match.group(2)
    else:
        start_date = "Unknown Start Date"
        end_date = "Unknown End Date"
    
    # Add at least one row for each day to avoid errors
    for i, day in enumerate(days_of_week):
        for meal in meal_types:
            default_data.append({
                'Day': day,
                'Date': f"May {10+i}, 2025",
                'Meal': meal,
                'Meal Name': f"Default {meal.lower()} for {day}"
            })
    
    return pd.DataFrame(default_data)

def create_pivot_table(df):
    """Create a pivot table from the meal plan DataFrame."""
    try:
        # Make a copy to avoid modifying the original
        df_copy = df.copy()
        
        # Ensure required columns exist
        required_columns = ['Day', 'Meal', 'Meal Name']
        for col in required_columns:
            if col not in df_copy.columns:
                if col == 'Day' and 'Date' in df_copy.columns:
                    # Extract day from date if possible
                    df_copy['Day'] = df_copy['Date'].apply(lambda x: x.split(',')[0] if isinstance(x, str) and ',' in x else "Unknown")
                else:
                    # Add a default column if missing
                    df_copy[col] = "Unknown"
        
        # Create the pivot table
        pivot_index = 'Day' if 'Day' in df_copy.columns else 'Date'
        pivot_df = df_copy.pivot(index=pivot_index, columns='Meal', values='Meal Name')
        
        # Reset index to make the pivot column a regular column
        pivot_df = pivot_df.reset_index()
        
        return pivot_df
    
    except Exception as e:
        # If pivot fails, return a simple formatted version of the dataframe
        print(f"Pivot table creation failed: {str(e)}")
        
        # Create a simplified table with the main columns
        if 'Day' in df.columns and 'Meal' in df.columns and 'Meal Name' in df.columns:
            simple_df = df[['Day', 'Meal', 'Meal Name']].copy()
            return simple_df
        else:
            # Return the original dataframe if we can't create a simplified version
            return df

def parse_grocery_list_to_dict(grocery_list_text):
    """Parse the grocery list text into a dictionary organized by category."""
    if not grocery_list_text:
        return {}
    
    categories = {}
    current_category = "Uncategorized"
    categories[current_category] = []
    
    # Split the text into lines and process each line
    lines = grocery_list_text.split('\n')
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
        
        # Check if the line is a category header
        if line.isupper() or line.endswith(':') or line.endswith('ITEMS') or line.endswith('Items'):
            current_category = line.rstrip(':')
            if current_category not in categories:
                categories[current_category] = []
        
        # Check if the line is a list item (starts with -, *, or •)
        elif line.startswith(('-', '*', '•', '1.', '2.', '3.')) or any(line.startswith(str(i) + '.') for i in range(1, 10)):
            # Remove the list marker and add to the current category
            item = line.lstrip('-*•0123456789. ')
            categories[current_category].append(item)
        
        # If it's not a category or a list marker, it might be a plain item
        elif categories[current_category] or current_category == "Uncategorized":
            categories[current_category].append(line)
    
    # Remove empty categories
    categories = {k: v for k, v in categories.items() if v}
    
    # If no structured categories were found, try a different approach
    if len(categories) <= 1:
        categories = {}
        # Common grocery categories
        common_categories = [
            "PRODUCE", "FRUITS AND VEGETABLES", "FRUITS", "VEGETABLES",
            "GRAINS", "BREAD AND GRAINS", "BREAD", "PASTA", "RICE",
            "PROTEINS", "PROTEIN", "MEAT ALTERNATIVES", "BEANS AND LEGUMES",
            "DAIRY", "DAIRY AND ALTERNATIVES", "DAIRY/ALTERNATIVES",
            "PANTRY", "PANTRY ITEMS", "CANNED GOODS", "CANNED",
            "SPICES", "HERBS AND SPICES", "SEASONINGS",
            "CONDIMENTS", "SAUCES", "OILS",
            "SNACKS", "NUTS AND SEEDS", "NUTS", "SEEDS",
            "FROZEN", "FROZEN FOODS",
            "BAKERY", "BAKED GOODS",
            "BEVERAGES", "DRINKS"
        ]
        
        # Find sections based on common category names
        for category in common_categories:
            pattern = rf'{category}[:\s]*\n((?:(?!{"|".join(common_categories)}).)*)(?={"|".join(common_categories)}|\Z)'
            matches = re.finditer(pattern, grocery_list_text, re.IGNORECASE | re.DOTALL)
            
            for match in matches:
                category_items = []
                items_text = match.group(1).strip()
                item_lines = items_text.split('\n')
                
                for item_line in item_lines:
                    item = item_line.strip().lstrip('-*•0123456789. ')
                    if item:
                        category_items.append(item)
                
                if category_items:
                    categories[category] = category_items
    
    # If still no structured categories, create basic ones based on line patterns
    if not categories:
        categories = {
            "Produce": [],
            "Grains & Bread": [],
            "Proteins": [],
            "Dairy & Alternatives": [],
            "Pantry Items": [],
            "Spices & Herbs": [],
            "Other": []
        }
        
        current_category = "Other"
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Simple heuristic to categorize items
            lower_line = line.lower()
            item = line.lstrip('-*•0123456789. ')
            
            if any(word in lower_line for word in ['vegetable', 'fruit', 'fresh', 'produce', 'lettuce', 'spinach', 'tomato', 'apple']):
                categories['Produce'].append(item)
            elif any(word in lower_line for word in ['bread', 'grain', 'pasta', 'rice', 'cereal', 'flour']):
                categories['Grains & Bread'].append(item)
            elif any(word in lower_line for word in ['protein', 'tofu', 'bean', 'lentil', 'legume', 'nut', 'seed', 'tempeh']):
                categories['Proteins'].append(item)
            elif any(word in lower_line for word in ['dairy', 'milk', 'yogurt', 'cheese', 'cream', 'alternative']):
                categories['Dairy & Alternatives'].append(item)
            elif any(word in lower_line for word in ['pantry', 'canned', 'jar', 'oil', 'sauce', 'condiment']):
                categories['Pantry Items'].append(item)
            elif any(word in lower_line for word in ['spice', 'herb', 'seasoning', 'powder', 'salt', 'pepper']):
                categories['Spices & Herbs'].append(item)
            else:
                categories['Other'].append(item)
    
    # Remove empty categories
    return {k: v for k, v in categories.items() if v}

def load_css(file_path="styles.css"):
    """Load CSS from file"""
    try:
        with open(file_path, 'r') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"CSS file not found: {file_path}")