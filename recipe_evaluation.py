# recipe_evaluation.py
import os
import json
from llm_evaluator import RecipeEvaluator, OpenAIClient, MistralClient, AnthropicClient, GoogleClient
import streamlit as st

class RecipeEvaluationManager:
    """Manages the evaluation of recipes using the RecipeEvaluator."""
    
    def __init__(self, api_key, provider="openai", model=None):
        """Initialize the evaluation manager with API key and provider."""
        self.api_key = api_key
        self.provider = provider.lower()
        
        # Set default model based on provider if none specified
        if model is None:
            if provider == "openai":
                model = "gpt-4-turbo"  # Use a model that supports JSON response format
            elif provider == "anthropic":
                model = "claude-3-opus-20240229"
            elif provider == "mistral":
                model = "mistral-medium"
            elif provider == "google":
                model = "gemini-1.5-pro"
        
        self.model = model
        self.evaluator = None
        self.setup_evaluator()
    
    
    def setup_evaluator(self):
        """Set up the appropriate evaluator based on the provider."""
        try:
            self.evaluator = RecipeEvaluator.create(
                provider=self.provider,
                api_key=self.api_key,
                model=self.model
            )
        except Exception as e:
            st.error(f"Error setting up evaluator: {str(e)}")
            self.evaluator = None
    
    def evaluate_recipe(self, recipe_text):
        """
        Evaluate a recipe using the MealMate rubric.
        """
        if not self.evaluator:
            return {"error": "Evaluator not initialized. Please check your API key."}
        
        try:
            evaluation_result = self.evaluator.evaluate_recipe(recipe_text)
            return evaluation_result
        except Exception as e:
            error_message = str(e)
            
            if "response_format" in error_message:
                # Handle response_format compatibility error
                return {
                    "error": f"Model compatibility issue: The selected model doesn't support structured JSON output. Try a different model like gpt-4-turbo.",
                    "details": error_message
                }
            else:
                # General error handling
                return {
                    "error": f"Evaluation error: {error_message}"
                }
    def get_score_color(self, score):
        """Return a color based on the score value."""
        if score >= 4.5:
            return "#2e7d32"  # Dark green
        elif score >= 4.0:
            return "#4caf50"  # Green
        elif score >= 3.5:
            return "#8bc34a"  # Light green
        elif score >= 3.0:
            return "#cddc39"  # Lime
        elif score >= 2.5:
            return "#ffc107"  # Amber
        elif score >= 2.0:
            return "#ff9800"  # Orange
        else:
            return "#f44336"  # Red

def render_evaluation_ui(evaluation_result, show_details=True):
    """
    Render evaluation results in the Streamlit UI.
    
    Args:
        evaluation_result: Dictionary with evaluation data
        show_details: Whether to show detailed breakdowns
    """
    if not evaluation_result or "error" in evaluation_result:
        st.error(f"Evaluation failed: {evaluation_result.get('error', 'Unknown error')}")
        return
    
    score_breakdown = evaluation_result.get("score_breakdown", {})
    feedback = evaluation_result.get("feedback", {})
    
    # Display final score with interpretation
    final_score = score_breakdown.get("final_score", 0)
    interpretation = feedback.get("interpretation", "No interpretation available")
    
    # Create a score gauge visualization
    st.markdown(f"""
    <div style="text-align: center;">
        <div style="display: inline-block; width: 150px; height: 150px; border-radius: 50%; background: conic-gradient(
            {get_gauge_gradient(final_score)}
        ); position: relative;">
            <div style="position: absolute; top: 15px; left: 15px; right: 15px; bottom: 15px; background: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-direction: column;">
                <span style="font-size: 36px; font-weight: bold; color: {get_score_color(final_score)};">{final_score:.1f}</span>
                <span style="font-size: 12px;">out of 5.0</span>
            </div>
        </div>
        <p style="margin-top: 10px; font-weight: bold;">{interpretation}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Display strengths and areas for improvement
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 💪 Strengths")
        strengths = feedback.get("strengths", [])
        if strengths:
            for strength in strengths:
                criterion = strength.get("criterion", "")
                evidence = strength.get("evidence", "")
                st.markdown(f"**{format_criterion_name(criterion)}**")
                st.markdown(f"{evidence}")
                st.markdown("---")
        else:
            st.info("No specific strengths identified")
    
    with col2:
        st.markdown("### 🔍 Areas for Improvement")
        improvements = feedback.get("areas_for_improvement", [])
        if improvements:
            for improvement in improvements:
                criterion = improvement.get("criterion", "")
                evidence = improvement.get("evidence", "")
                st.markdown(f"**{format_criterion_name(criterion)}**")
                st.markdown(f"{evidence}")
                st.markdown("---")
        else:
            st.info("No specific improvements identified")
    
    # Show detailed score breakdown if requested
    if show_details:
        with st.expander("📊 Detailed Score Breakdown", expanded=False):
            # Create a table for dimension scores
            st.markdown("#### Dimension Scores")
            
            dimension_data = []
            for dimension, data in score_breakdown.items():
                if dimension not in ["base_score", "cot_bonus", "final_score"]:
                    dimension_data.append({
                        "Dimension": format_dimension_name(dimension),
                        "Average": f"{data.get('average', 0):.2f}",
                        "Weight": f"{data.get('weight', 0)*100:.0f}%"
                    })
            
            if dimension_data:
                st.dataframe(dimension_data, use_container_width=True)
            
            # Create detailed criterion scores
            st.markdown("#### Criterion Scores")
            
            for dimension, data in score_breakdown.items():
                if dimension not in ["base_score", "cot_bonus", "final_score"]:
                    st.markdown(f"**{format_dimension_name(dimension)}**")
                    
                    criterion_data = []
                    scores = data.get("scores", {})
                    
                    for criterion, details in scores.items():
                        if isinstance(details, dict) and "score" in details:
                            criterion_data.append({
                                "Criterion": format_criterion_name(criterion),
                                "Score": details.get("score", 0),
                                "Evidence": details.get("evidence", "")[:100] + "..." if len(details.get("evidence", "")) > 100 else details.get("evidence", "")
                            })
                    
                    if criterion_data:
                        st.dataframe(criterion_data, use_container_width=True)

def format_dimension_name(name):
    """Format dimension name for display."""
    name = name.replace('_', ' ').title()
    return name

def format_criterion_name(name):
    """Format criterion name for display."""
    name = name.replace('_', ' ').title()
    return name

def get_score_color(score):
    """Return a color based on the score value."""
    if score >= 4.5:
        return "#2e7d32"  # Dark green
    elif score >= 4.0:
        return "#4caf50"  # Green
    elif score >= 3.5:
        return "#8bc34a"  # Light green
    elif score >= 3.0:
        return "#cddc39"  # Lime
    elif score >= 2.5:
        return "#ffc107"  # Amber
    elif score >= 2.0:
        return "#ff9800"  # Orange
    else:
        return "#f44336"  # Red

def get_gauge_gradient(score):
    """Generate a conic gradient for the score gauge."""
    percentage = min(max((score / 5.0) * 100, 0), 100)
    
    if percentage >= 90:  # 4.5+
        return f"#2e7d32 0%, #2e7d32 {percentage}%, #e0e0e0 {percentage}%, #e0e0e0 100%"
    elif percentage >= 80:  # 4.0+
        return f"#4caf50 0%, #4caf50 {percentage}%, #e0e0e0 {percentage}%, #e0e0e0 100%"
    elif percentage >= 70:  # 3.5+
        return f"#8bc34a 0%, #8bc34a {percentage}%, #e0e0e0 {percentage}%, #e0e0e0 100%"
    elif percentage >= 60:  # 3.0+
        return f"#cddc39 0%, #cddc39 {percentage}%, #e0e0e0 {percentage}%, #e0e0e0 100%"
    elif percentage >= 50:  # 2.5+
        return f"#ffc107 0%, #ffc107 {percentage}%, #e0e0e0 {percentage}%, #e0e0e0 100%"
    elif percentage >= 40:  # 2.0+
        return f"#ff9800 0%, #ff9800 {percentage}%, #e0e0e0 {percentage}%, #e0e0e0 100%"
    else:
        return f"#f44336 0%, #f44336 {percentage}%, #e0e0e0 {percentage}%, #e0e0e0 100%"