import os
import sys
import numpy as np

from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC

from sklearn.model_selection import GridSearchCV
from sklearn.metrics import accuracy_score

from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging

from networksecurity.entity.config_entity import ModelTrainerConfig
from networksecurity.entity.artifact_entity import (
    DataTransformationArtifact,
    ModelTrainerArtifact
)
from networksecurity.utils.main_utils.utils import save_object
import mlflow
import mlflow.sklearn
mlflow.set_tracking_uri("http://127.0.0.1:5000")
mlflow.set_experiment("networksecurity_experiment")


class ModelTrainer:

    def __init__(
        self,
        data_transformation_artifact: DataTransformationArtifact,
        model_trainer_config: ModelTrainerConfig
    ):
        try:
            self.data_transformation_artifact = data_transformation_artifact
            self.model_trainer_config = model_trainer_config
        except Exception as e:
            raise NetworkSecurityException(e, sys)

    def track_mlflow(self, model, accuracy, model_name, params):

        with mlflow.start_run():

            mlflow.log_param("model_name", model_name)

            for param, value in params.items():
                mlflow.log_param(param, value)

            mlflow.log_metric("accuracy", accuracy)

        mlflow.sklearn.log_model(model, "model")

    def initiate_model_trainer(self) -> ModelTrainerArtifact:

        try:

            logging.info("Loading transformed train and test arrays")

            train_arr = np.load(
                self.data_transformation_artifact.transformed_train_file_path
            )

            test_arr = np.load(
                self.data_transformation_artifact.transformed_test_file_path
            )

            X_train = train_arr[:, :-1]
            y_train = train_arr[:, -1]

            X_test = test_arr[:, :-1]
            y_test = test_arr[:, -1]

            models = {

                "LogisticRegression": LogisticRegression(),

                "DecisionTree": DecisionTreeClassifier(),

                "RandomForest": RandomForestClassifier(),

                "GradientBoosting": GradientBoostingClassifier(),

                "KNN": KNeighborsClassifier(),

                "SVM": SVC()

            }

            params = {

                "LogisticRegression": {
                    "C": [0.01, 0.1, 1, 10]
                },

                "DecisionTree": {
                    "max_depth": [5, 10, 20]
                },

                "RandomForest": {
                    "n_estimators": [50, 100],
                    "max_depth": [10, 20]
                },

                "GradientBoosting": {
                    "learning_rate": [0.01, 0.1],
                    "n_estimators": [100, 200]
                },

                "KNN": {
                    "n_neighbors": [3, 5, 7]
                },

                "SVM": {
                    "C": [0.1, 1, 10],
                    "kernel": ["rbf", "linear"]
                }
            }

            best_model = None
            best_score = 0

            for model_name, model in models.items():

                logging.info(f"Training model: {model_name}")

                grid_search = GridSearchCV(
                    model,
                    params[model_name],
                    cv=3,
                    scoring="accuracy"
                )

                grid_search.fit(X_train, y_train)

                best_estimator = grid_search.best_estimator_

                y_pred = best_estimator.predict(X_test)

                accuracy = accuracy_score(y_test, y_pred)

                logging.info(f"{model_name} accuracy: {accuracy}")

                # MLflow tracking
                self.track_mlflow(
                    best_estimator,
                    accuracy,
                    model_name,
                    grid_search.best_params_
                    )

                if accuracy > best_score:
                    best_score = accuracy
                    best_model = best_estimator

            logging.info(f"Best model accuracy: {best_score}")

            os.makedirs(
                os.path.dirname(
                    self.model_trainer_config.trained_model_file_path
                ),
                exist_ok=True
            )

            save_object(
                self.model_trainer_config.trained_model_file_path,
                best_model
            )

            model_trainer_artifact = ModelTrainerArtifact(
                trained_model_file_path=(
                    self.model_trainer_config.trained_model_file_path),
                train_accuracy=best_score,
                test_accuracy=best_score
            )

            return model_trainer_artifact

        except Exception as e:
            raise NetworkSecurityException(e, sys)
