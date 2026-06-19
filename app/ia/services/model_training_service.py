import os
import logging
import joblib
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

from ..ml.features import build_training_dataset, FEATURE_COLUMNS
from ..repositories.ai_model_repository import AIModelRepository
from ...models.prediccion_ia import AIModel

logger = logging.getLogger(__name__)

# Base storage path
STORAGE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../modelos"))


class ModelTrainingService:
    @staticmethod
    def train_models() -> dict:
        """
        Trains RandomForestClassifier and XGBClassifier models on client risk historical data.
        Selects the best model based on ROC AUC, saves both to disk, registers them in the database,
        and marks the best one as active.
        """
        logger.info("Inicio de entrenamiento de modelos de riesgo crediticio.")
        
        # 1. Fetch training data
        df = build_training_dataset()
        
        if df.empty or len(df) < 10:
            err_msg = f"Insuficiente cantidad de datos históricos para entrenar. Se requieren al menos 10 clientes (actualmente: {len(df)})."
            logger.error(err_msg)
            raise ValueError(err_msg)
            
        unique_targets = df["target"].nunique()
        if unique_targets < 2:
            err_msg = "El dataset contiene una única clase para el target de riesgo. Se requieren ejemplos de clientes en mora y al día para entrenar."
            logger.error(err_msg)
            raise ValueError(err_msg)
            
        # 2. Split features and target
        X = df[FEATURE_COLUMNS]
        y = df["target"]
        
        # We split the data. Stratification is key in credit risk because default is usually rare (unbalanced classes).
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Ensure target folder exists
        os.makedirs(STORAGE_DIR, exist_ok=True)
        
        version = f"v_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        trained_models_info = []
        
        # 3. Train algorithms
        algorithms = {
            "RandomForestClassifier": RandomForestClassifier(n_estimators=100, random_state=42),
            "XGBClassifier": XGBClassifier(use_label_encoder=False, eval_metric="logloss", random_state=42)
        }
        
        best_roc_auc = -1.0
        best_model_db = None
        
        for name, clf in algorithms.items():
            logger.info(f"Entrenando algoritmo: {name}")
            clf.fit(X_train, y_train)
            
            # Predict
            y_pred = clf.predict(X_test)
            y_prob = clf.predict_proba(X_test)[:, 1]
            
            # Metrics
            acc = float(accuracy_score(y_test, y_pred))
            prec = float(precision_score(y_test, y_pred, zero_division=0))
            rec = float(recall_score(y_test, y_pred, zero_division=0))
            f1 = float(f1_score(y_test, y_pred, zero_division=0))
            roc_auc = float(roc_auc_score(y_test, y_prob))
            
            # Save file path
            filename = f"{name}_{version}.joblib"
            filepath = os.path.join(STORAGE_DIR, filename)
            joblib.dump(clf, filepath)
            
            logger.info(f"Modelo {name} entrenado exitosamente. Métricas: Accuracy={acc:.4f}, Precision={prec:.4f}, Recall={rec:.4f}, F1={f1:.4f}, ROC_AUC={roc_auc:.4f}")
            
            # Save model to DB
            model_record = AIModel(
                name=f"Modelo de Riesgo {name}",
                version=version,
                algorithm=name,
                accuracy=acc,
                precision=prec,
                recall=rec,
                f1_score=f1,
                roc_auc=roc_auc,
                model_path=filepath,
                is_active=False
            )
            
            # Create in DB
            AIModelRepository.create(model_record)
            trained_models_info.append({
                "id": model_record.id,
                "algorithm": name,
                "accuracy": acc,
                "precision": prec,
                "recall": rec,
                "f1_score": f1,
                "roc_auc": roc_auc
            })
            
            # Check if best model
            if roc_auc > best_roc_auc:
                best_roc_auc = roc_auc
                best_model_db = model_record
                
        # 4. Activate the best model
        if best_model_db:
            logger.info(f"Seleccionado el mejor modelo: {best_model_db.algorithm} (ID: {best_model_db.id}) con ROC AUC: {best_roc_auc:.4f}")
            AIModelRepository.activate_model(best_model_db.id)
            for info in trained_models_info:
                if info["id"] == best_model_db.id:
                    info["is_active"] = True
                else:
                    info["is_active"] = False
                    
        logger.info("Fin de entrenamiento de modelos.")
        return {
            "version": version,
            "best_model_id": best_model_db.id if best_model_db else None,
            "best_algorithm": best_model_db.algorithm if best_model_db else None,
            "models": trained_models_info
        }
