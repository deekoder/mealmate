# recipe_agent.py with CoT improvements
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
    
    def get_cot_system_prompt(self):
        """Generate the Chain of Thought system prompt for recipe creation"""
        return """You are an intelligent recipe generation agent specializing in vegetarian, pre-diabetic friendly recipes. 
        
        ALWAYS use Chain of Thought (CoT) reasoning to explain your thinking process transparently. This means you should:
        
        1. ANALYZE REQUIREMENTS: First, analyze what the recipe needs to accomplish and what dietary constraints must be considered.
           - Break down the meal type and its typical ingredients
           - Identify potential glycemic index concerns in traditional versions
           - Consider protein, fiber, and micronutrient needs for a balanced vegetarian meal
        
        2. PLAN RECIPE APPROACH: Think step-by-step about your approach before diving into details.
           - What cooking methods would best preserve nutrients?
           - What ingredient combinations will create complete proteins?
           - How can you ensure the meal is satisfying while maintaining low glycemic load?
           - What flavor profile will make this dish appealing?
        
        3. TOOL UTILIZATION: Before using any tool, explain WHY you're using it and what you hope to learn.
           Format your tool reasoning like this:
           
           THINKING: [Explain why you need this tool and what you hope to learn]
           TOOL: [Name of the tool you're using]
           
           After receiving tool results, analyze them with:
           
           ANALYSIS: [Your interpretation of the results and how they inform your next steps]
        
        4. INGREDIENT DECISIONS: For key ingredients, explain:
           - Why you're choosing them (nutritional benefits, glycemic impact, flavor)
           - How they contribute to a pre-diabetic friendly profile
           - Their role in creating a balanced vegetarian meal
        
        5. FINAL RECIPE FORMAT: Present your final recipe with clear sections:
           - Brief introduction explaining the recipe's benefits for pre-diabetic vegetarians
           - Prep time, cook time, total time, and servings
           - Ingredients with precise measurements
           - Detailed, numbered instructions
           - Nutritional information per serving
           - Tips for variations or substitutions
           - Storage recommendations
        
        Your goal is not just to create a recipe, but to EDUCATE the user on WHY this recipe works for their dietary needs. Make your reasoning clear and accessible, using specific metrics (glycemic index, fiber content, etc.) when relevant.
        
        Use these tools strategically:
        1. search_recipe_variations - To explore different approaches to the meal
        2. check_nutritional_values - To confirm the nutritional profile aligns with pre-diabetic needs
        3. suggest_substitutions - To find better alternatives for higher glycemic ingredients
        4. generate_shopping_list - To create an organized list of ingredients
        
        Remember to share your reasoning process throughout the entire interaction."""
    
    def generate_recipe(self, meal_name, dietary_requirements="vegetarian, pre-diabetic"):
        """Main agent function that orchestrates recipe generation with Chain of Thought reasoning"""
        # Get the enhanced CoT system message
        system_message = self.get_cot_system_prompt()
        
        # Start the conversation with a clear request for CoT reasoning
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"Please create a recipe for {meal_name} that's suitable for a vegetarian pre-diabetic diet. Use Chain of Thought reasoning to explain your process and thinking for each step of recipe development."}
        ]
        
        try:
            if self.use_new_api and self.client:
                # First interaction - decide what tools to use with CoT reasoning
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
                
                # Final recipe generation with explicit request for CoT summary
                messages.append(response.choices[0].message)
                
                # Add a final prompt to ensure CoT reasoning is included
                messages.append({
                    "role": "user", 
                    "content": "Please provide the final recipe with your complete Chain of Thought reasoning. Make sure to summarize your thought process about the ingredient choices, cooking methods, and how this recipe specifically addresses pre-diabetic dietary needs while remaining flavorful and nutritionally complete for vegetarians."
                })
                
                # Get final response with CoT reasoning
                final_response = self.client.chat.completions.create(
                    model="gpt-4",
                    messages=messages
                )
                
                final_recipe = final_response.choices[0].message.content
                
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
                # But still using CoT reasoning
                prompt = f"""Generate a detailed vegetarian recipe for: {meal_name}

Please use Chain of Thought reasoning throughout your response:

1. First, analyze what makes a good pre-diabetic, vegetarian {meal_name}
2. Explain your thinking about key ingredient choices and their glycemic impact
3. Discuss your reasoning for cooking methods and how they affect nutrition
4. Explain why this recipe is suitable for pre-diabetic needs

Requirements:
- Vegetarian (no meat, fish, poultry)
- Suitable for pre-diabetic diet (low glycemic index, controlled carbs)
- Include prep time, cook time, and servings
- List ingredients with measurements
- Provide step-by-step instructions
- Include nutrition information
- Explain the glycemic impact of key ingredients

Format the response as a complete recipe with your reasoning clearly shown."""
                
                try:
                    import openai
                    response = openai.ChatCompletion.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": self.get_cot_system_prompt()},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7,
                        max_tokens=1200  # Increased to accommodate CoT reasoning
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