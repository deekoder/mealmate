# VegetarianMealPlanner.py
from openai import OpenAI
import json
from datetime import datetime, timedelta
import os

class VegetarianMealPlanner:
    def __init__(self, openai_api_key):
        """Initialize the meal planner with OpenAI API key"""
        self.client = OpenAI(api_key=openai_api_key)
        self.meal_plan = None
        self.grocery_list = None
        
    def get_current_week_dates(self):
        """Get start and end dates for the current week"""
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        return start_of_week, end_of_week
    
    def generate_meal_plan(self, start_date=None, end_date=None):
        """Generate a weekly vegetarian meal plan using OpenAI"""
        if start_date is None or end_date is None:
            start_date, end_date = self.get_current_week_dates()
        
        # Convert to datetime if they're date objects
        if hasattr(start_date, 'strftime') and not hasattr(start_date, 'hour'):
            start_date = datetime.combine(start_date, datetime.min.time())
        if hasattr(end_date, 'strftime') and not hasattr(end_date, 'hour'):
            end_date = datetime.combine(end_date, datetime.min.time())
        
        prompt = f"""You are a vegetarian meal planning expert specializing in pre-diabetic nutrition. Create a weekly meal plan with the following requirements:

CONTEXT:
- Focus on vegetarian foods only (no meat, fish, poultry)
- Optimize for pre-diabetic diet (low glycemic index, high protein, controlled carbs)
- Include bulk cooking strategies for weekends
- Date range: {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}

IMPORTANT: Follow this EXACT template format for easy parsing:

# VEGETARIAN MEAL PLAN

## Week Overview
Start Date: {start_date.strftime('%B %d, %Y')}
End Date: {end_date.strftime('%B %d, %Y')}

## Daily Meal Plan

{self._generate_daily_plan_template(start_date, end_date)}

## Weekend Bulk Cooking
[Saturday bulk cooking strategy]
[Sunday bulk cooking strategy]

## Grocery List
### Produce
- Item 1
- Item 2
### Proteins
- Item 1
- Item 2
### Grains
- Item 1
- Item 2
### Dairy
- Item 1
- Item 2
### Pantry
- Item 1
- Item 2
### Frozen
- Item 1
- Item 2

## Nutrition Summary
- Weekly Protein: X g
- Daily Carbs: X g
- Key Nutrients: Item 1, Item 2

Ensure all meals are:
1. Low glycemic index
2. High in plant-based protein
3. Rich in fiber
4. Vegetarian-friendly
5. Suitable for pre-diabetic individuals
"""
        
        try:
            # Updated API call for OpenAI v1.0+
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a vegetarian meal planning expert specializing in pre-diabetic nutrition. Always follow the EXACT template format provided."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2500
            )
            
            self.meal_plan = response.choices[0].message.content
            return self.meal_plan
            
        except Exception as e:
            return f"Error generating meal plan: {str(e)}"
    
    def _generate_daily_plan_template(self, start_date, end_date):
        """Generate daily plan template for the given date range"""
        days = []
        current_date = start_date
        day_num = 1
        
        while current_date <= end_date:
            # Simplified template for easier parsing
            day_template = f"""### Day {day_num} - {current_date.strftime('%A, %B %d')}
**Breakfast (7:00 AM)**
- Meal: [Meal Name]
- Time: 15-20 minutes

**Snack (10:00 AM)**
- Meal: [Snack Name]
- Time: 5 minutes

**Lunch (12:30 PM)**
- Meal: [Meal Name]
- Time: 20-25 minutes

**Snack (3:30 PM)**
- Meal: [Snack Name]
- Time: 5 minutes

**Dinner (6:30 PM)**
- Meal: [Meal Name]
- Time: 25-30 minutes
"""
            days.append(day_template)
            current_date += timedelta(days=1)
            day_num += 1
        
        return "\n".join(days)
    
    def extract_grocery_list(self):
        """Extract grocery list from the meal plan"""
        if not self.meal_plan:
            return "No meal plan generated yet."
        
        # Extract between "## Grocery List" and "## Nutrition Summary"
        lines = self.meal_plan.split('\n')
        grocery_section = False
        grocery_list = []
        
        for line in lines:
            if "## Grocery List" in line:
                grocery_section = True
                continue
            if "## Nutrition Summary" in line:
                grocery_section = False
            if grocery_section and line.strip():
                grocery_list.append(line.strip())
        
        self.grocery_list = '\n'.join(grocery_list)
        return self.grocery_list
    
    def save_to_file(self, filename="meal_plan.txt"):
        """Save the meal plan to a file"""
        if not self.meal_plan:
            return "No meal plan to save."
        
        try:
            with open(filename, 'w') as f:
                f.write(self.meal_plan)
            return f"Meal plan saved to {filename}"
        except Exception as e:
            return f"Error saving file: {str(e)}"
    
    def print_formatted_plan(self):
        """Print the meal plan in a formatted manner"""
        if not self.meal_plan:
            return "No meal plan generated yet."
        
        print("=" * 50)
        print("VEGETARIAN MEAL PLANNER FOR PRE-DIABETIC")
        print("=" * 50)
        print(self.meal_plan)
        print("=" * 50)

def main():
    # Initialize the meal planner
    api_key = os.getenv('OPENAI_API_KEY') or input("Enter your OpenAI API key: ")
    planner = VegetarianMealPlanner(api_key)
    
    print("Vegetarian Meal Planner")
    print("----------------------")
    print("1. This week")
    print("2. Custom date range")
    
    choice = input("Choose option (1 or 2): ")
    
    if choice == "2":
        start_date_str = input("Enter start date (YYYY-MM-DD): ")
        end_date_str = input("Enter end date (YYYY-MM-DD): ")
        
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        except ValueError:
            print("Invalid date format. Using current week instead.")
            start_date, end_date = None, None
    else:
        start_date, end_date = None, None
    
    print(f"Generating meal plan for {start_date.strftime('%B %d, %Y') if start_date else 'this week'} to {end_date.strftime('%B %d, %Y') if end_date else 'end of week'}...")
    
    # Generate meal plan
    plan = planner.generate_meal_plan(start_date, end_date)
    
    if plan.startswith("Error"):
        print(plan)
        return
    
    # Display the meal plan
    planner.print_formatted_plan()
    
    # Extract and display grocery list
    grocery_list = planner.extract_grocery_list()
    print("\n" + "=" * 50)
    print("EXTRACTED GROCERY LIST")
    print("=" * 50)
    print(grocery_list)
    
    # Save to file with dates in filename
    if start_date and end_date:
        filename = f"meal_plan_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.txt"
    else:
        filename = "meal_plan.txt"
    
    save_result = planner.save_to_file(filename)
    print(f"\n{save_result}")
    
    # Optional: Save grocery list separately
    with open(f"grocery_list_{filename}", "w") as f:
        f.write(grocery_list)
    print(f"Grocery list saved to grocery_list_{filename}")

if __name__ == "__main__":
    main()