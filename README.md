# Vegetarian Meal Planner with Recipe Agent

A Streamlit application that generates weekly vegetarian meal plans optimized for pre-diabetic diets, with an AI-powered recipe generation agent.

## Features

- 🥗 **Weekly Meal Planning**: Generate personalized vegetarian meal plans
- 🤖 **Recipe Agent**: AI agent that generates detailed recipes using multiple tools
- 📊 **Nutritional Focus**: Optimized for pre-diabetic dietary requirements
- 🛒 **Grocery Lists**: Automatically generated shopping lists
- 📱 **Responsive UI**: Clean, organized interface with both column and table views
- 💾 **Export Options**: Download meal plans, recipes, and grocery lists

## Project Structure

```
vegetarian-meal-planner/
├── requirements.txt              # Project dependencies
├── streamlit_app.py             # Main Streamlit application with Recipe Agent
├── VegetarianMealPlanner.py     # Meal planning core functionality
├── recipe_agent.py              # Recipe generation agent with tools
└── README.md                    # This file
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd vegetarian-meal-planner
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Get an OpenAI API key:
   - Visit [OpenAI API Keys](https://platform.openai.com/api-keys)
   - Create a new API key

## Usage

1. Run the Streamlit app:
```bash
streamlit run streamlit_app.py
```

2. Enter your OpenAI API key in the sidebar

3. Select your date range (This Week, Custom Week, or Date Range)

4. Click "Generate Meal Plan" to create your weekly meal plan

5. Use "Generate Recipe" buttons to get detailed recipes using the AI agent

## Recipe Agent Features

The Recipe Agent uses multiple tools to create optimal recipes:

1. **Search Recipe Variations**: Finds alternative recipe ideas
2. **Check Nutritional Values**: Analyzes ingredient nutrition
3. **Suggest Substitutions**: Recommends pre-diabetic friendly substitutions
4. **Generate Shopping Lists**: Creates scaled grocery lists

## File Descriptions

### `streamlit_app.py`
Main application interface that:
- Handles user input and API key management
- Displays meal plans in column and table views
- Integrates the Recipe Agent for on-demand recipe generation
- Manages downloads and exports

### `VegetarianMealPlanner.py`
Core meal planning functionality:
- Generates weekly meal plans using OpenAI
- Extracts grocery lists
- Handles date range customization

### `recipe_agent.py`
AI agent for recipe generation:
- Defines tools for recipe enhancement
- Manages agent conversation flow
- Tracks tool usage and history

## Dependencies

- **Streamlit**: Web interface
- **OpenAI**: AI-powered content generation
- **Pandas**: Data processing and table management
- **Python-dotenv**: Environment variable management

## License

MIT License

## Support

For issues or questions, please open an issue in the repository.

## Acknowledgments

Created for AI Class Project