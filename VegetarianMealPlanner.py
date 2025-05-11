# VegetarianMealPlanner.py
import json
from datetime import datetime, timedelta
from openai import OpenAI

class VegetarianMealPlanner:
    def __init__(self, api_key):
        """Initialize the VegetarianMealPlanner with an OpenAI API key."""
        self.client = OpenAI(api_key=api_key)
        self.meal_plan = ""
        self.grocery_list = ""
        self.meal_plan_data = None
        
    def generate_meal_plan(self, start_date, end_date):
        """Generate a meal plan for a specified date range."""
        # Format dates to strings if they're datetime objects
        if isinstance(start_date, datetime):
            start_date_str = start_date.strftime("%B %d, %Y")
        else:
            start_date_str = start_date.strftime("%B %d, %Y")
            
        if isinstance(end_date, datetime):
            end_date_str = end_date.strftime("%B %d, %Y")
        else:
            end_date_str = end_date.strftime("%B %d, %Y")
            
        # Create prompt for generating a meal plan
        prompt = f"""
        Create a vegetarian meal plan for pre-diabetic individuals from {start_date_str} to {end_date_str}.
        
        For each day, include:
        - Breakfast
        - Lunch
        - Dinner
        - Snack
        
        For each meal, provide a specific dish name. Focus on low glycemic index ingredients, 
        adequate protein, and fiber-rich options that help manage blood sugar levels.
        
        Include ideas for batch cooking and efficient meal prep strategies.
        
        Format each day like this:
        --- Day Name, Month Day, Year ---
        
        Breakfast: [Meal Name]
        
        Lunch: [Meal Name]
        
        Dinner: [Meal Name]
        
        Snack: [Meal Name]
        
        [Any additional notes or batch cooking tips]
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4",  # or whichever model you're using
            messages=[
                {"role": "system", "content": "You are a nutritionist specializing in vegetarian pre-diabetic meal planning."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        self.meal_plan = response.choices[0].message.content
        return self.meal_plan
    
    def generate_meal_plan_with_cot(self, start_date, end_date, complexity="Moderate"):
        """
        Generate a meal plan using Chain-of-Thought reasoning.
        This enhances the quality of meal plans by guiding the model through a structured thought process.
        
        Args:
            start_date: Start date (datetime or string in format %Y-%m-%d)
            end_date: End date (datetime or string in format %Y-%m-%d)
            complexity: Meal complexity level (Simple, Moderate, Complex)
            
        Returns:
            dict: A structured meal plan with reasoning
        """
        # Format dates to strings if they're datetime objects
        if isinstance(start_date, datetime):
            start_date_str = start_date.strftime("%B %d, %Y")
            start_date_iso = start_date.strftime("%Y-%m-%d")
        else:
            start_date_str = start_date.strftime("%B %d, %Y")
            start_date_iso = start_date.strftime("%Y-%m-%d")
            
        if isinstance(end_date, datetime):
            end_date_str = end_date.strftime("%B %d, %Y")
            end_date_iso = end_date.strftime("%Y-%m-%d")
        else:
            end_date_str = end_date.strftime("%B %d, %Y")
            end_date_iso = end_date.strftime("%Y-%m-%d")
        
        # Calculate the number of days in the range
        start = datetime.strptime(start_date_iso, "%Y-%m-%d")
        end = datetime.strptime(end_date_iso, "%Y-%m-%d")
        days_diff = (end - start).days + 1
        
        # Adjust complexity instructions
        complexity_instructions = ""
        if complexity == "Simple":
            complexity_instructions = "Focus on simple recipes with minimal ingredients and quick preparation times. Prioritize dishes that can be made in 30 minutes or less."
        elif complexity == "Complex":
            complexity_instructions = "Include more elaborate recipes with diverse ingredients and techniques. You can suggest dishes that take longer to prepare and have more sophisticated flavor profiles."
        else:  # Moderate
            complexity_instructions = "Balance simplicity and variety. Include some quick recipes and some that take more time, with a moderate level of culinary complexity."
        
        # Create a Chain-of-Thought prompt
        cot_prompt = f"""
        You are an expert nutritionist and chef specializing in vegetarian meal planning for pre-diabetic individuals.
        
        Please create a detailed vegetarian meal plan from {start_date_str} to {end_date_str} ({days_diff} days).
        {complexity_instructions}
        
        First, I'll think through this meal planning process step-by-step:
        
        Step 1: Consider the specific nutritional requirements for pre-diabetic individuals.
        - Pre-diabetic individuals need to carefully manage blood sugar levels
        - They should prioritize low glycemic index foods that don't cause blood sugar spikes
        - A balanced macronutrient profile is essential: moderate carbs (focusing on complex carbs), adequate protein (challenging in vegetarian diets), and healthy fats
        - High fiber intake helps regulate blood sugar and improves satiety
        - Need to ensure adequate micronutrients, especially those that support insulin sensitivity like magnesium, chromium, and certain B vitamins
        
        Step 2: Create a framework for balanced vegetarian nutrition.
        - Identify diverse protein sources (legumes, tofu, tempeh, dairy if allowed, nuts, seeds)
        - Plan for complex carbohydrates in appropriate portions (whole grains, starchy vegetables)
        - Incorporate healthy fats (avocado, olive oil, nuts, seeds)
        - Ensure abundant non-starchy vegetables for fiber, vitamins, and minerals
        - Consider calcium sources for bone health
        - Include vitamin B12 sources or supplements as it's primarily found in animal products
        
        Step 3: Plan for variety and enjoyment across the {days_diff}-day period.
        - Rotate protein sources throughout the week
        - Vary cooking methods and flavor profiles
        - Consider cultural food traditions for inspiration
        - Plan for practical aspects like leftovers and meal prep
        - Ensure meals are satisfying and don't feel restrictive
        
        Step 4: For each specific date, craft a daily meal plan that:
        - Distributes nutrients appropriately throughout the day
        - Keeps blood sugar stable with properly timed meals and snacks
        - Considers the appropriate calorie range for maintaining healthy weight
        - Includes seasonal produce when possible
        - Provides adequate hydration recommendations
        
        Now I'll create a complete meal plan based on this reasoning.
        
        For each day, I'll provide:
        1. The specific date in YYYY-MM-DD format
        2. A breakfast, lunch, dinner, and snack option with specific dish names
        3. A brief note about why each meal is suitable for a pre-diabetic vegetarian diet
        4. Batch cooking opportunities and meal prep tips
        
        Please provide this as structured JSON with two main sections:
        1. "reasoning" - containing your nutritional strategy, key considerations, and approach, organized into subsections:
           - "pre_diabetic_considerations" - specific nutritional strategies for managing pre-diabetes
           - "vegetarian_considerations" - ensuring complete nutrition in a plant-based diet
           - "meal_variety" - approaches to ensuring diverse and satisfying meals
        
        2. "days" - an array of daily meal plans, each containing:
           - "date": in YYYY-MM-DD format
           - "breakfast": specific meal name
           - "breakfast_note": why this breakfast works for pre-diabetic vegetarians
           - "lunch": specific meal name
           - "lunch_note": why this lunch works for pre-diabetic vegetarians
           - "dinner": specific meal name
           - "dinner_note": why this dinner works for pre-diabetic vegetarians
           - "snack": specific snack name
           - "snack_note": why this snack works for pre-diabetic vegetarians
           - "batch_cooking": any meal prep opportunities for this day
        
        3. Additional optional sections:
           - "batch_cooking_summary": overview of batch cooking strategy for the week
           - "general_notes": any additional tips or considerations
           
        Ensure the JSON is valid and properly formatted.
        """
        
        # Call OpenAI API with the CoT prompt using the updated API
        response = self.client.chat.completions.create(
            model="gpt-4",  # or your preferred model
            messages=[
                {"role": "system", "content": "You are a helpful assistant specializing in nutrition."},
                {"role": "user", "content": cot_prompt}
            ],
            temperature=0.7,
            max_tokens=3000
        )
        
        try:
            # Try to parse as JSON
            meal_plan_data = json.loads(response.choices[0].message.content)
            
            # Store the raw response for later extraction
            self.meal_plan_data = meal_plan_data
            
            # Format the meal plan into a text representation for backward compatibility
            self.meal_plan = self.format_meal_plan_from_cot(meal_plan_data)
            
            return meal_plan_data
            
        except json.JSONDecodeError:
            # If not valid JSON, use the raw text and try to extract some structure
            raw_content = response.choices[0].message.content
            self.meal_plan = raw_content
            
            # Create a basic structure for the reasoning
            meal_plan_data = {
                "reasoning": {
                    "pre_diabetic_considerations": "The model didn't return structured data, but the meal plan follows pre-diabetic nutritional guidelines.",
                    "vegetarian_considerations": "The meal plan includes diverse plant-based protein sources and essential nutrients.",
                    "meal_variety": "The meal plan offers variety in flavors, textures, and cooking methods."
                },
                "days": []
            }
            
            # Try to extract days and meals from the text (very basic extraction)
            import re
            
            # Generate date range
            date_range = [start + timedelta(days=x) for x in range(days_diff)]
            
            # Look for day patterns in the text
            day_patterns = [
                r"Day \d+:.*?(?=Day \d+:|$)",  # "Day 1: ..." format
                r"\*\*\s*\w+,\s*\w+\s*\d+\s*\*\*.*?(?=\*\*\s*\w+|$)",  # "** Monday, January 1 **" format
                r"\w+,\s*\w+\s*\d+.*?(?=\w+,\s*\w+\s*\d+|$)"  # "Monday, January 1" format
            ]
            
            for pattern in day_patterns:
                day_sections = re.findall(pattern, raw_content, re.DOTALL)
                if day_sections:
                    break
            
            # If we found day sections, try to extract meals
            if day_sections:
                for i, section in enumerate(day_sections):
                    if i < len(date_range):
                        date_obj = date_range[i]
                        
                        # Extract meals with basic patterns
                        breakfast = re.search(r"Breakfast:(.+?)(?=Lunch:|Dinner:|Snack:|$)", section, re.DOTALL)
                        lunch = re.search(r"Lunch:(.+?)(?=Breakfast:|Dinner:|Snack:|$)", section, re.DOTALL)
                        dinner = re.search(r"Dinner:(.+?)(?=Breakfast:|Lunch:|Snack:|$)", section, re.DOTALL)
                        snack = re.search(r"Snack:(.+?)(?=Breakfast:|Lunch:|Dinner:|$)", section, re.DOTALL)
                        
                        day_data = {
                            "date": date_obj.strftime("%Y-%m-%d"),
                            "breakfast": breakfast.group(1).strip() if breakfast else "Not specified",
                            "lunch": lunch.group(1).strip() if lunch else "Not specified",
                            "dinner": dinner.group(1).strip() if dinner else "Not specified",
                            "snack": snack.group(1).strip() if snack else "Not specified"
                        }
                        
                        meal_plan_data["days"].append(day_data)
            
            return meal_plan_data
    
    def format_meal_plan_from_cot(self, meal_plan_data):
        """Convert the structured meal plan data to text format for compatibility with existing code."""
        formatted_text = "VEGETARIAN MEAL PLAN FOR PRE-DIABETICS\n\n"
        
        # Add date range
        if meal_plan_data.get("days") and len(meal_plan_data["days"]) > 0:
            first_day = meal_plan_data["days"][0].get("date", "")
            last_day = meal_plan_data["days"][-1].get("date", "")
            
            if first_day and last_day:
                try:
                    start = datetime.strptime(first_day, "%Y-%m-%d")
                    end = datetime.strptime(last_day, "%Y-%m-%d")
                    formatted_text += f"Period: {start.strftime('%B %d, %Y')} to {end.strftime('%B %d, %Y')}\n\n"
                except:
                    pass
        
        # Format each day - ensure consistent format that can be parsed
        for day_data in meal_plan_data.get("days", []):
            date_str = day_data.get("date", "")
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                day_header = date_obj.strftime("%A, %B %d, %Y")
            except:
                day_header = "Monday, January 1, 2024"  # Fallback
        
            formatted_text += f"--- {day_header} ---\n\n"
            
            # Handle all values to ensure they're strings
            breakfast = str(day_data.get('breakfast', 'Oatmeal with fruit'))
            lunch = str(day_data.get('lunch', 'Veggie salad'))
            dinner = str(day_data.get('dinner', 'Vegetable stir-fry'))
            snack = str(day_data.get('snack', 'Mixed nuts'))
            
            # Add meals - ensure each meal has clean, parseable format
            formatted_text += f"Breakfast: {breakfast}\n"
            if "breakfast_note" in day_data and day_data['breakfast_note']:
                formatted_text += f"Note: {str(day_data['breakfast_note'])}\n"
            
            formatted_text += f"\nLunch: {lunch}\n"
            if "lunch_note" in day_data and day_data['lunch_note']:
                formatted_text += f"Note: {str(day_data['lunch_note'])}\n"
            
            formatted_text += f"\nDinner: {dinner}\n"
            if "dinner_note" in day_data and day_data['dinner_note']:
                formatted_text += f"Note: {str(day_data['dinner_note'])}\n"
            
            formatted_text += f"\nSnack: {snack}\n"
            if "snack_note" in day_data and day_data['snack_note']:
                formatted_text += f"Note: {str(day_data['snack_note'])}\n"
            
            # Add batch cooking tips if available
            if "batch_cooking" in day_data and day_data['batch_cooking']:
                formatted_text += f"\nBatch Cooking: {str(day_data['batch_cooking'])}\n"
            
            formatted_text += "\n\n"
        
        # Add batch cooking summary if available
        if "batch_cooking_summary" in meal_plan_data and meal_plan_data['batch_cooking_summary']:
            formatted_text += f"BATCH COOKING STRATEGIES:\n{str(meal_plan_data['batch_cooking_summary'])}\n\n"
        
        # Add any general notes from the meal plan
        if "general_notes" in meal_plan_data and meal_plan_data['general_notes']:
            formatted_text += f"GENERAL NOTES:\n{str(meal_plan_data['general_notes'])}\n\n"
        
        return formatted_text
        
    def extract_grocery_list(self):
        """Generate a grocery list from the meal plan."""
        if not self.meal_plan:
            return "Please generate a meal plan first."
        
        prompt = f"""
        Based on the following vegetarian meal plan for pre-diabetics, create a comprehensive grocery list
        organized by category (Produce, Grains, Proteins, Dairy/Alternatives, Pantry Items, Spices, etc.).
        
        Meal Plan:
        {self.meal_plan}
        
        Please be thorough and include all ingredients needed for the meals in the plan.
        Organize items by category for easy shopping.
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4",  # or your preferred model
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates organized grocery lists."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        
        self.grocery_list = response.choices[0].message.content
        return self.grocery_list