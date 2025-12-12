#!/bin/bash

echo "🏒 NHL Prediction Model - Dashboard Launcher"
echo "============================================="
echo ""
echo "Which dashboard would you like to launch?"
echo ""
echo "1) Enhanced Visualization Dashboard (RECOMMENDED)"
echo "   - Beautiful interactive analytics"
echo "   - Detailed explanations"
echo "   - Interactive charts with Plotly"
echo ""
echo "2) Original Model Training Dashboard"
echo "   - Train models on-the-fly"
echo "   - Compare different algorithms"
echo "   - Feature importance analysis"
echo ""
read -p "Enter your choice (1 or 2): " choice

case $choice in
    1)
        echo ""
        echo "🚀 Launching Enhanced Visualization Dashboard..."
        echo "Opening at http://localhost:8501"
        echo ""
        streamlit run visualization_dashboard_enhanced.py
        ;;
    2)
        echo ""
        echo "🚀 Launching Original Model Training Dashboard..."
        echo "Opening at http://localhost:8501"
        echo ""
        export PYTHONPATH="${PYTHONPATH}:${PWD}/src"
        streamlit run streamlit_app.py
        ;;
    *)
        echo ""
        echo "❌ Invalid choice. Please run again and select 1 or 2."
        exit 1
        ;;
esac

