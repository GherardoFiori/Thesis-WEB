import os
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
import joblib
from src.dataProcess import preprocessData

def trainModel(dataDirectory, savedModelPath):

    # Safety check for existing model save path
    os.makedirs(os.path.dirname(savedModelPath), exist_ok=True)

    # Preprocess the data
    X_train, X_test, y_train, y_test, vectorizer = preprocessData(dataDirectory)

    model = LogisticRegression()
    model.fit(X_train, y_train)

    # Evaluate the model
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Model Accuracy: {accuracy * 100:.2f}%")

    # Save the model and vectorizer
    joblib.dump(model, savedModelPath)
    joblib.dump(vectorizer, "models/vectorizer.pkl")
    print(f"Model saved to {savedModelPath}")