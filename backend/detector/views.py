from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import joblib

# Load model and vectorizer
MODEL = joblib.load("models/model.pkl")
VECTORIZER = joblib.load("models/vectorizer.pkl")

@csrf_exempt
def analyze_extension(request):
    if request.method == 'POST':
        uploadedFile = request.FILES.get('file')
        if not uploadedFile:
            return JsonResponse({"error": "No file uploaded"}, status=400)
        
        try:
            # here is where the file is uploaded and read
            text = uploadedFile.read().decode('utf-8')
            
            # prediction logic applied here
            X = VECTORIZER.transform([text])
            prediction = MODEL.predict(X)[0]
            result = "Malicious" if prediction == 1 else "Benign"
            
            return JsonResponse({"result": result})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)