# recipe_agent.py
import json
from datetime import datetime

class RecipeAgent:
    def __init__(self, api_key):
        """Initialize the Recipe Agent with OpenAI API key"""
        self.api_key = api_key
        
        # Handle OpenAI import and client initialization
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
            self.use_new_api = True
        except ImportError:
            # OpenAI package not installed or old version
            try:
                import openai
                openai.api_key = api_key
                self.client = None
                self.use_new_api = False
            except ImportError:
                raise ImportError("OpenAI package not installed. Please install with: pip install openai")
        except Exception as e:
            # Error initializing OpenAI client
            print(f"Error initializing OpenAI: {e}")
            import openai
            openai.api_key = api_key
            self.client = None
            self.use_new_api = False
        
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_recipe_variations",
                    "description": "Search for variations of a meal to provide alternatives",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "meal_name": {"type": "string", "description": "Name of the meal to search variations for"},
                            "dietary_preferences": {"type": "string", "description": "Dietary preferences (vegetarian, pre-diabetic)"}
                        },
                        "required": ["meal_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "check_nutritional_values",
                    "description": "Analyze nutritional content of ingredients",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ingredients": {"type": "array", "items": {"type": "string"}, "description": "List of ingredients"},
                            "servings": {"type": "integer", "description": "Number of servings"}
                        },
                        "required": ["ingredients"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "suggest_substitutions",
                    "description": "Suggest ingredient substitutions for dietary restrictions",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "original_ingredient": {"type": "string", "description": "Original ingredient"},
                            "restriction": {"type": "string", "description": "Dietary restriction (e.g., pre-diabetic)"}
                        },
                        "required": ["original_ingredient", "restriction"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_shopping_list",
                    "description": "Create a shopping list from recipe ingredients",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "recipe": {"type": "string", "description": "Complete recipe text"},
                            "people": {"type": "integer", "description": "Number of people to shop for"}
                        },
                        "required": ["recipe"]
                    }
                }
            }
        ]
        self.conversation_history = []
    
    def search_recipe_variations(self, meal_name, dietary_preferences="vegetarian, pre-diabetic"):
        """Tool: Search for recipe variations"""
        variations = [
            f"{meal_name} with chickpeas",
            f"Spiced {meal_name}",
            f"{meal_name} with tofu",
            f"Low-glycemic {meal_name}",
            f"High-protein {meal_name}"
        ]
        return {"variations": variations}
    
    def check_nutritional_values(self, ingredients, servings=4):
        """Tool: Check nutritional values of ingredients"""
        # This is a simplified version - in reality, you'd integrate with a nutrition API
        nutritional_info = {
            "total_carbs": 45,
            "total_protein": 15,
            "total_fiber": 8,
            "glycemic_load": "low",
            "per_serving": {
                "carbs": 45/servings,
                "protein": 15/servings,
                "fiber": 8/servings
            }
        }
        return nutritional_info
    
    def suggest_substitutions(self, original_ingredient, restriction="pre-diabetic"):
        """Tool: Suggest ingredient substitutions"""
        substitutions = {
            "white rice": "brown rice or quinoa",
            "sugar": "stevia or monk fruit",
            "white bread": "whole grain bread",
            "regular pasta": "whole wheat pasta or zucchini noodles",
            "potato": "sweet potato or cauliflower"
        }
        
        # Find the best substitution
        for key, value in substitutions.items():
            if key.lower() in original_ingredient.lower():
                return {"substitution": value, "reason": f"Better for {restriction} diet"}
        
        return {"substitution": original_ingredient, "reason": "No substitution needed"}
    
    def generate_shopping_list(self, recipe, people=4):
        """Tool: Generate shopping list from recipe"""
        # Extract ingredients from recipe (simplified)
        import re
        ingredients = re.findall(r'- (.*?)\n', recipe)
        
        shopping_list = []
        for ingredient in ingredients:
            # Scale quantity if needed
            if any(char.isdigit() for char in ingredient):
                try:
                    match = re.search(r'\d+', ingredient)
                    if match:
                        scaled_ingredient = ingredient.replace(
                            match.group(),
                            str(int(float(match.group()) * people / 4))
                        )
                        shopping_list.append(scaled_ingredient)
                    else:
                        shopping_list.append(ingredient)
                except:
                    shopping_list.append(ingredient)
            else:
                shopping_list.append(ingredient)
        
        return {"shopping_list": shopping_list, "servings": people}
    
    def generate_recipe(self, meal_name, dietary_requirements="vegetarian, pre-diabetic"):
        """Main agent function that orchestrates recipe generation"""
        # Initial system message for the agent
        system_message = """You are an intelligent recipe generation agent. You have access to tools to:
        1. Search for recipe variations
        2. Check nutritional values
        3. Suggest ingredient substitutions
        4. Generate shopping lists
        
        Use these tools to create the best possible recipe for the user's needs.
        Always consider pre-diabetic dietary requirements and vegetarian preferences.
        Think step by step and use tools when needed."""
        
        # Start the conversation
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"I need a recipe for {meal_name} that's suitable for a vegetarian pre-diabetic diet."}
        ]
        
        try:
            if self.use_new_api and self.client:
                # First interaction - decide what tools to use
                response = self.client.chat.completions.create(
                    model="gpt-4",
                    messages=messages,
                    tools=self.tools,
                    tool_choice="auto"
                )
                
                # Process tool calls
                while hasattr(response.choices[0].message, 'tool_calls') and response.choices[0].message.tool_calls:
                    # Execute tools
                    tool_calls = response.choices[0].message.tool_calls
                    messages.append(response.choices[0].message)
                    
                    for tool_call in tool_calls:
                        function_name = tool_call.function.name
                        function_args = json.loads(tool_call.function.arguments)
                        
                        # Execute the tool
                        if hasattr(self, function_name):
                            tool_result = getattr(self, function_name)(**function_args)
                        else:
                            tool_result = {"error": f"Tool {function_name} not implemented"}
                        
                        # Add tool result to conversation
                        messages.append({
                            "role": "tool",
                            "content": json.dumps(tool_result),
                            "tool_call_id": tool_call.id
                        })
                    
                    # Get next response
                    response = self.client.chat.completions.create(
                        model="gpt-4",
                        messages=messages,
                        tools=self.tools,
                        tool_choice="auto"
                    )
                
                # Final recipe generation
                final_recipe = response.choices[0].message.content
                
                # Store conversation history
                tool_calls_used = []
                for msg in messages:
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        for tc in msg.tool_calls:
                            tool_calls_used.append(tc.function.name)
                
                self.conversation_history.append({
                    "meal_name": meal_name,
                    "timestamp": datetime.now(),
                    "recipe": final_recipe,
                    "tools_used": tool_calls_used
                })
                
                return final_recipe
            else:
                # Fallback to simpler recipe generation without tools for old API
                prompt = f"""Generate a detailed vegetarian recipe for: {meal_name}

Requirements:
- Vegetarian (no meat, fish, poultry)
- Suitable for pre-diabetic diet (low glycemic index, controlled carbs)
- Include prep time, cook time, and servings
- List ingredients with measurements
- Provide step-by-step instructions
- Include nutrition information

Format the response as a complete recipe."""
                
                try:
                    import openai
                    response = openai.ChatCompletion.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": "You are a vegetarian cooking expert specializing in pre-diabetic nutrition."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7,
                        max_tokens=800
                    )
                    return response.choices[0].message.content
                except Exception as e:
                    return f"Error generating recipe (old API): {str(e)}"
                
        except Exception as e:
            # Fallback to simple error message
            return f"""Error generating recipe: {str(e)}

Basic Recipe for {meal_name}:
- This is a placeholder recipe due to an error.
- Try refreshing to generate a proper recipe.
- Make sure you have a valid OpenAI API key."""