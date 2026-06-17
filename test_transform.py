from src.etl_transform_to_db import ETLTransformer
transformer = ETLTransformer()
print("Starting transform...")
res = transformer.transform_data()
print(res)
