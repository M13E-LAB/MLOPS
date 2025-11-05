"""
Tests unitaires pour les utilitaires
"""

import pytest
import os
import sys

def test_project_structure():
    """Vérifier que la structure du projet est correcte"""
    project_root = os.path.dirname(os.path.dirname(__file__))
    
    # Vérifier les dossiers principaux
    expected_dirs = ['api', 'k8s', 'airflow', 'monitoring']
    for dir_name in expected_dirs:
        dir_path = os.path.join(project_root, dir_name)
        assert os.path.exists(dir_path), f"Le dossier {dir_name} doit exister"

def test_requirements_file():
    """Vérifier que le fichier requirements.txt existe"""
    project_root = os.path.dirname(os.path.dirname(__file__))
    requirements_path = os.path.join(project_root, 'requirements.txt')
    assert os.path.exists(requirements_path), "Le fichier requirements.txt doit exister"

def test_kubernetes_manifests():
    """Vérifier que les manifests Kubernetes existent"""
    project_root = os.path.dirname(os.path.dirname(__file__))
    k8s_dir = os.path.join(project_root, 'k8s')
    
    expected_files = [
        'namespace.yaml',
        'mysql-deployment.yaml', 
        'minio-deployment.yaml',
        'api-simple-deployment.yaml'
    ]
    
    for file_name in expected_files:
        file_path = os.path.join(k8s_dir, file_name)
        assert os.path.exists(file_path), f"Le fichier {file_name} doit exister dans k8s/"

def test_documentation_files():
    """Vérifier que la documentation existe"""
    project_root = os.path.dirname(os.path.dirname(__file__))
    
    expected_docs = [
        'README.md',
        'INSTALLATION_GUIDE.md',
        'DOCUMENTATION_TECHNIQUE.md',
        'DEMO_GUIDE.md'
    ]
    
    for doc_name in expected_docs:
        doc_path = os.path.join(project_root, doc_name)
        assert os.path.exists(doc_path), f"Le fichier {doc_name} doit exister"

def test_python_version():
    """Vérifier la version Python"""
    assert sys.version_info >= (3, 9), "Python 3.9+ requis"
