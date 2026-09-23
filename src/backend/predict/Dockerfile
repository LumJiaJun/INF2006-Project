FROM public.ecr.aws/lambda/python:3.11

COPY analytics/requirements-inference.txt ${LAMBDA_TASK_ROOT}/requirements.txt
RUN pip install --no-cache-dir --requirement ${LAMBDA_TASK_ROOT}/requirements.txt

COPY src/backend/predict/handler.py ${LAMBDA_TASK_ROOT}/handler.py
COPY analytics/artifacts/airbnb_price_model.joblib ${LAMBDA_TASK_ROOT}/model/airbnb_price_model.joblib

ENV MODEL_PATH=${LAMBDA_TASK_ROOT}/model/airbnb_price_model.joblib \
    JOBLIB_MULTIPROCESSING=0

CMD ["handler.lambda_handler"]
