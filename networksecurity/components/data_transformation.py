import os
import sys
import numpy as np
import pandas as pd
from sklearn.impute import KNNImputer
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.entity.config_entity import DataTransformationConfig
from networksecurity.entity.artifact_entity import (
    DataValidationArtifact,
    DataTransformationArtifact
)
from networksecurity.constant.training_pipeline import (
    DATA_TRANSFORMATION_INPUT_PARAMS
)
from networksecurity.utils.main_utils.utils import (
    save_numpy_array_data,
    save_object
)


class DataTransformation:

    def __init__(self,
                 data_validation_artifact: DataValidationArtifact,
                 data_transformation_config: DataTransformationConfig):

        try:
            self.data_validation_artifact = data_validation_artifact
            self.data_transformation_config = data_transformation_config
        except Exception as e:
            raise NetworkSecurityException(e, sys)

    def get_data_transformer_object(self):

        try:

            imputer = KNNImputer(**DATA_TRANSFORMATION_INPUT_PARAMS)

            scaler = StandardScaler()

            pipeline = Pipeline([
                ("imputer", imputer),
                ("scaler", scaler)
            ])

            return pipeline

        except Exception as e:
            raise NetworkSecurityException(e, sys)

    def initiate_data_transformation(self) -> DataTransformationArtifact:

        try:

            train_df = pd.read_csv(
                self.data_validation_artifact.valid_train_file_path
            )

            test_df = pd.read_csv(
                self.data_validation_artifact.valid_test_file_path
            )

            target_column = "label"

            numeric_columns = train_df.select_dtypes(
                include=["int64", "float64"]).columns

            input_feature_train_df = train_df[numeric_columns].drop(
                columns=[target_column])
            target_feature_train_df = train_df[target_column]

            input_feature_test_df = test_df[numeric_columns].drop(
                columns=[target_column])
            target_feature_test_df = test_df[target_column]

            preprocessing_obj = self.get_data_transformer_object()

            input_feature_train_arr = preprocessing_obj.fit_transform(
                input_feature_train_df
            )

            input_feature_test_arr = preprocessing_obj.transform(
                input_feature_test_df
            )

            train_arr = np.c_[
                input_feature_train_arr,
                np.array(target_feature_train_df)
            ]

            test_arr = np.c_[
                input_feature_test_arr,
                np.array(target_feature_test_df)
            ]

            os.makedirs(
                os.path.dirname(
                    self.data_transformation_config.transformed_train_file_path
                ),
                exist_ok=True
            )

            save_numpy_array_data(
                self.data_transformation_config.transformed_train_file_path,
                train_arr
                )

            save_numpy_array_data(
                self.data_transformation_config.transformed_test_file_path,
                test_arr
                )
            os.makedirs(
                os.path.dirname(
                    self.data_transformation_config.
                    preprocessed_object_file_path
                ),
                exist_ok=True
            )
            save_object(
                self.data_transformation_config.preprocessed_object_file_path,
                preprocessing_obj
                )

            data_transformation_artifact = DataTransformationArtifact(
                transformed_train_file_path=(
                    self.data_transformation_config.
                    transformed_train_file_path),
                transformed_test_file_path=(
                    self.data_transformation_config.
                    transformed_test_file_path),
                preprocessor_object_file_path=(
                    self.data_transformation_config.
                    preprocessed_object_file_path)
            )

            return data_transformation_artifact

        except Exception as e:
            raise NetworkSecurityException(e, sys)
