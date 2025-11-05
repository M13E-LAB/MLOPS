-- Script d'initialisation de la base de données MLOps
-- Création de la table plants_data pour stocker les métadonnées des images

USE mlops_db;

-- Table pour stocker les métadonnées des images
CREATE TABLE IF NOT EXISTS plants_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    url_source VARCHAR(500) NOT NULL COMMENT 'URL source de l\'image sur GitHub',
    url_s3 VARCHAR(500) COMMENT 'URL de l\'image stockée dans S3/Minio',
    label ENUM('dandelion', 'grass') NOT NULL COMMENT 'Label de classification',
    filename VARCHAR(100) NOT NULL COMMENT 'Nom du fichier image',
    file_size INT COMMENT 'Taille du fichier en bytes',
    image_width INT COMMENT 'Largeur de l\'image en pixels',
    image_height INT COMMENT 'Hauteur de l\'image en pixels',
    download_status ENUM('pending', 'downloaded', 'failed') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_label (label),
    INDEX idx_download_status (download_status),
    INDEX idx_created_at (created_at),
    UNIQUE KEY unique_source_url (url_source)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table pour tracker les expériences MLflow
CREATE TABLE IF NOT EXISTS ml_experiments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    experiment_id VARCHAR(100) NOT NULL,
    run_id VARCHAR(100) NOT NULL,
    model_name VARCHAR(100),
    model_version VARCHAR(50),
    accuracy FLOAT,
    precision_score FLOAT,
    recall_score FLOAT,
    f1_score FLOAT,
    loss FLOAT,
    training_time_seconds INT,
    dataset_size INT,
    model_size_mb FLOAT,
    hyperparameters JSON,
    artifacts_path VARCHAR(500),
    status ENUM('running', 'finished', 'failed') DEFAULT 'running',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_experiment_id (experiment_id),
    INDEX idx_run_id (run_id),
    INDEX idx_model_name (model_name),
    INDEX idx_status (status),
    INDEX idx_accuracy (accuracy),
    UNIQUE KEY unique_run_id (run_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table pour tracker les déploiements de modèles
CREATE TABLE IF NOT EXISTS model_deployments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    deployment_id VARCHAR(100) NOT NULL,
    environment ENUM('dev', 'staging', 'production') NOT NULL,
    endpoint_url VARCHAR(500),
    docker_image VARCHAR(200),
    kubernetes_namespace VARCHAR(100),
    deployment_status ENUM('deploying', 'active', 'inactive', 'failed') DEFAULT 'deploying',
    health_check_url VARCHAR(500),
    last_health_check TIMESTAMP,
    cpu_request VARCHAR(20),
    memory_request VARCHAR(20),
    replicas INT DEFAULT 1,
    deployed_by VARCHAR(100),
    deployed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_model_name (model_name),
    INDEX idx_environment (environment),
    INDEX idx_deployment_status (deployment_status),
    INDEX idx_deployed_at (deployed_at),
    UNIQUE KEY unique_deployment (deployment_id, environment)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table pour tracker les prédictions API
CREATE TABLE IF NOT EXISTS api_predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    request_id VARCHAR(100) NOT NULL,
    model_name VARCHAR(100),
    model_version VARCHAR(50),
    input_image_url VARCHAR(500),
    input_image_hash VARCHAR(64),
    predicted_class VARCHAR(50),
    confidence_score FLOAT,
    prediction_time_ms INT,
    client_ip VARCHAR(45),
    user_agent TEXT,
    api_version VARCHAR(20),
    response_status INT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_request_id (request_id),
    INDEX idx_model_name (model_name),
    INDEX idx_predicted_class (predicted_class),
    INDEX idx_created_at (created_at),
    INDEX idx_response_status (response_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table pour monitoring des performances système
CREATE TABLE IF NOT EXISTS system_metrics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    metric_unit VARCHAR(20),
    environment ENUM('dev', 'staging', 'production') NOT NULL,
    hostname VARCHAR(100),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_service_name (service_name),
    INDEX idx_metric_name (metric_name),
    INDEX idx_environment (environment),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insertion des données initiales pour les images
-- Images de pissenlits
INSERT IGNORE INTO plants_data (url_source, label, filename) VALUES
('https://raw.githubusercontent.com/btphan95/greenr-airflow/refs/heads/master/data/dandelion/00000000.jpg', 'dandelion', '00000000.jpg'),
('https://raw.githubusercontent.com/btphan95/greenr-airflow/refs/heads/master/data/dandelion/00000001.jpg', 'dandelion', '00000001.jpg'),
('https://raw.githubusercontent.com/btphan95/greenr-airflow/refs/heads/master/data/dandelion/00000002.jpg', 'dandelion', '00000002.jpg'),
('https://raw.githubusercontent.com/btphan95/greenr-airflow/refs/heads/master/data/dandelion/00000003.jpg', 'dandelion', '00000003.jpg'),
('https://raw.githubusercontent.com/btphan95/greenr-airflow/refs/heads/master/data/dandelion/00000004.jpg', 'dandelion', '00000004.jpg');

-- Générer le reste des URLs avec une procédure stockée
DELIMITER //

CREATE PROCEDURE IF NOT EXISTS PopulatePlantsData()
BEGIN
    DECLARE i INT DEFAULT 0;
    
    -- Insérer les images de pissenlits (0-199)
    WHILE i < 200 DO
        INSERT IGNORE INTO plants_data (url_source, label, filename) 
        VALUES (
            CONCAT('https://raw.githubusercontent.com/btphan95/greenr-airflow/refs/heads/master/data/dandelion/', LPAD(i, 8, '0'), '.jpg'),
            'dandelion',
            CONCAT(LPAD(i, 8, '0'), '.jpg')
        );
        SET i = i + 1;
    END WHILE;
    
    -- Reset counter pour les images d'herbe
    SET i = 0;
    
    -- Insérer les images d'herbe (0-199)
    WHILE i < 200 DO
        INSERT IGNORE INTO plants_data (url_source, label, filename) 
        VALUES (
            CONCAT('https://raw.githubusercontent.com/btphan95/greenr-airflow/refs/heads/master/data/grass/', LPAD(i, 8, '0'), '.jpg'),
            'grass',
            CONCAT(LPAD(i, 8, '0'), '.jpg')
        );
        SET i = i + 1;
    END WHILE;
    
END //

DELIMITER ;

-- Exécuter la procédure pour peupler la table
CALL PopulatePlantsData();

-- Créer un utilisateur pour l'application
CREATE USER IF NOT EXISTS 'mlops_app'@'%' IDENTIFIED BY 'mlops_app_password';
GRANT SELECT, INSERT, UPDATE, DELETE ON mlops_db.* TO 'mlops_app'@'%';

-- Créer un utilisateur en lecture seule pour le monitoring
CREATE USER IF NOT EXISTS 'mlops_readonly'@'%' IDENTIFIED BY 'mlops_readonly_password';
GRANT SELECT ON mlops_db.* TO 'mlops_readonly'@'%';

FLUSH PRIVILEGES;

-- Afficher un résumé des données insérées
SELECT 
    label,
    COUNT(*) as count,
    MIN(filename) as first_file,
    MAX(filename) as last_file
FROM plants_data 
GROUP BY label;

SELECT 'Database initialization completed successfully!' as status;
