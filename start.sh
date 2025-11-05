#!/bin/bash

# Script de démarrage rapide pour le projet MLOps
# Usage: ./start.sh [dev|prod|stop|clean]

set -e

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonctions utilitaires
print_header() {
    echo -e "${BLUE}"
    echo "🌼 =================================="
    echo "   MLOps Image Classification"
    echo "   Pissenlit vs Herbe"
    echo "=================================== 🌱${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Vérifier les prérequis
check_prerequisites() {
    print_info "Vérification des prérequis..."
    
    # Vérifier Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker n'est pas installé"
        exit 1
    fi
    
    # Vérifier Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose n'est pas installé"
        exit 1
    fi
    
    # Vérifier Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 n'est pas installé"
        exit 1
    fi
    
    print_success "Prérequis vérifiés"
}

# Démarrer l'environnement de développement
start_dev() {
    print_info "Démarrage de l'environnement de développement..."
    
    # Créer les dossiers nécessaires
    mkdir -p airflow/logs airflow/plugins models logs visualizations
    
    # Démarrer les services
    docker-compose -f docker-compose.dev.yml up -d
    
    print_info "Attente du démarrage des services..."
    sleep 30
    
    # Vérifier l'état des services
    print_info "État des services:"
    docker-compose -f docker-compose.dev.yml ps
    
    print_success "Environnement de développement démarré!"
    print_services_info
}

# Démarrer l'environnement de production (Kubernetes)
start_prod() {
    print_info "Démarrage de l'environnement de production..."
    
    # Vérifier kubectl
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl n'est pas installé"
        exit 1
    fi
    
    # Appliquer les manifests Kubernetes
    kubectl apply -f k8s/namespace.yaml
    kubectl apply -f k8s/
    
    print_info "Attente du déploiement..."
    kubectl wait --for=condition=available --timeout=300s deployment/mlops-api -n mlops
    kubectl wait --for=condition=available --timeout=300s deployment/mlops-webapp -n mlops
    
    print_success "Environnement de production démarré!"
    
    # Afficher les services
    kubectl get services -n mlops
}

# Arrêter les services
stop_services() {
    print_info "Arrêt des services..."
    
    # Arrêter Docker Compose
    if [ -f docker-compose.dev.yml ]; then
        docker-compose -f docker-compose.dev.yml down
    fi
    
    # Arrêter Kubernetes (si applicable)
    if command -v kubectl &> /dev/null; then
        kubectl delete namespace mlops --ignore-not-found=true
    fi
    
    print_success "Services arrêtés"
}

# Nettoyer l'environnement
clean_environment() {
    print_warning "Nettoyage de l'environnement..."
    
    # Arrêter les services
    stop_services
    
    # Supprimer les volumes Docker
    docker-compose -f docker-compose.dev.yml down -v
    
    # Nettoyer les images Docker
    docker system prune -f
    
    # Supprimer les dossiers temporaires
    rm -rf airflow/logs/* models/* logs/* visualizations/*
    
    print_success "Environnement nettoyé"
}

# Afficher les informations des services
print_services_info() {
    echo ""
    print_info "🌐 Services disponibles:"
    echo "┌─────────────────────────────────────────────────────────────┐"
    echo "│ Service                 │ URL                    │ Auth     │"
    echo "├─────────────────────────────────────────────────────────────┤"
    echo "│ 🔍 API Documentation    │ http://localhost:8000/docs        │"
    echo "│ 🌐 Web Application      │ http://localhost:8501             │"
    echo "│ 🔄 Airflow              │ http://localhost:8080  │ admin/admin │"
    echo "│ 📊 MLflow               │ http://localhost:5000             │"
    echo "│ 💾 Minio Console        │ http://localhost:9001  │ minioadmin │"
    echo "│ 📈 Grafana              │ http://localhost:3000  │ admin/admin │"
    echo "│ 🎯 Prometheus           │ http://localhost:9090             │"
    echo "└─────────────────────────────────────────────────────────────┘"
    echo ""
}

# Télécharger et préparer les données
setup_data() {
    print_info "Configuration des données..."
    
    # Vérifier si Python est disponible
    if command -v python3 &> /dev/null; then
        # Installer les dépendances si nécessaire
        if [ -f requirements.txt ]; then
            print_info "Installation des dépendances Python..."
            pip3 install -r requirements.txt
        fi
        
        # Télécharger les données
        if [ -f download_data.py ]; then
            print_info "Téléchargement des données..."
            python3 download_data.py
        fi
        
        # Explorer les données
        if [ -f data_exploration.py ]; then
            print_info "Exploration des données..."
            python3 data_exploration.py
        fi
    else
        print_warning "Python non disponible, téléchargement des données ignoré"
    fi
}

# Entraîner le modèle
train_model() {
    print_info "Entraînement du modèle..."
    
    if [ -f model_training.py ]; then
        python3 model_training.py
        print_success "Modèle entraîné avec succès!"
    else
        print_error "Script d'entraînement non trouvé"
    fi
}

# Tests de charge
run_load_tests() {
    print_info "Exécution des tests de charge..."
    
    # Vérifier si Locust est installé
    if ! command -v locust &> /dev/null; then
        print_info "Installation de Locust..."
        pip3 install locust
    fi
    
    # Exécuter les tests
    if [ -f tests/load/locustfile.py ]; then
        locust -f tests/load/locustfile.py --host=http://localhost:8000 \
               --users=10 --spawn-rate=2 --run-time=60s --headless \
               --html=load_test_report.html
        print_success "Tests de charge terminés. Rapport: load_test_report.html"
    else
        print_error "Fichier de tests de charge non trouvé"
    fi
}

# Afficher l'aide
show_help() {
    print_header
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  dev          Démarrer l'environnement de développement"
    echo "  prod         Démarrer l'environnement de production (Kubernetes)"
    echo "  stop         Arrêter tous les services"
    echo "  clean        Nettoyer l'environnement complètement"
    echo "  data         Télécharger et préparer les données"
    echo "  train        Entraîner le modèle"
    echo "  test         Exécuter les tests de charge"
    echo "  help         Afficher cette aide"
    echo ""
    echo "Examples:"
    echo "  $0 dev       # Démarrer en mode développement"
    echo "  $0 data      # Préparer les données"
    echo "  $0 train     # Entraîner le modèle"
    echo "  $0 test      # Tests de charge"
    echo "  $0 clean     # Tout nettoyer"
    echo ""
}

# Fonction principale
main() {
    print_header
    
    case "${1:-help}" in
        "dev")
            check_prerequisites
            start_dev
            ;;
        "prod")
            check_prerequisites
            start_prod
            ;;
        "stop")
            stop_services
            ;;
        "clean")
            clean_environment
            ;;
        "data")
            setup_data
            ;;
        "train")
            train_model
            ;;
        "test")
            run_load_tests
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# Exécuter la fonction principale avec tous les arguments
main "$@"
