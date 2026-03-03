from networksecurity.entity.artifact_entity import (
    DataIngestionArtifact,
    DataValidationArtifact
)
from networksecurity.entity.config_entity import DataValidationConfig
from networksecurity.constant.training_pipeline import SCHEMA_FILE_PATH
from networksecurity.exception.exception import NetworkSecurityException

import pandas as pd
import os
import sys
from scipy.stats import ks_2samp
from networksecurity.utils.main_utils.utils import (
    read_yaml_file, write_yaml_file)


class DataValidation:
    def __init__(
        self,
        data_ingestion_artifact: DataIngestionArtifact,
        data_validation_config: DataValidationConfig
    ):
        try:
            self.data_ingestion_artifact = data_ingestion_artifact
            self.data_validation_config = data_validation_config
            self._schema_config = read_yaml_file(str(SCHEMA_FILE_PATH))
        except Exception as e:
            raise NetworkSecurityException(e, sys)

    @staticmethod
    def read_data(file_path: str) -> pd.DataFrame:
        try:
            return pd.read_csv(file_path)
        except Exception as e:
            raise NetworkSecurityException(e, sys)

    def validate_columns(self, dataframe: pd.DataFrame) -> bool:
        try:
            required_columns = [
                list(col.keys())[0] for col in self._schema_config["columns"]
            ]
            actual_columns = dataframe.columns.tolist()

            missing_columns = list(set(required_columns) - set(actual_columns))

            if missing_columns:
                raise Exception(f"Missing columns: {missing_columns}")

            return True

        except Exception as e:
            raise NetworkSecurityException(e, sys)

    def detect_dataset_drift(
        self,
        base_df: pd.DataFrame,
        current_df: pd.DataFrame,
        threshold: float = 0.05
    ) -> bool:

        try:
            status = True
            report = {}

            for column in base_df.columns:

                d1 = base_df[column].dropna()
                d2 = current_df[column].dropna()

                if not pd.api.types.is_numeric_dtype(d1):
                    continue

                if len(d1) == 0 or len(d2) == 0:
                    continue

                if d1.nunique() <= 1 or d2.nunique() <= 1:
                    continue

                ks_test = ks_2samp(d1, d2)
                drift_detected = ks_test.pvalue < threshold

                if drift_detected:
                    status = False

                report[column] = {
                    "p_value": float(ks_test.pvalue),
                    "drift_status": drift_detected
                }

            drift_report_path = (
                self.data_validation_config.drift_report_file_path)
            os.makedirs(os.path.dirname(drift_report_path), exist_ok=True)

            write_yaml_file(
                file_path=drift_report_path,
                content=report
            )

            return status

        except Exception as e:
            raise NetworkSecurityException(e, sys)

    def initiate_data_validation(self) -> DataValidationArtifact:
        try:
            train_path = self.data_ingestion_artifact.trained_file_path
            test_path = self.data_ingestion_artifact.test_file_path

            train_df = self.read_data(train_path)
            test_df = self.read_data(test_path)

            self.validate_columns(train_df)
            self.validate_columns(test_df)

            drift_status = self.detect_dataset_drift(
                base_df=train_df,
                current_df=test_df
            )

            os.makedirs(
                os.path.dirname(
                    self.data_validation_config.valid_train_file_path),
                exist_ok=True
            )

            train_df.to_csv(
                self.data_validation_config.valid_train_file_path,
                index=False
            )

            test_df.to_csv(
                self.data_validation_config.valid_test_file_path,
                index=False
            )

            return DataValidationArtifact(
                validation_status=drift_status,
                valid_train_file_path=(
                    self.data_validation_config.valid_train_file_path),
                valid_test_file_path=(
                    self.data_validation_config.valid_test_file_path),
                invalid_train_file_path=None,
                invalid_test_file_path=None,
                drift_report_file_path=(
                    self.data_validation_config.drift_report_file_path)
            )

        except Exception as e:
            raise NetworkSecurityException(e, sys)
