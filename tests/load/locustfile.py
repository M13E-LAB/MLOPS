"""
Tests de charge avec Locust pour l'API MLOps
"""

from locust import HttpUser, task, between
import io
from PIL import Image
import random

class MLOpsAPIUser(HttpUser):
    wait_time = between(1, 3)  # Attendre entre 1 et 3 secondes entre les requêtes
    
    def on_start(self):
        """Méthode appelée au démarrage de chaque utilisateur"""
        # Créer une image de test
        self.test_image = self.create_test_image()
    
    def create_test_image(self):
        """Créer une image de test en mémoire"""
        # Créer une image RGB aléatoire
        width, height = 224, 224
        image = Image.new('RGB', (width, height))
        
        # Remplir avec des pixels aléatoires
        pixels = []
        for _ in range(width * height):
            pixels.append((
                random.randint(0, 255),  # R
                random.randint(0, 255),  # G
                random.randint(0, 255)   # B
            ))
        
        image.putdata(pixels)
        
        # Convertir en bytes
        img_bytes = io.BytesIO()
        image.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        return img_bytes.getvalue()
    
    @task(8)  # 80% des requêtes
    def predict_single_image(self):
        """Test de prédiction d'une seule image"""
        files = {"file": ("test_image.jpg", self.test_image, "image/jpeg")}
        
        with self.client.post("/predict", files=files, catch_response=True) as response:
            if response.status_code == 200:
                json_response = response.json()
                if "predicted_class" in json_response and "confidence" in json_response:
                    response.success()
                else:
                    response.failure("Missing required fields in response")
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(1)  # 10% des requêtes
    def get_health(self):
        """Test du endpoint de santé"""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                json_response = response.json()
                if "status" in json_response:
                    response.success()
                else:
                    response.failure("Missing status in health response")
            else:
                response.failure(f"Health check failed with status {response.status_code}")
    
    @task(1)  # 10% des requêtes
    def get_model_info(self):
        """Test du endpoint d'informations du modèle"""
        with self.client.get("/model/info", catch_response=True) as response:
            if response.status_code == 200:
                json_response = response.json()
                if "model_version" in json_response and "classes" in json_response:
                    response.success()
                else:
                    response.failure("Missing required fields in model info")
            elif response.status_code == 503:
                # Modèle non chargé, c'est acceptable
                response.success()
            else:
                response.failure(f"Model info failed with status {response.status_code}")

class MLOpsAPIStressUser(HttpUser):
    """Utilisateur pour les tests de stress avec des requêtes plus agressives"""
    wait_time = between(0.1, 0.5)  # Attente très courte
    
    def on_start(self):
        self.test_image = self.create_test_image()
    
    def create_test_image(self):
        """Créer une image de test plus grande pour stresser le système"""
        width, height = 512, 512  # Image plus grande
        image = Image.new('RGB', (width, height))
        
        pixels = []
        for _ in range(width * height):
            pixels.append((
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255)
            ))
        
        image.putdata(pixels)
        
        img_bytes = io.BytesIO()
        image.save(img_bytes, format='JPEG', quality=95)  # Haute qualité
        img_bytes.seek(0)
        
        return img_bytes.getvalue()
    
    @task
    def stress_predict(self):
        """Test de stress pour les prédictions"""
        files = {"file": ("stress_test.jpg", self.test_image, "image/jpeg")}
        
        with self.client.post("/predict", files=files, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 413:  # Fichier trop volumineux
                response.success()  # C'est un comportement attendu
            elif response.status_code == 503:  # Service indisponible
                response.failure("Service overloaded")
            else:
                response.failure(f"Unexpected status code {response.status_code}")

# Configuration pour différents scénarios de test
class MLOpsAPIBatchUser(HttpUser):
    """Utilisateur simulant des requêtes batch"""
    wait_time = between(5, 10)  # Attente plus longue entre les batches
    
    def on_start(self):
        # Créer plusieurs images pour les tests batch
        self.test_images = [self.create_test_image() for _ in range(5)]
    
    def create_test_image(self):
        width, height = 224, 224
        image = Image.new('RGB', (width, height))
        
        # Créer des patterns différents pour chaque image
        pixels = []
        pattern = random.choice(['random', 'gradient', 'noise'])
        
        if pattern == 'random':
            for _ in range(width * height):
                pixels.append((
                    random.randint(0, 255),
                    random.randint(0, 255),
                    random.randint(0, 255)
                ))
        elif pattern == 'gradient':
            for y in range(height):
                for x in range(width):
                    pixels.append((
                        int(255 * x / width),
                        int(255 * y / height),
                        128
                    ))
        else:  # noise
            base_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            for _ in range(width * height):
                noise = random.randint(-50, 50)
                pixels.append((
                    max(0, min(255, base_color[0] + noise)),
                    max(0, min(255, base_color[1] + noise)),
                    max(0, min(255, base_color[2] + noise))
                ))
        
        image.putdata(pixels)
        
        img_bytes = io.BytesIO()
        image.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        return img_bytes.getvalue()
    
    @task
    def batch_predict(self):
        """Test de prédictions en lot"""
        files = []
        for i, img in enumerate(self.test_images):
            files.append(("files", (f"batch_image_{i}.jpg", img, "image/jpeg")))
        
        with self.client.post("/predict/batch", files=files, catch_response=True) as response:
            if response.status_code == 200:
                json_response = response.json()
                if "results" in json_response and "batch_id" in json_response:
                    response.success()
                else:
                    response.failure("Missing required fields in batch response")
            elif response.status_code == 400:  # Trop d'images dans le batch
                response.success()  # Comportement attendu
            else:
                response.failure(f"Batch predict failed with status {response.status_code}")

# Scénarios de test personnalisés
def create_custom_load_test():
    """
    Exemple de configuration personnalisée pour les tests de charge
    
    Usage:
    locust -f locustfile.py --host=http://localhost:8000 \
           --users=50 --spawn-rate=5 --run-time=300s
    """
    pass

if __name__ == "__main__":
    # Configuration pour exécution directe
    import os
    import sys
    
    # Ajouter le répertoire parent au path pour les imports
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    print("🚀 Tests de charge MLOps API")
    print("📊 Scénarios disponibles:")
    print("   - MLOpsAPIUser: Tests normaux (80% predict, 10% health, 10% model info)")
    print("   - MLOpsAPIStressUser: Tests de stress avec images plus grandes")
    print("   - MLOpsAPIBatchUser: Tests de prédictions en lot")
    print("\n💡 Commandes d'exemple:")
    print("   locust -f locustfile.py --host=http://localhost:8000 --users=10 --spawn-rate=2")
    print("   locust -f locustfile.py --host=http://localhost:8000 --headless --users=50 --spawn-rate=5 --run-time=60s")
