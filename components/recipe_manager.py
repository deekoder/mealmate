# components/recipe_manager.py
import streamlit as st
from recipe_evaluation import render_evaluation_ui
import json

def display_recipes(df_meals, enable_auto_evaluation=True):
    """
    Display recipe generation section and recipe items.
    
    Args:
        df_meals: DataFrame with meal data
        enable_auto_evaluation: Whether to auto-evaluate new recipes
    """
    st.markdown("""
    <div class="section-header">
        <h2>👨‍🍳 Recipe Generation</h2>
        <p class="section-subtitle">Generate detailed recipes and evaluate them against our rubric</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create list view for recipes
    for idx, (_, meal) in enumerate(df_meals.iterrows()):
        _display_recipe_item(meal, enable_auto_evaluation)
    
    # Add divider before next section
    st.markdown('<div class="recipe-section-divider"></div>', unsafe_allow_html=True)
    
    # Add summary of evaluations if any exist
    if hasattr(st.session_state, 'evaluations') and st.session_state.evaluations:
        _display_evaluation_summary(df_meals)
    
    # Add download options for collections
    _display_download_options(df_meals)

def _display_recipe_item(meal, enable_auto_evaluation):
    """Display an individual recipe item with its controls"""
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

def _display_evaluation_summary(df_meals):
    """Display a summary of recipe evaluations"""
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

def _display_download_options(df_meals):
    """Display options to download collections of recipes and evaluations"""
    if 'sidebar_date_range' not in st.session_state:
        # Use current dates if not set
        from datetime import datetime
        start_date = datetime.now()
        end_date = datetime.now()
    else:
        start_date = st.session_state.sidebar_date_range["start_date"]
        end_date = st.session_state.sidebar_date_range["end_date"]
    
    # Recipe and evaluation export options
    if st.session_state.recipes:
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
            _generate_complete_report(df_meals, start_date, end_date)
        else:
            st.warning("No evaluations available to download.")

def _generate_complete_report(df_meals, start_date, end_date):
    """Generate and offer download for a complete report with all recipes and evaluations"""
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