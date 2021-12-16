
from brainflow.ml_model import BrainFlowMetrics, BrainFlowClassifiers, BrainFlowModelParams, MLModel


model_params = BrainFlowModelParams(BrainFlowMetrics.RELAXATION, BrainFlowClassifiers.REGRESSION)
model = MLModel(model_params)
model.enable_ml_logger()
model.prepare()
model.release()


model_params = BrainFlowModelParams(BrainFlowMetrics.RELAXATION, BrainFlowClassifiers.REGRESSION)
model = MLModel(model_params)
model.enable_ml_logger()
model.prepare()
model.release()

model_params = BrainFlowModelParams(BrainFlowMetrics.RELAXATION, BrainFlowClassifiers.REGRESSION)
model = MLModel(model_params)
model.enable_ml_logger()
model.prepare()
model.release()
