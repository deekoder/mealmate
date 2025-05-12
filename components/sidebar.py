# components/sidebar.py
import streamlit as st
from datetime import datetime, timedelta
from VegetarianMealPlanner import VegetarianMealPlanner
from recipe_agent import RecipeAgent
from recipe_evaluation import RecipeEvaluationManager
import traceback

def render_sidebar():
    """Render sidebar with configuration options and return the collected settings"""
    with st.sidebar:
        st.header("Configuration")
        
        # API Key handling
        api_key = _handle_api_key()
        
        # Date selection
        date_config = _handle_date_selection()
        
        # Advanced options
        app_config = _handle_advanced_options()
        
        # Evaluation settings
        if api_key:
            _handle_evaluation_settings(api_key, app_config)
        
        return api_key, date_config, app_config

def _handle_api_key():
    """Handle API key input and initialization"""
    # Get API key from secrets or user input
    if 'openai_api_key' in st.secrets:
        api_key = st.secrets.openai_api_key
        st.success("API Key loaded from secrets!")
    else:
        # Fallback to user input if not in secrets
        api_key = st.text_input("OpenAI API Key", type="password")
        if api_key:
            st.info("Consider adding your API key to `.streamlit/secrets.toml` for persistence")
        else:
            st.markdown("[Get API Key](https://platform.openai.com/api-keys)")
    
    # Initialize recipe agent when API key is provided
    if api_key and st.session_state.recipe_agent is None:
        st.session_state.recipe_agent = RecipeAgent(api_key)
    
    return api_key

def _handle_date_selection():
    """Handle date selection options"""
    st.header("Date Selection")
    date_option = st.radio(
        "Choose date option:",
        ["This Week", "Custom Week", "Date Range"]
    )
    
    if date_option == "This Week":
        today = datetime.now()
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
    elif date_option == "Custom Week":
        selected_date = st.date_input("Select any date in the week", datetime.now())
        if selected_date.weekday() == 0:  # If it's Monday
            start_date = selected_date
        else:
            start_date = selected_date - timedelta(days=selected_date.weekday())
        end_date = start_date + timedelta(days=6)
    else:  # Date Range
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", datetime.now())
        with col2:
            end_date = st.date_input("End Date", datetime.now() + timedelta(days=6))
    
    st.markdown(f"**Selected Week:** {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}")
    
    return {
        "start_date": start_date,
        "end_date": end_date
    }

def _handle_advanced_options():
    """Handle advanced app options"""
    st.header("Advanced Options")
    show_reasoning = st.checkbox("Show nutritional reasoning", value=st.session_state.show_reasoning)
    st.session_state.show_reasoning = show_reasoning
    
    # Add a meal complexity option that will be passed to the meal planner
    meal_complexity = st.select_slider(
        "Meal Complexity",
        options=["Simple", "Moderate", "Complex"],
        value="Moderate"
    )
    
    # Add evaluation toggle
    enable_auto_evaluation = st.checkbox("Auto-evaluate recipes", value=True)
    
    # Generate Meal Plan button
    generate_plan = False
    if st.button("Generate Meal Plan", type="primary"):
        generate_plan = True
    
    return {
        "show_reasoning": show_reasoning,
        "meal_complexity": meal_complexity,
        "enable_auto_evaluation": enable_auto_evaluation,
        "generate_plan": generate_plan
    }

def _handle_evaluation_settings(api_key, app_config):
    """Handle recipe evaluation settings"""
    st.header("Evaluation Settings")
    eval_provider = st.selectbox(
        "Evaluation Provider",
        options=["openai", "anthropic", "mistral", "google"],
        index=0
    )
    
    # Add model selection dropdown based on provider
    selected_model = None
    if eval_provider == "openai":
        selected_model = st.selectbox(
            "OpenAI Model",
            options=["gpt-4-turbo", "gpt-3.5-turbo", "gpt-4", "gpt-4-0613", "gpt-3.5-turbo-0613"],
            index=0,  # Default to gpt-4-turbo which supports response_format
            help="Select a model that supports JSON response format for best results"
        )
    elif eval_provider == "anthropic":
        selected_model = st.selectbox(
            "Anthropic Model",
            options=["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
            index=0
        )
    elif eval_provider == "mistral":
        selected_model = st.selectbox(
            "Mistral Model",
            options=["mistral-medium", "mistral-large", "mistral-small"],
            index=0
        )
    elif eval_provider == "google":
        selected_model = st.selectbox(
            "Google Model",
            options=["gemini-1.5-pro", "gemini-1.0-pro"],
            index=0
        )
    
    # Initialize or update evaluation manager with selected provider and model
    try:
        if (st.session_state.evaluation_manager is None or 
            getattr(st.session_state.evaluation_manager, 'provider', None) != eval_provider or
            getattr(st.session_state.evaluation_manager, 'model', None) != selected_model):
            st.session_state.evaluation_manager = RecipeEvaluationManager(
                api_key, 
                provider=eval_provider,
                model=selected_model
            )
    except Exception as e:
        st.error(f"Error initializing evaluation manager: {str(e)}")
    
    # If generate plan button is clicked, proceed with meal plan generation
    if app_config["generate_plan"]:
        _generate_meal_plan(api_key, app_config)

def _generate_meal_plan(api_key, app_config):
    """Generate meal plan based on configuration"""
    with st.spinner("Generating your meal plan... This may take a moment."):
        try:
            # Create planner with custom dates
            planner = VegetarianMealPlanner(api_key)
            
            # Use the CoT version of the meal planner if reasoning is enabled
            if app_config["show_reasoning"]:
                try:
                    meal_plan_data = planner.generate_meal_plan_with_cot(
                        start_date=st.session_state.sidebar_date_range["start_date"], 
                        end_date=st.session_state.sidebar_date_range["end_date"],
                        complexity=app_config["meal_complexity"]
                    )
                    
                    # Store the raw meal plan data for reasoning display
                    st.session_state.meal_plan_data = meal_plan_data
                    
                    # The meal plan text is already set by the CoT method
                    meal_plan = planner.meal_plan
                    
                except Exception as e:
                    st.error(f"Error in CoT generation: {str(e)}")
                    st.error(traceback.format_exc())
                    # Fallback to regular meal plan
                    meal_plan = planner.generate_meal_plan(
                        start_date=st.session_state.sidebar_date_range["start_date"], 
                        end_date=st.session_state.sidebar_date_range["end_date"]
                    )
                    st.session_state.meal_plan_data = None
            else:
                # Use the original method if reasoning is not needed
                meal_plan = planner.generate_meal_plan(
                    start_date=st.session_state.sidebar_date_range["start_date"], 
                    end_date=st.session_state.sidebar_date_range["end_date"]
                )
                st.session_state.meal_plan_data = None
            
            grocery_list = planner.extract_grocery_list()
            
            # Store meal plan in session state
            st.session_state.meal_plan = meal_plan
            st.session_state.grocery_list = grocery_list
            
            # Store date range in session state for other components
            st.session_state.sidebar_date_range = {
                "start_date": st.session_state.sidebar_date_range["start_date"],
                "end_date": st.session_state.sidebar_date_range["end_date"]
            }
            
            # Display success message
            st.success("Meal plan generated successfully!")
            
        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.error(f"Error details: {type(e).__name__}")
            st.error(traceback.format_exc())