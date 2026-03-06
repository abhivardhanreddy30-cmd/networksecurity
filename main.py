import sys
from networksecurity.components.data_ingestion import DataIngestion
from networksecurity.components.data_validation import DataValidation
from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging
from networksecurity.entity.config_entity import DataIngestionConfig
from networksecurity.entity.config_entity import DataValidationConfig
from networksecurity.entity.config_entity import TrainingPipelineConfig
from networksecurity.components.data_transformation import DataTransformation
from networksecurity.entity.config_entity import DataTransformationConfig
from networksecurity.components.model_trainer import ModelTrainer
from networksecurity.entity.config_entity import ModelTrainerConfig

if __name__ == "__main__":
    try:
        traningpipelineconfig = TrainingPipelineConfig()
        dataingestionconfig = DataIngestionConfig(traningpipelineconfig)
        data_ingestion = DataIngestion(dataingestionconfig)
        logging.info('Initiate Data Ingestion')
        dataingestionartifact = data_ingestion.initiate_data_ingestion()
        logging.info('Data initiation completed')
        print(dataingestionartifact)
        data_validation_config = DataValidationConfig(traningpipelineconfig)
        data_validation = DataValidation(
            dataingestionartifact, data_validation_config)
        logging.info('Initiate Data Validation')
        data_validation_artifact = data_validation.initiate_data_validation()
        logging.info('Data validation completed')
        print(data_validation_artifact)
        data_transformation_config = DataTransformationConfig(
            traningpipelineconfig)

        data_transformation = DataTransformation(
            data_validation_artifact,
            data_transformation_config
            )
        logging.info("Initiate Data Transformation")
        data_transformation_artifact = (
            data_transformation.initiate_data_transformation())
        logging.info("Data Transformation Completed")
        print(data_transformation_artifact)
        model_trainer_config = ModelTrainerConfig(traningpipelineconfig)

        model_trainer = ModelTrainer(
            data_transformation_artifact,
            model_trainer_config
            )

        logging.info("Initiate Model Trainer")

        model_trainer_artifact = model_trainer.initiate_model_trainer()

        logging.info("Model Training Completed")

        print(model_trainer_artifact)
    except Exception as e:
        raise NetworkSecurityException(e, sys)
