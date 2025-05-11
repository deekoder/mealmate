import streamlit as st
from VegetarianMealPlanner import VegetarianMealPlanner
from recipe_agent import RecipeAgent
from utils import parse_meal_plan_to_dataframe, parse_grocery_list_to_dict, create_pivot_table, load_css
from datetime import datetime, timedelta
import json
import traceback
from recipe_evaluation import RecipeEvaluationManager, render_evaluation_ui

# Helper function to create consistent unique IDs regardless of data source
def generate_unique_id(row):
    """Helper function to create consistent unique IDs regardless of data source"""
    # Standardize the input values
    day = str(row['Day']).strip()
    meal = str(row['Meal']).strip().split('(')[0].strip()  # Remove any parenthetical content
    meal_name = str(row['Meal Name']).strip()
    
    # Create a unique ID that will be consistent between different data sources
    unique_id = f"{day}_{meal}_{meal_name[:20]}".replace(' ', '_')
    
    return unique_id

st.set_page_config(
    page_title="Vegetarian Meal Planner",
    page_icon="🥗",
    layout="wide"
)

# Load custom CSS
load_css()

# Add session state for recipes, reasoning, and evaluations
if 'recipes' not in st.session_state:
    st.session_state.recipes = {}
if 'recipe_agent' not in st.session_state:
    st.session_state.recipe_agent = None
if 'show_reasoning' not in st.session_state:
    st.session_state.show_reasoning = False
if 'meal_plan_data' not in st.session_state:
    st.session_state.meal_plan_data = None
if 'evaluations' not in st.session_state:
    st.session_state.evaluations = {}
if 'evaluation_manager' not in st.session_state:
    st.session_state.evaluation_manager = None

st.title("🥗 Vegetarian Meal Planner for Pre-Diabetics")
st.markdown("""
Generate a weekly meal plan optimized for vegetarian pre-diabetic diet.
This app creates personalized meal plans with bulk cooking strategies and grocery lists.
""")

# Sidebar for API key and date selection
with st.sidebar:
    st.header("Configuration")
    
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
    
    # Add a toggle for showing CoT reasoning
    st.header("Advanced Options")
    st.session_state.show_reasoning = st.checkbox("Show nutritional reasoning", value=st.session_state.show_reasoning)
    
    # Add a meal complexity option that will be passed to the meal planner
    meal_complexity = st.select_slider(
        "Meal Complexity",
        options=["Simple", "Moderate", "Complex"],
        value="Moderate"
    )
    
    # Add evaluation settings
    st.header("Evaluation Settings")
    eval_provider = st.selectbox(
        "Evaluation Provider",
        options=["openai", "anthropic", "mistral", "google"],
        index=0
    )
    
    # Add model selection dropdown based on provider
    if eval_provider == "openai":
        openai_model = st.selectbox(
            "OpenAI Model",
            options=["gpt-4-turbo", "gpt-3.5-turbo", "gpt-4", "gpt-4-0613", "gpt-3.5-turbo-0613"],
            index=0,  # Default to gpt-4-turbo which supports response_format
            help="Select a model that supports JSON response format for best results"
        )
    elif eval_provider == "anthropic":
        anthropic_model = st.selectbox(
            "Anthropic Model",
            options=["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
            index=0
        )
    elif eval_provider == "mistral":
        mistral_model = st.selectbox(
            "Mistral Model",
            options=["mistral-medium", "mistral-large", "mistral-small"],
            index=0
        )
    elif eval_provider == "google":
        google_model = st.selectbox(
            "Google Model",
            options=["gemini-1.5-pro", "gemini-1.0-pro"],
            index=0
        )
    
    # Add evaluation toggle
    enable_auto_evaluation = st.checkbox("Auto-evaluate recipes", value=True)
    
    # Initialize or update evaluation manager
    if api_key:
        # Get the model based on selected provider
        selected_model = None
        if eval_provider == "openai":
            selected_model = openai_model
        elif eval_provider == "anthropic":
            selected_model = anthropic_model
        elif eval_provider == "mistral":
            selected_model = mistral_model
        elif eval_provider == "google":
            selected_model = google_model
        
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

# Main content
if api_key:
    if st.button("Generate Meal Plan", type="primary"):
        with st.spinner("Generating your meal plan... This may take a moment."):
            try:
                # Create planner with custom dates
                planner = VegetarianMealPlanner(api_key)
                
                # Use the CoT version of the meal planner if reasoning is enabled
                if st.session_state.show_reasoning:
                    try:
                        meal_plan_data = planner.generate_meal_plan_with_cot(
                            start_date=start_date, 
                            end_date=end_date,
                            complexity=meal_complexity
                        )
                        
                        # Store the raw meal plan data for reasoning display
                        st.session_state.meal_plan_data = meal_plan_data
                        
                        # The meal plan text is already set by the CoT method
                        meal_plan = planner.meal_plan
                        
                        # Print debug info
                        print("CoT meal plan data keys:", meal_plan_data.keys())
                        if "days" in meal_plan_data:
                            print(f"Number of days: {len(meal_plan_data['days'])}")
                            if meal_plan_data["days"]:
                                print(f"First day keys: {meal_plan_data['days'][0].keys()}")
                    except Exception as e:
                        st.error(f"Error in CoT generation: {str(e)}")
                        st.error(traceback.format_exc())
                        # Fallback to regular meal plan
                        meal_plan = planner.generate_meal_plan(start_date=start_date, end_date=end_date)
                        st.session_state.meal_plan_data = None
                else:
                    # Use the original method if reasoning is not needed
                    meal_plan = planner.generate_meal_plan(start_date=start_date, end_date=end_date)
                    st.session_state.meal_plan_data = None
                
                grocery_list = planner.extract_grocery_list()
                
                # Store meal plan in session state
                st.session_state.meal_plan = meal_plan
                st.session_state.grocery_list = grocery_list
                
                # Display success message
                st.success("Meal plan generated successfully!")
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.error(f"Error details: {type(e).__name__}")
                st.error(traceback.format_exc())

    # Display meal plan if it exists
    if 'meal_plan' in st.session_state and st.session_state.meal_plan:
        st.markdown("## 📅 Your Weekly Meal Plan")
        st.markdown(f"**Period:** {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}")
        
        # Display reasoning if enabled and available
        if st.session_state.show_reasoning and 'meal_plan_data' in st.session_state and st.session_state.meal_plan_data:
            reasoning_data = st.session_state.meal_plan_data.get('reasoning', {})
            
            if reasoning_data:
                with st.expander("💡 Nutritional Reasoning & Strategy", expanded=True):
                    # Create tabs for different aspects of reasoning
                    reasoning_tabs = st.tabs([
                        "Pre-Diabetic Strategy", 
                        "Vegetarian Nutrition", 
                        "Meal Variety"
                    ])
                    
                    # Process and display each reasoning aspect
                    with reasoning_tabs[0]:
                        diabetic_text = reasoning_data.get("pre_diabetic_considerations", 
                                        reasoning_data.get("nutritional_considerations", ""))
                        
                        # Add visual enhancements
                        highlight_terms = [
                            ("glycemic index", "📊 **glycemic index**"),
                            ("blood sugar", "🩸 **blood sugar**"),
                            ("carbohydrates", "🌾 **carbohydrates**"),
                            ("fiber", "🌱 **fiber**"),
                            ("protein", "💪 **protein**"),
                            ("fat", "🥑 **fat**"),
                        ]
                        
                        enhanced_text = str(diabetic_text)
                        for term, replacement in highlight_terms:
                            enhanced_text = enhanced_text.replace(term, replacement)
                        
                        st.markdown(enhanced_text)
                        
                        # Add educational info box
                        st.info("""
                        **Why This Matters**: Pre-diabetic diets focus on managing blood sugar while ensuring complete nutrition. 
                        Low glycemic foods, adequate protein, and fiber-rich choices help maintain stable glucose levels.
                        """)
                    
                    with reasoning_tabs[1]:
                        veg_text = reasoning_data.get("vegetarian_considerations", 
                                   reasoning_data.get("protein_sources", ""))
                        
                        if not veg_text:
                            veg_text = """
                            This meal plan ensures complete vegetarian nutrition by:
                            
                            - **Diverse protein sources** including legumes, tofu, tempeh, dairy, nuts, and seeds
                            - **Complete amino acid profiles** through complementary proteins
                            - **Strategic inclusion of foods rich in iron, B12, zinc, and calcium** that can be lacking in vegetarian diets
                            - **Healthy fat sources** from nuts, seeds, avocados, and olive oil
                            """
                        
                        st.markdown(str(veg_text))
                        
                        # Visual element - protein sources table
                        st.subheader("Key Protein Sources in Your Meal Plan")
                        protein_sources = {
                            "Source": ["Legumes", "Dairy", "Tofu/Tempeh", "Nuts & Seeds", "Whole Grains"],
                            "Protein (g/serving)": ["7-9", "8-10", "10-20", "5-7", "3-5"],
                            "Complete Protein": ["No*", "Yes", "Yes", "No*", "No*"],
                            "Key Benefits": ["Fiber, Iron", "Calcium, B12", "All Amino Acids", "Healthy Fats", "Fiber, B Vitamins"]
                        }
                        st.dataframe(protein_sources, use_container_width=True)
                        st.caption("* Incomplete proteins can be combined to form complete protein profiles")
                    
                    with reasoning_tabs[2]:
                        variety_text = reasoning_data.get("meal_variety", 
                                       reasoning_data.get("meal_balance", ""))
                        
                        if not variety_text:
                            variety_text = """
                            The meal plan incorporates variety through:
                            
                            - **Diverse cuisines and flavor profiles** to prevent menu fatigue
                            - **Different cooking techniques** to vary textures and taste experiences
                            - **Strategic leftovers planning** for efficiency without repetition
                            - **Seasonal ingredients** for freshness and nutritional diversity
                            - **Balance of different food groups** across the week
                            """
                        
                        st.markdown(str(variety_text))

        # Parse and display meal plan as table
        try:
            df_meals = parse_meal_plan_to_dataframe(st.session_state.meal_plan)
            
            # Display table
            if not df_meals.empty:
                try:
                    # Create a unique identifier for each meal - UPDATED to use the generate_unique_id function
                    df_meals['unique_id'] = df_meals.apply(generate_unique_id, axis=1)
                    
                    # Add debugging info if reasoning is enabled (can be removed in production)
                    if st.session_state.show_reasoning and st.session_state.recipes:
                        with st.expander("Debug Information", expanded=False):
                            st.write(f"Number of meals in table: {len(df_meals)}")
                            st.write(f"Number of recipes stored: {len(st.session_state.recipes)}")
                            st.write(f"Recipe keys: {list(st.session_state.recipes.keys())[:5]}")
                            st.write(f"Table unique_ids: {df_meals['unique_id'].tolist()[:5]}")
                    
                    # Create and display pivot table
                    pivot_df = create_pivot_table(df_meals)
                    st.dataframe(pivot_df, use_container_width=True, hide_index=True)
                except Exception as e:
                    st.error(f"Error creating table view: {str(e)}")
                    # Fallback to simpler display
                    st.dataframe(df_meals, use_container_width=True)
                
                # Generate Recipe Section
                st.markdown("""
                <div class="section-header">
                    <h2>👨‍🍳 Recipe Generation</h2>
                    <p class="section-subtitle">Generate detailed recipes and evaluate them against our rubric</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Create list view for recipes
                for idx, (_, meal) in enumerate(df_meals.iterrows()):
                    try:
                        # Create recipe list item
                        meal_score = ""
                        if meal['unique_id'] in st.session_state.evaluations:
                            eval_result = st.session_state.evaluations[meal['unique_id']]
                            if "score_breakdown" in eval_result and "final_score" in eval_result["score_breakdown"]:
                                final_score = eval_result["score_breakdown"]["final_score"]
                                meal_score = f"<span class='recipe-score'>Score: {final_score:.1f}/5.0</span>"
                        
                        st.markdown(f"""
                        <div class="recipe-list-item">
                            <div class="recipe-info">
                                <div class="recipe-info-title">{meal['Meal Name']} {meal_score}</div>
                                <div class="recipe-info-meta">{meal['Day']} • {meal['Meal'].split('(')[0].strip()}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Create columns for buttons and status
                        col1, col2, col3, col4 = st.columns([2, 2, 2, 3])
                        
                        unique_key = f"recipe_{meal['unique_id']}"
                        
                        with col1:
                            # Generate/Refresh Recipe button
                            button_text = "Get Recipe" if meal['unique_id'] not in st.session_state.recipes else "Refresh Recipe"
                            button_type = "primary" if meal['unique_id'] not in st.session_state.recipes else "secondary"
                            
                            if st.button(button_text, key=unique_key, type=button_type, use_container_width=True):
                                with st.spinner(f"Generating recipe for {meal['Meal Name']}..."):
                                    if st.session_state.recipe_agent:
                                        recipe = st.session_state.recipe_agent.generate_recipe(meal['Meal Name'])
                                        st.session_state.recipes[meal['unique_id']] = recipe
                                        
                                        # Auto-evaluate if enabled
                                        if enable_auto_evaluation and st.session_state.evaluation_manager:
                                            with st.spinner("Evaluating recipe..."):
                                                try:
                                                    eval_result = st.session_state.evaluation_manager.evaluate_recipe(recipe)
                                                    st.session_state.evaluations[meal['unique_id']] = eval_result
                                                except Exception as e:
                                                    st.error(f"Evaluation error: {str(e)}")
                                        
                                        st.rerun()
                        
                        with col2:
                            # Evaluate Recipe button
                            eval_button_text = "Evaluate" if meal['unique_id'] not in st.session_state.evaluations else "Re-evaluate"
                            eval_button_disabled = meal['unique_id'] not in st.session_state.recipes
                            
                            if st.button(eval_button_text, key=f"eval_{unique_key}", disabled=eval_button_disabled, use_container_width=True):
                                if st.session_state.evaluation_manager and meal['unique_id'] in st.session_state.recipes:
                                    with st.spinner("Evaluating recipe..."):
                                        try:
                                            eval_result = st.session_state.evaluation_manager.evaluate_recipe(
                                                st.session_state.recipes[meal['unique_id']]
                                            )
                                            st.session_state.evaluations[meal['unique_id']] = eval_result
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Evaluation error: {str(e)}")
                        
                        with col3:
                            # Copy to Clipboard button (only show if recipe exists)
                            if meal['unique_id'] in st.session_state.recipes:
                                if st.button("Copy", key=f"copy_{unique_key}", use_container_width=True):
                                    st.toast("Recipe copied to clipboard!")
                                    # Note: JavaScript clipboard access is limited in Streamlit
                                    # We'll use a simpler approach with a copy hint
                                    st.code(st.session_state.recipes[meal['unique_id']], language="text")
                        
                        with col4:
                            # Status indicator with evaluation score if available
                            if meal['unique_id'] in st.session_state.evaluations:
                                eval_result = st.session_state.evaluations[meal['unique_id']]
                                if "score_breakdown" in eval_result and "final_score" in eval_result["score_breakdown"]:
                                    final_score = eval_result["score_breakdown"]["final_score"]
                                    # Color-code based on score
                                    score_color = "#4CAF50" if final_score >= 4.0 else "#FFC107" if final_score >= 3.0 else "#F44336"
                                    st.markdown(f'<span class="recipe-status-badge" style="background-color: {score_color};">Score: {final_score:.1f}/5.0</span>', unsafe_allow_html=True)
                                else:
                                    st.markdown('<span class="recipe-status-badge status-ready-badge">✓ Recipe Evaluated</span>', unsafe_allow_html=True)
                            elif meal['unique_id'] in st.session_state.recipes:
                                st.markdown('<span class="recipe-status-badge status-ready-badge">✓ Recipe Ready</span>', unsafe_allow_html=True)
                            else:
                                st.markdown('<span class="recipe-status-badge status-pending-badge">Not Generated</span>', unsafe_allow_html=True)
                        
                        # Display recipe and evaluation if they exist
                        if meal['unique_id'] in st.session_state.recipes:
                            # Create tabs for recipe and evaluation
                            recipe_tabs = st.tabs(["📖 Recipe", "📊 Evaluation"])
                            
                            with recipe_tabs[0]:
                                st.markdown(f"""
                                <div class="recipe-content-wrapper">
                                    <div class="recipe-content-text">
                                    {st.session_state.recipes[meal['unique_id']]}
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Add download button
                                st.download_button(
                                    label="⬇️ Download Recipe",
                                    data=st.session_state.recipes[meal['unique_id']],
                                    file_name=f"recipe_{meal['Meal Name'].replace(' ', '_')}.txt",
                                    mime="text/plain",
                                    key=f"download_{meal['unique_id']}",
                                    use_container_width=True
                                )
                            
                            with recipe_tabs[1]:
                                if meal['unique_id'] in st.session_state.evaluations:
                                    # Render evaluation UI
                                    eval_result = st.session_state.evaluations[meal['unique_id']]
                                    render_evaluation_ui(eval_result)
                                    
                                    # Add download button for evaluation
                                    st.download_button(
                                        label="⬇️ Download Evaluation Report",
                                        data=str(eval_result),
                                        file_name=f"evaluation_{meal['Meal Name'].replace(' ', '_')}.json",
                                        mime="application/json",
                                        key=f"download_eval_{meal['unique_id']}",
                                        use_container_width=True
                                    )
                                else:
                                    st.info("No evaluation data available. Click the 'Evaluate' button to analyze this recipe.")
                                    
                                    if st.button("Run Evaluation Now", key=f"quick_eval_{meal['unique_id']}"):
                                        if st.session_state.evaluation_manager:
                                            with st.spinner("Evaluating recipe..."):
                                                try:
                                                    eval_result = st.session_state.evaluation_manager.evaluate_recipe(
                                                        st.session_state.recipes[meal['unique_id']]
                                                    )
                                                    st.session_state.evaluations[meal['unique_id']] = eval_result
                                                    st.rerun()
                                                except Exception as e:
                                                    st.error(f"Evaluation error: {str(e)}")
                    except Exception as e:
                        st.error(f"Error displaying recipe card: {str(e)}")
                    
                    # Add spacing between list items
                    st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)
                
                # Add divider before next section
                st.markdown('<div class="recipe-section-divider"></div>', unsafe_allow_html=True)
                
                # Add summary of evaluations if any exist
                if hasattr(st.session_state, 'evaluations') and st.session_state.evaluations:
                    st.markdown("### 🏆 Recipe Evaluation Summary")
                    
                    # Calculate average scores and best recipes
                    eval_data = []
                    best_recipe = {"meal_id": None, "score": 0, "name": None}
                    worst_recipe = {"meal_id": None, "score": 5, "name": None}
                    total_score = 0
                    count = 0
                    
                    for meal_id, eval_result in st.session_state.evaluations.items():
                        if "score_breakdown" in eval_result and "final_score" in eval_result["score_breakdown"]:
                            # Find the meal name from df_meals
                            meal_name = None
                            for _, meal in df_meals.iterrows():
                                if meal['unique_id'] == meal_id:
                                    meal_name = meal['Meal Name']
                                    break
                            
                            score = eval_result["score_breakdown"]["final_score"]
                            
                            # Track best and worst recipes
                            if score > best_recipe["score"]:
                                best_recipe = {"meal_id": meal_id, "score": score, "name": meal_name}
                            
                            if score < worst_recipe["score"]:
                                worst_recipe = {"meal_id": meal_id, "score": score, "name": meal_name}
                            
                            # Add to totals for average
                            total_score += score
                            count += 1
                            
                            # Build data for summary table
                            interpretation = eval_result.get("feedback", {}).get("interpretation", "")
                            eval_data.append({
                                "Meal": meal_name,
                                "Score": f"{score:.1f}/5.0",
                                "Rating": interpretation
                            })
                    
                    # Display evaluation summary metrics
                    if count > 0:
                        avg_score = total_score / count
                        
                        # Create metric cards in columns
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Recipes Evaluated", count)
                        
                        with col2:
                            st.metric("Average Score", f"{avg_score:.1f}")
                        
                        with col3:
                            if best_recipe["name"]:
                                st.metric("Best Recipe", f"{best_recipe['score']:.1f}", best_recipe["name"])
                        
                        with col4:
                            if count > 1 and worst_recipe["name"]:  # Only show worst if more than 1 recipe
                                st.metric("Needs Most Improvement", f"{worst_recipe['score']:.1f}", worst_recipe["name"])
                        
                        # Display evaluation summary table
                        if eval_data:
                            st.dataframe(eval_data, use_container_width=True, hide_index=True)

            else:
                st.warning("Could not parse the meal plan into a table. Showing raw text:")
                st.text(st.session_state.meal_plan)
        except Exception as e:
            st.error(f"Error parsing meal plan: {str(e)}")
            st.error(traceback.format_exc())
            st.text(st.session_state.meal_plan)
        
        # Download buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            st.download_button(
                label="📥 Meal Plan",
                data=st.session_state.meal_plan,
                file_name=f"meal_plan_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.txt",
                mime="text/plain"
            )
        
        with col2:
            st.download_button(
                label="📥 Grocery List",
                data=st.session_state.grocery_list,
                file_name=f"grocery_list_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.txt",
                mime="text/plain"
            )
        
        # Recipe and evaluation export options
        if st.session_state.recipes:
            with col3:
                # Create a dropdown for download options
                download_option = st.selectbox(
                    "Choose download option",
                    ["All Recipes", "All Evaluations", "Complete Report"],
                    key="download_option"
                )
                
                if download_option == "All Recipes":
                    all_recipes = "\n\n".join([f"## {meal_id}\n{recipe}" for meal_id, recipe in st.session_state.recipes.items()])
                    st.download_button(
                        label="📥 Download All Recipes",
                        data=all_recipes,
                        file_name=f"all_recipes_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.txt",
                        mime="text/plain"
                    )
                elif download_option == "All Evaluations" and hasattr(st.session_state, 'evaluations') and st.session_state.evaluations:
                    import json
                    all_evaluations = json.dumps(st.session_state.evaluations, indent=2)
                    st.download_button(
                        label="📥 Download All Evaluations",
                        data=all_evaluations,
                        file_name=f"all_evaluations_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.json",
                        mime="application/json"
                    )
                elif download_option == "Complete Report":
                    # Generate comprehensive report with recipes and evaluations
                    report = f"# Vegetarian Pre-Diabetic Meal Plan Report\n\n"
                    report += f"Period: {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}\n\n"
                    
                    # Add meal plan overview
                    report += "## Meal Plan Overview\n\n"
                    report += st.session_state.meal_plan
                    
                    # Add recipes with evaluations
                    report += "\n\n## Recipes and Evaluations\n\n"
                    
                    for meal_id, recipe in st.session_state.recipes.items():
                        # Find meal name
                        meal_name = "Unnamed Recipe"
                        meal_day = "Unknown Day"
                        meal_type = "Unknown Meal"
                        for _, meal in df_meals.iterrows():
                            if meal['unique_id'] == meal_id:
                                meal_name = meal['Meal Name']
                                meal_day = meal['Day']
                                meal_type = meal['Meal']
                                break
                        
                        report += f"### {meal_name} ({meal_day}, {meal_type})\n\n"
                        
                        # Add evaluation summary if available
                        if meal_id in st.session_state.evaluations:
                            eval_result = st.session_state.evaluations[meal_id]
                            if "score_breakdown" in eval_result and "final_score" in eval_result["score_breakdown"]:
                                score = eval_result["score_breakdown"]["final_score"]
                                interpretation = eval_result.get("feedback", {}).get("interpretation", "")
                                report += f"**Evaluation Score:** {score:.1f}/5.0 - {interpretation}\n\n"
                                
                                # Add strengths
                                report += "**Strengths:**\n"
                                strengths = eval_result.get("feedback", {}).get("strengths", [])
                                if strengths:
                                    for strength in strengths:
                                        criterion = strength.get("criterion", "")
                                        report += f"- {criterion}\n"
                                else:
                                    report += "- No specific strengths highlighted\n"
                                
                                report += "\n"
                        
                        # Add the recipe itself
                        report += "**Recipe:**\n\n"
                        report += recipe
                        report += "\n\n---\n\n"
                    
                    # Add grocery list
                    report += "## Grocery List\n\n"
                    report += st.session_state.grocery_list
                    
                    # Download the complete report
                    st.download_button(
                        label="📥 Download Complete Report",
                        data=report,
                        file_name=f"complete_report_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.md",
                        mime="text/markdown"
                    )
                else:
                    st.warning("No evaluations available to download.")
         # Display grocery list as organized sections
        
        st.markdown("## 🛒 Grocery List")
        try:
            grocery_categories = parse_grocery_list_to_dict(st.session_state.grocery_list)
            
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
                except Exception as e:
                    st.error(f"Error displaying grocery categories: {str(e)}")
                    # Fallback to simple display
                    st.text(st.session_state.grocery_list)
            else:
                st.text(st.session_state.grocery_list)
        except Exception as e:
            st.error(f"Error parsing grocery list: {str(e)}")
            st.text(st.session_state.grocery_list)
        
        # Add summary statistics with compact styling
        st.markdown("## 📊 Summary")
        try:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                try:
                    st.metric("Total Meals", len(df_meals) if 'df_meals' in locals() else 0)
                except Exception as e:
                    st.metric("Total Meals", 0)
            
            with col2:
                try:
                    if 'df_meals' in locals() and 'Day' in df_meals.columns:
                        st.metric("Days Covered", len(df_meals['Day'].unique()))
                    elif 'df_meals' in locals() and 'Date' in df_meals.columns:
                        st.metric("Days Covered", len(df_meals['Date'].unique()))
                    else:
                        st.metric("Days Covered", 0)
                except Exception as e:
                    st.metric("Days Covered", 0)
            
            with col3:
                try:
                    if 'df_meals' in locals() and 'Meal' in df_meals.columns:
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
else:
    st.warning("Please enter your OpenAI API key to get started.")

# Footer
st.markdown("---")
st.markdown("*Created for AI Class Project | MIT License*")# streamlit_app.py
import streamlit as st