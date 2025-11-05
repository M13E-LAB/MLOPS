#!/usr/bin/env python3
"""
Script d'exploration des données pour le projet MLOps
Classification pissenlit vs herbe
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from PIL import Image
import pandas as pd
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

def analyze_dataset():
    """Analyser la structure et les caractéristiques du dataset"""
    print("🔍 Analyse du dataset MLOps - Classification Pissenlit vs Herbe")
    print("=" * 60)
    
    # Chemins des données
    data_dir = Path("data")
    dandelion_dir = data_dir / "dandelion"
    grass_dir = data_dir / "grass"
    
    # Vérifier l'existence des dossiers
    if not dandelion_dir.exists() or not grass_dir.exists():
        print("❌ Dossiers de données non trouvés. Exécutez d'abord download_data.py")
        return
    
    # Compter les images
    dandelion_images = list(dandelion_dir.glob("*.jpg"))
    grass_images = list(grass_dir.glob("*.jpg"))
    
    print(f"📊 Structure du dataset:")
    print(f"   🌼 Pissenlits: {len(dandelion_images)} images")
    print(f"   🌱 Herbe: {len(grass_images)} images")
    print(f"   📁 Total: {len(dandelion_images) + len(grass_images)} images")
    
    # Analyser les dimensions des images
    print(f"\n🖼️  Analyse des dimensions des images:")
    analyze_image_dimensions(dandelion_images, grass_images)
    
    # Visualiser quelques exemples
    print(f"\n🎨 Génération de visualisations...")
    create_sample_visualization(dandelion_images, grass_images)
    
    # Analyser la distribution des tailles de fichiers
    analyze_file_sizes(dandelion_images, grass_images)
    
    print(f"\n✅ Exploration terminée! Consultez les graphiques générés.")

def analyze_image_dimensions(dandelion_images, grass_images):
    """Analyser les dimensions des images"""
    dimensions_data = []
    
    # Échantillonner quelques images pour l'analyse (pour éviter de charger toutes les images)
    sample_size = min(50, len(dandelion_images))
    
    print(f"   📏 Analyse sur un échantillon de {sample_size} images par classe...")
    
    # Analyser les pissenlits
    for img_path in dandelion_images[:sample_size]:
        try:
            with Image.open(img_path) as img:
                width, height = img.size
                dimensions_data.append({
                    'class': 'dandelion',
                    'width': width,
                    'height': height,
                    'ratio': width/height,
                    'pixels': width * height
                })
        except Exception as e:
            print(f"   ⚠️  Erreur avec {img_path}: {e}")
    
    # Analyser l'herbe
    for img_path in grass_images[:sample_size]:
        try:
            with Image.open(img_path) as img:
                width, height = img.size
                dimensions_data.append({
                    'class': 'grass',
                    'width': width,
                    'height': height,
                    'ratio': width/height,
                    'pixels': width * height
                })
        except Exception as e:
            print(f"   ⚠️  Erreur avec {img_path}: {e}")
    
    # Créer un DataFrame pour l'analyse
    df = pd.DataFrame(dimensions_data)
    
    if not df.empty:
        print(f"\n   📐 Statistiques des dimensions:")
        for class_name in ['dandelion', 'grass']:
            class_data = df[df['class'] == class_name]
            if not class_data.empty:
                print(f"   {class_name.capitalize()}:")
                print(f"      Largeur: {class_data['width'].mean():.0f}±{class_data['width'].std():.0f} px")
                print(f"      Hauteur: {class_data['height'].mean():.0f}±{class_data['height'].std():.0f} px")
                print(f"      Ratio: {class_data['ratio'].mean():.2f}±{class_data['ratio'].std():.2f}")
                print(f"      Pixels: {class_data['pixels'].mean():.0f}±{class_data['pixels'].std():.0f}")
    
    return df

def create_sample_visualization(dandelion_images, grass_images):
    """Créer une visualisation d'échantillons d'images"""
    fig, axes = plt.subplots(2, 5, figsize=(15, 6))
    fig.suptitle('Échantillons du Dataset - Pissenlits vs Herbe', fontsize=16, fontweight='bold')
    
    # Afficher 5 pissenlits
    for i in range(5):
        if i < len(dandelion_images):
            try:
                img = Image.open(dandelion_images[i])
                axes[0, i].imshow(img)
                axes[0, i].set_title(f'Pissenlit {i+1}', fontsize=10)
                axes[0, i].axis('off')
            except Exception as e:
                axes[0, i].text(0.5, 0.5, f'Erreur\n{e}', ha='center', va='center')
                axes[0, i].set_title(f'Pissenlit {i+1} (Erreur)', fontsize=10)
    
    # Afficher 5 herbes
    for i in range(5):
        if i < len(grass_images):
            try:
                img = Image.open(grass_images[i])
                axes[1, i].imshow(img)
                axes[1, i].set_title(f'Herbe {i+1}', fontsize=10)
                axes[1, i].axis('off')
            except Exception as e:
                axes[1, i].text(0.5, 0.5, f'Erreur\n{e}', ha='center', va='center')
                axes[1, i].set_title(f'Herbe {i+1} (Erreur)', fontsize=10)
    
    plt.tight_layout()
    plt.savefig('dataset_samples.png', dpi=300, bbox_inches='tight')
    plt.show()
    print("   💾 Échantillons sauvegardés: dataset_samples.png")

def analyze_file_sizes(dandelion_images, grass_images):
    """Analyser la distribution des tailles de fichiers"""
    file_sizes = []
    
    # Analyser les tailles de fichiers
    for img_path in dandelion_images:
        try:
            size_kb = img_path.stat().st_size / 1024
            file_sizes.append({'class': 'dandelion', 'size_kb': size_kb})
        except:
            pass
    
    for img_path in grass_images:
        try:
            size_kb = img_path.stat().st_size / 1024
            file_sizes.append({'class': 'grass', 'size_kb': size_kb})
        except:
            pass
    
    if file_sizes:
        df_sizes = pd.DataFrame(file_sizes)
        
        # Créer un graphique de distribution des tailles
        plt.figure(figsize=(12, 5))
        
        plt.subplot(1, 2, 1)
        sns.histplot(data=df_sizes, x='size_kb', hue='class', bins=30, alpha=0.7)
        plt.title('Distribution des Tailles de Fichiers')
        plt.xlabel('Taille (KB)')
        plt.ylabel('Nombre d\'images')
        
        plt.subplot(1, 2, 2)
        sns.boxplot(data=df_sizes, x='class', y='size_kb')
        plt.title('Tailles de Fichiers par Classe')
        plt.xlabel('Classe')
        plt.ylabel('Taille (KB)')
        
        plt.tight_layout()
        plt.savefig('file_sizes_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        print(f"\n📊 Statistiques des tailles de fichiers:")
        for class_name in ['dandelion', 'grass']:
            class_data = df_sizes[df_sizes['class'] == class_name]
            if not class_data.empty:
                print(f"   {class_name.capitalize()}:")
                print(f"      Moyenne: {class_data['size_kb'].mean():.1f} KB")
                print(f"      Médiane: {class_data['size_kb'].median():.1f} KB")
                print(f"      Min-Max: {class_data['size_kb'].min():.1f} - {class_data['size_kb'].max():.1f} KB")
        
        print("   💾 Analyse des tailles sauvegardée: file_sizes_analysis.png")

def check_data_quality():
    """Vérifier la qualité des données"""
    print(f"\n🔍 Vérification de la qualité des données:")
    
    data_dir = Path("data")
    issues = []
    
    for class_dir in [data_dir / "dandelion", data_dir / "grass"]:
        if class_dir.exists():
            for img_path in class_dir.glob("*.jpg"):
                try:
                    # Essayer d'ouvrir l'image
                    with Image.open(img_path) as img:
                        # Vérifier si l'image est corrompue
                        img.verify()
                        
                        # Vérifier la taille minimale
                        if img.size[0] < 50 or img.size[1] < 50:
                            issues.append(f"Image trop petite: {img_path}")
                            
                except Exception as e:
                    issues.append(f"Image corrompue: {img_path} - {e}")
    
    if issues:
        print(f"   ⚠️  {len(issues)} problèmes détectés:")
        for issue in issues[:10]:  # Afficher les 10 premiers
            print(f"      - {issue}")
        if len(issues) > 10:
            print(f"      ... et {len(issues) - 10} autres")
    else:
        print(f"   ✅ Aucun problème de qualité détecté!")

if __name__ == "__main__":
    # Installer les dépendances si nécessaire
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
        from PIL import Image
        import pandas as pd
    except ImportError:
        print("📦 Installation des dépendances pour l'exploration...")
        os.system("pip install matplotlib seaborn pillow pandas")
        import matplotlib.pyplot as plt
        import seaborn as sns
        from PIL import Image
        import pandas as pd
    
    # Configuration matplotlib pour l'affichage
    plt.style.use('default')
    
    # Lancer l'analyse
    analyze_dataset()
    check_data_quality()
    
    print(f"\n🎯 Prochaines étapes recommandées:")
    print(f"   1. Examiner les visualisations générées")
    print(f"   2. Décider de la stratégie de préprocessing")
    print(f"   3. Créer le pipeline de données")
    print(f"   4. Commencer l'entraînement du modèle")
