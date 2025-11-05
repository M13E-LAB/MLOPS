#!/usr/bin/env python3
"""
Test simple pour Streamlit
"""

import streamlit as st

st.title("🌼 Test MLOps")
st.write("Si vous voyez ce message, Streamlit fonctionne !")

st.success("✅ Application Streamlit opérationnelle")

# Test de base
if st.button("Test"):
    st.balloons()
    st.write("🎉 Test réussi !")

# Informations
st.markdown("""
## Services MLOps Disponibles:
- **MLflow**: http://localhost:5001
- **Minio**: http://localhost:9001 (minioadmin/minioadmin123)  
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
""")
