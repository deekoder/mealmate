# utils/ui_helpers.py
import streamlit as st
import os

def load_css(file_path="styles.css"):
    """Load CSS from file"""
    try:
        with open(file_path, 'r') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"CSS file not found: {file_path}")
        # Basic fallback styles
        st.markdown("""
        <style>
        .recipe-list-item {
            background: #ffffff;
            border: 1px solid #e3e8ef;
            border-radius: 8px;
            margin-bottom: 12px;
            padding: 16px;
        }
        .recipe-info-title {
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 4px;
        }
        .recipe-info-meta {
            font-size: 13px;
            color: #6b7280;
        }
        .recipe-status-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 500;
            margin-left: 8px;
        }
        .recipe-content-wrapper {
            background: #f9fafb;
            border-radius: 6px;
            padding: 16px;
            margin-bottom: 12px;
        }
        </style>
        """, unsafe_allow_html=True)

def format_dimension_name(name):
    """Format dimension name for display in evaluations"""
    name = name.replace('_', ' ').title()
    return name

def format_criterion_name(name):
    """Format criterion name for display in evaluations"""
    name = name.replace('_', ' ').title()
    return name

def get_score_color(score):
    """Return a color based on the score value"""
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