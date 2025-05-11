# llm_evaluator.py
import json
import statistics
import os
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod

class BaseLLMClient(ABC):
    """Abstract base class for different LLM API clients."""
    
    @abstractmethod
    def generate_completion(self, system_prompt: str, user_prompt: str, json_response: bool = True) -> str:
        """Generate a completion using the LLM API."""
        pass

class OpenAIClient(BaseLLMClient):
    """OpenAI API client."""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        """Initialize OpenAI client with API key and model."""
        self.api_key = api_key
        self.model = model
        self.setup_client()

    def setup_client(self):
        """Set up OpenAI client based on available package version."""
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
            self.use_new_api = True
            # Add this line to check if model supports json_object format
            self.supports_json_response_format = self._check_json_support()
        except ImportError:
            # Fallback to older OpenAI package
            import openai
            openai.api_key = self.api_key
            self.client = None
            self.use_new_api = False
            self.supports_json_response_format = False

    def _check_json_support(self):
        """Check if the model supports json_object response format."""
        # Models known to support json_object response format
        json_supporting_models = [
            "gpt-4-1106-preview", "gpt-4-0125-preview", "gpt-4-turbo-preview", 
            "gpt-4-turbo", "gpt-4-0613", "gpt-3.5-turbo-1106", "gpt-3.5-turbo-0125",
            "gpt-3.5-turbo"
        ]
        
        # Check if model name contains any of the supported model identifiers
        for supported_model in json_supporting_models:
            if supported_model in self.model:
                return True
        
        return False
    
    def generate_completion(self, system_prompt: str, user_prompt: str, json_response: bool = True) -> str:
        """Generate a completion using OpenAI API."""
        try:
            if self.use_new_api and self.client:
                # Only use response_format if the model supports it and json_response is requested
                response_format = {"type": "json_object"} if json_response and self.supports_json_response_format else None
                
                # If json response is needed but not supported, add instruction to the prompt
                modified_system_prompt = system_prompt
                modified_user_prompt = user_prompt
                
                if json_response and not self.supports_json_response_format:
                    modified_system_prompt += "\nYou must respond with valid JSON only. No other text."
                    modified_user_prompt += "\n\nFormat your response as a valid JSON object."
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": modified_system_prompt},
                        {"role": "user", "content": modified_user_prompt}
                    ],
                    response_format=response_format
                )
                return response.choices[0].message.content
            else:
                import openai
                # For old API, add JSON instruction to the prompt if needed
                modified_system_prompt = system_prompt
                modified_user_prompt = user_prompt
                
                if json_response:
                    modified_system_prompt += "\nYou must respond with valid JSON only. No other text."
                    modified_user_prompt += "\n\nFormat your response as a valid JSON object."
                
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": modified_system_prompt},
                        {"role": "user", "content": modified_user_prompt}
                    ]
                )
                return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")

class MistralClient(BaseLLMClient):
    """Mistral AI client."""
    
    def __init__(self, api_key: str, model: str = "mistral-medium"):
        """Initialize Mistral client with API key and model."""
        self.api_key = api_key
        self.model = model
        self.setup_client()
        
    def setup_client(self):
        """Set up Mistral client."""
        try:
            from mistralai.client import MistralClient
            from mistralai.models.chat_completion import ChatMessage
            
            self.client = MistralClient(api_key=self.api_key)
            self.ChatMessage = ChatMessage
        except ImportError:
            raise ImportError("Mistral AI package not installed. Please install with: pip install mistralai")
    
    def generate_completion(self, system_prompt: str, user_prompt: str, json_response: bool = True) -> str:
        """Generate a completion using Mistral API."""
        try:
            messages = [
                self.ChatMessage(role="system", content=system_prompt),
                self.ChatMessage(role="user", content=user_prompt)
            ]
            
            if json_response:
                # Add JSON formatting instruction
                user_prompt_with_format = f"{user_prompt}\n\nFormat your response as a valid JSON object."
                messages[1] = self.ChatMessage(role="user", content=user_prompt_with_format)
            
            response = self.client.chat(
                model=self.model,
                messages=messages
            )
            
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Mistral API error: {str(e)}")

class AnthropicClient(BaseLLMClient):
    """Anthropic Claude client."""
    
    def __init__(self, api_key: str, model: str = "claude-3-opus-20240229"):
        """Initialize Anthropic client with API key and model."""
        self.api_key = api_key
        self.model = model
        self.setup_client()
        
    def setup_client(self):
        """Set up Anthropic client."""
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError("Anthropic package not installed. Please install with: pip install anthropic")
    
    def generate_completion(self, system_prompt: str, user_prompt: str, json_response: bool = True) -> str:
        """Generate a completion using Anthropic API."""
        try:
            if json_response:
                user_prompt = f"{user_prompt}\n\nPlease format your response as a valid JSON object."
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            return message.content[0].text
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")

class GoogleClient(BaseLLMClient):
    """Google Gemini client."""
    
    def __init__(self, api_key: str, model: str = "gemini-1.5-pro"):
        """Initialize Google client with API key and model."""
        self.api_key = api_key
        self.model = model
        self.setup_client()
        
    def setup_client(self):
        """Set up Google client."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.genai = genai
            self.model_client = self.genai.GenerativeModel(self.model)
        except ImportError:
            raise ImportError("Google GenerativeAI package not installed. Please install with: pip install google-generativeai")
    
    def generate_completion(self, system_prompt: str, user_prompt: str, json_response: bool = True) -> str:
        """Generate a completion using Google Gemini API."""
        try:
            combined_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            if json_response:
                combined_prompt = f"{combined_prompt}\n\nFormat your response as a valid JSON object."
            
            response = self.model_client.generate_content(combined_prompt)
            
            return response.text
        except Exception as e:
            raise Exception(f"Google API error: {str(e)}")

class RecipeEvaluator:
    """Flexible recipe evaluator using various LLM providers."""
    
    def __init__(self, llm_client: BaseLLMClient):
        """
        Initialize evaluator with an LLM client.
        
        Args:
            llm_client: Instance of a BaseLLMClient implementation
        """
        self.llm_client = llm_client
    
    @classmethod
    def create(cls, provider: str, api_key: str = None, model: str = None) -> 'RecipeEvaluator':
        """
        Factory method to create an evaluator with the specified LLM provider.
        
        Args:
            provider: LLM provider ('openai', 'mistral', 'anthropic', 'google')
            api_key: API key (will use environment variable if not provided)
            model: Model name (uses provider-specific default if not provided)
            
        Returns:
            Initialized RecipeEvaluator
        """
        provider = provider.lower()
        
        # Get API key from environment variable if not provided
        if not api_key:
            env_var_name = f"{provider.upper()}_API_KEY"
            api_key = os.environ.get(env_var_name)
            if not api_key:
                raise ValueError(f"No API key provided and {env_var_name} environment variable not found")
        
        # Create appropriate client based on provider
        if provider == 'openai':
            client = OpenAIClient(api_key, model or "gpt-4")
        elif provider == 'mistral':
            client = MistralClient(api_key, model or "mistral-medium")
        elif provider == 'anthropic':
            client = AnthropicClient(api_key, model or "claude-3-opus-20240229")
        elif provider == 'google':
            client = GoogleClient(api_key, model or "gemini-1.5-pro")
        else:
            raise ValueError(f"Unsupported provider: {provider}")
        
        return cls(client)
    
    def evaluate_recipe(self, recipe_text: str) -> Dict:
        """
        Evaluate a recipe using the MealMate rubric.
        
        Args:
            recipe_text: The full recipe text including CoT reasoning
            
        Returns:
            Dictionary with evaluation results
        """
        # Extract components from the recipe
        components = self._extract_recipe_components(recipe_text)
        
        # Evaluate each dimension
        nutritional_scores = self._evaluate_nutrition(components)
        variety_scores = self._evaluate_variety(components)
        budget_scores = self._evaluate_budget(components)
        preparation_scores = self._evaluate_preparation(components)
        cot_scores = self._evaluate_cot(components)
        
        # Calculate final score
        final_score, score_breakdown = self._calculate_final_score(
            nutritional_scores, variety_scores, budget_scores, 
            preparation_scores, cot_scores
        )
        
        # Generate feedback
        feedback = self._generate_feedback(score_breakdown)
        
        return {
            "final_score": final_score,
            "score_breakdown": score_breakdown,
            "feedback": feedback,
            "components": components
        }
    
    def _extract_recipe_components(self, recipe_text: str) -> Dict:
        """Extract key components from recipe text."""
        system_prompt = """
        You are a recipe analysis expert. Extract and organize the following components from the recipe:
        
        1. Title
        2. Description/Introduction
        3. Ingredients list (as an array)
        4. Instructions (as an array of steps)
        5. Nutritional information (structured as key-value pairs)
        6. Preparation/cooking times
        7. Chain of Thought reasoning sections (all text marked with THINKING or explaining reasoning)
        8. Any cost or budget information
        9. Serving size information
        10. Equipment needed
        
        Format your response as a valid JSON object.
        """
        
        response = self.llm_client.generate_completion(system_prompt, recipe_text)
        
        try:
            # Parse JSON response
            return json.loads(response)
        except json.JSONDecodeError:
            # If response isn't valid JSON, try to extract it
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except:
                    pass
            
            # Fallback to a simpler structure if JSON parsing fails
            return {
                "title": "Recipe", 
                "ingredients": recipe_text.split("\n\n")[2:3],
                "instructions": recipe_text.split("\n\n")[3:4],
                "reasoning": recipe_text
            }
    
    def _evaluate_nutrition(self, components: Dict) -> Dict:
        """Evaluate nutritional quality dimension."""
        system_prompt = """
        You are a nutritional evaluation expert for pre-diabetic vegetarian diets.
        
        Evaluate the recipe on the following criteria, providing a score from 1-5 and specific evidence for each:
        
        1. Pre-Diabetic Appropriateness (glycemic impact control, GI values, macronutrient balance)
        2. Nutrient Density & Balance (macro/micronutrient profile, nutritional rationale)
        3. Complete Vegetarian Protein (protein content, essential amino acids, complementary sources)
        
        Format your response as valid JSON with this structure:
        {
            "pre_diabetic_appropriateness": {"score": number, "evidence": "string"},
            "nutrient_density_balance": {"score": number, "evidence": "string"},
            "complete_vegetarian_protein": {"score": number, "evidence": "string"}
        }
        
        Be critical and rigorous. Do not inflate scores.
        """
        
        return self._get_dimension_scores(system_prompt, components)
    
    def _evaluate_variety(self, components: Dict) -> Dict:
        """Evaluate variety and creativity dimension."""
        system_prompt = """
        You are a culinary evaluation expert.
        
        Evaluate the recipe on the following criteria, providing a score from 1-5 and specific evidence for each:
        
        1. Ingredient Diversity (number of distinct food groups, variety, specialty ingredients)
        2. Culinary Creativity (innovation, flavor combinations, techniques)
        3. Cultural Representation (authenticity, appropriate adaptations, cultural context)
        
        Format your response as valid JSON with this structure:
        {
            "ingredient_diversity": {"score": number, "evidence": "string"},
            "culinary_creativity": {"score": number, "evidence": "string"},
            "cultural_representation": {"score": number, "evidence": "string"}
        }
        
        Be critical and rigorous. Do not inflate scores.
        """
        
        return self._get_dimension_scores(system_prompt, components)
    
    def _evaluate_budget(self, components: Dict) -> Dict:
        """Evaluate budget and cost dimension."""
        system_prompt = """
        You are a food budget and cost evaluation expert.
        
        Evaluate the recipe on the following criteria, providing a score from 1-5 and specific evidence for each:
        
        1. Ingredient Affordability (estimated cost per serving, accessibility of ingredients)
        2. Pantry Optimization (use of staple ingredients, waste potential, storage tips)
        3. Scaling Flexibility (guidance for different serving sizes, cost adjustments)
        
        Format your response as valid JSON with this structure:
        {
            "ingredient_affordability": {"score": number, "evidence": "string"},
            "pantry_optimization": {"score": number, "evidence": "string"},
            "scaling_flexibility": {"score": number, "evidence": "string"}
        }
        
        Be critical and rigorous. Do not inflate scores.
        """
        
        return self._get_dimension_scores(system_prompt, components)
    
    def _evaluate_preparation(self, components: Dict) -> Dict:
        """Evaluate preparation feasibility dimension."""
        system_prompt = """
        You are a cooking process evaluation expert.
        
        Evaluate the recipe on the following criteria, providing a score from 1-5 and specific evidence for each:
        
        1. Time Efficiency (active preparation time, time-saving strategies, make-ahead options)
        2. Equipment & Technique Accessibility (required tools, explanation of techniques, skill level)
        3. Instruction Clarity (step-by-step guidance, sequencing, timing cues, visual indicators)
        
        Format your response as valid JSON with this structure:
        {
            "time_efficiency": {"score": number, "evidence": "string"},
            "equipment_technique_accessibility": {"score": number, "evidence": "string"},
            "instruction_clarity": {"score": number, "evidence": "string"}
        }
        
        Be critical and rigorous. Do not inflate scores.
        """
        
        return self._get_dimension_scores(system_prompt, components)
    
    def _evaluate_cot(self, components: Dict) -> Dict:
        """Evaluate Chain of Thought quality dimension."""
        system_prompt = """
        You are an expert in evaluating Chain of Thought reasoning in recipe development.
        
        Evaluate the recipe on the following criteria, providing a score from 1-5 and specific evidence for each:
        
        1. Reasoning Transparency (clear explanations for ingredient choices and cooking methods)
        2. Educational Value (evidence-based explanations of nutritional concepts and cooking science)
        
        Format your response as valid JSON with this structure:
        {
            "reasoning_transparency": {"score": number, "evidence": "string"},
            "educational_value": {"score": number, "evidence": "string"}
        }
        
        Be critical and rigorous. Do not inflate scores.
        """
        
        return self._get_dimension_scores(system_prompt, components)
    
    def _get_dimension_scores(self, system_prompt: str, components: Dict) -> Dict:
        """Get scores for a dimension using LLM client."""
        component_json = json.dumps(components)
        response = self.llm_client.generate_completion(system_prompt, component_json)
        
        try:
            # Parse JSON response
            return json.loads(response)
        except json.JSONDecodeError:
            # If response isn't valid JSON, try to extract it
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except:
                    pass
            
            # If still fails, try to fix the JSON
            fix_prompt = f"The following text should be valid JSON but isn't. Please fix it and return ONLY valid JSON: {response}"
            fixed_response = self.llm_client.generate_completion(
                "You correct invalid JSON. Return ONLY fixed JSON.",
                fix_prompt
            )
            
            try:
                return json.loads(fixed_response)
            except:
                # Last resort fallback
                return {"error": "Failed to parse response", "raw_response": response[:100] + "..."}
    
    def _calculate_final_score(self, nutritional_scores: Dict, variety_scores: Dict, 
                              budget_scores: Dict, preparation_scores: Dict, 
                              cot_scores: Dict) -> tuple:
        """Calculate final score and breakdown based on dimension scores."""
        # Handle potential errors in scores
        def safe_get_score(scores_dict, key):
            try:
                return scores_dict[key]["score"]
            except (KeyError, TypeError):
                return 3  # Default to middle score if missing
        
        # Calculate dimension averages
        nutritional_avg = statistics.mean([
            safe_get_score(nutritional_scores, "pre_diabetic_appropriateness"),
            safe_get_score(nutritional_scores, "nutrient_density_balance"),
            safe_get_score(nutritional_scores, "complete_vegetarian_protein")
        ])
        
        variety_avg = statistics.mean([
            safe_get_score(variety_scores, "ingredient_diversity"),
            safe_get_score(variety_scores, "culinary_creativity"),
            safe_get_score(variety_scores, "cultural_representation")
        ])
        
        budget_avg = statistics.mean([
            safe_get_score(budget_scores, "ingredient_affordability"),
            safe_get_score(budget_scores, "pantry_optimization"),
            safe_get_score(budget_scores, "scaling_flexibility")
        ])
        
        preparation_avg = statistics.mean([
            safe_get_score(preparation_scores, "time_efficiency"),
            safe_get_score(preparation_scores, "equipment_technique_accessibility"),
            safe_get_score(preparation_scores, "instruction_clarity")
        ])
        
        cot_avg = statistics.mean([
            safe_get_score(cot_scores, "reasoning_transparency"),
            safe_get_score(cot_scores, "educational_value")
        ])
        
        # Build score breakdown
        score_breakdown = {
            "nutritional_quality": {
                "scores": nutritional_scores,
                "average": nutritional_avg,
                "weight": 0.30
            },
            "variety_creativity": {
                "scores": variety_scores,
                "average": variety_avg,
                "weight": 0.25
            },
            "budget_cost": {
                "scores": budget_scores,
                "average": budget_avg,
                "weight": 0.20
            },
            "preparation_feasibility": {
                "scores": preparation_scores,
                "average": preparation_avg,
                "weight": 0.25
            },
            "cot_quality": {
                "scores": cot_scores,
                "average": cot_avg,
                "weight": 0.10
            }
        }
        
        # Calculate base score
        base_score = (
            nutritional_avg * 0.30 +
            variety_avg * 0.25 +
            budget_avg * 0.20 +
            preparation_avg * 0.25
        )
        
        # Calculate CoT bonus
        cot_bonus = cot_avg * 0.10
        
        # Calculate final score
        final_score = base_score + cot_bonus
        
        score_breakdown["base_score"] = base_score
        score_breakdown["cot_bonus"] = cot_bonus
        score_breakdown["final_score"] = final_score
        
        return final_score, score_breakdown
    
    def _generate_feedback(self, score_breakdown: Dict) -> Dict:
        """Generate feedback based on score breakdown."""
        # Identify strengths and weaknesses
        all_criteria = []
        for dimension, data in score_breakdown.items():
            if dimension in ["base_score", "cot_bonus", "final_score"]:
                continue
            
            for criterion, details in data["scores"].items():
                if isinstance(details, dict) and "score" in details and "evidence" in details:
                    all_criteria.append((criterion, details["score"], details["evidence"]))
        
        # Sort by score (descending)
        all_criteria.sort(key=lambda x: x[1], reverse=True)
        
        # Top 3 strengths
        strengths = [{"criterion": criterion, "evidence": evidence} 
                     for criterion, score, evidence in all_criteria[:3]]
        
        # Bottom 3 areas for improvement
        improvements = [{"criterion": criterion, "evidence": evidence} 
                        for criterion, score, evidence in all_criteria[-3:]]
        
        # Interpret final score
        score = score_breakdown["final_score"]
        if score >= 4.5:
            interpretation = "Outstanding - Exceptional recipe that excels in nearly all areas"
        elif score >= 4.0:
            interpretation = "Excellent - High-quality recipe with minor room for improvement"
        elif score >= 3.5:
            interpretation = "Very Good - Strong recipe with several notable strengths"
        elif score >= 3.0:
            interpretation = "Good - Solid recipe meeting all basic requirements"
        elif score >= 2.5:
            interpretation = "Fair - Acceptable recipe with notable weaknesses"
        elif score >= 2.0:
            interpretation = "Needs Improvement - Significant issues in multiple areas"
        else:
            interpretation = "Unsatisfactory - Major issues requiring complete revision"
        
        return {
            "strengths": strengths,
            "areas_for_improvement": improvements,
            "interpretation": interpretation
        }