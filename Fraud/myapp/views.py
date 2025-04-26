import pandas as pd
from django.shortcuts import render
from django.http import HttpResponse
import os
from django.conf import settings
import joblib
import numpy as np
import pandas as pd
from django.conf import settings
import os

def main_page(request):
    return render(request, 'myapp/main.html')

def load_data():
    file_path = os.path.join(settings.BASE_DIR, 'myapp', 'data', 'final_data.csv')
    return pd.read_csv(file_path)

def search_form(request):
    if request.method == 'POST':
        policy_number = request.POST.get('policy_number')
        print("🔹 Policy Number Input:", policy_number)

        data = load_data()
        data.columns = data.columns.str.strip()
        data["Policy_no"] = data["Policy_no"].astype(str)
        policy_number = policy_number.strip()

        filtered_data = data[data["Policy_no"] == policy_number]
        print("🔹 Matching Data:\n", filtered_data)

        if not filtered_data.empty:
            result = filtered_data.to_dict(orient='records')[0]
            print("🔹 Data Sent to Template:", result)
            return render(request, 'myapp/result.html', {'result': result})
        else:
            print("🔹 No matching data found.")
            return HttpResponse("No matching data found.")

    return render(request, 'myapp/search_form.html')
from django.shortcuts import render
from .models import Candidate
import os
import pandas as pd
from django.conf import settings
from django.http import HttpResponse
from datetime import datetime

def format_date(date_str):
    """Convert date string to YYYY-MM-DD format for HTML input."""
    try:
        # Try multiple possible formats if needed
        return datetime.strptime(date_str, "%d-%m-%Y").strftime("%Y-%m-%d")
    except ValueError:
        try:
            return datetime.strptime(date_str, "%d/%m/%Y").strftime("%Y-%m-%d")
        except:
            return ""  # Return empty if not parsable

def fraud_form(request, policy_no):
    file_path = os.path.join(settings.BASE_DIR, 'myapp', 'data', 'final_data.csv')
    data = pd.read_csv(file_path)
    data.columns = data.columns.str.strip()
    data["Policy_no"] = data["Policy_no"].astype(str)

    matched = data[data["Policy_no"] == policy_no].to_dict(orient='records')
    
    if matched:
        record = matched[0]

        prefill = {
            'name': record.get('Name'),
            'age': record.get('Age'),
            'driving_license_no': record.get('Driving_License_No'),
            'engine_no': record.get('Engine_no'),
            'body_type': record.get('Body_type'),
            'vehicle_use': record.get('Vehicle_use'),
            'policy_no': record.get('Policy_no'),
            'policy_start_date': format_date(record.get('Policy_start_date')),
            'policy_End_date': format_date(record.get('Policy_End_date')),
            'type_of_incident': record.get('Type_of_Incident'),
            'price_of_vehicle': record.get('Price_of_vehicle'),
            'market_value': record.get('Market_value')
        }

        return render(request, 'myapp/fraud_form.html', {'prefill': prefill})
    else:
        return HttpResponse("Policy not found.")


def predict_fraud(request):
    if request.method == 'POST':
        form_data = request.POST

        # Collect values from the form
        input_dict = {
            'Type_of_Incident': form_data.get('type_of_incident'),
            'Body_type': form_data.get('body_type'),
            'Driving_license_valid': 1 if form_data.get('driving_license_no') else 0,
            'Drinking': 1 if form_data.get('drinking') == 'Yes' else 0,
            'Eyewitness': 1 if form_data.get('eyewitness') == 'Yes' else 0,
            'Past_claims': 1 if form_data.get('past_claims') == 'Yes' else 0,
            'Substantial_proofs': 1 if form_data.get('substantial_proofs') == 'Yes' else 0,
            'Principal_amt': float(form_data.get('principal_amt', 0)),
            'Claim_amt': float(form_data.get('claim_amt', 0)),
            'Vehicle_age': int(form_data.get('vehicle_age', 0)),
            'Price_of_vehicle': float(form_data.get('price_of_vehicle', 0)),
            'Market_value': float(form_data.get('market_value', 0)),
        }

        # Incident-specific cleanup
        if input_dict["Type_of_Incident"].lower() == "theft":
            input_dict.pop("Drinking", None)
            input_dict.pop("Eyewitness", None)
            input_dict.pop("Past_claims", None)

        # Load model and scaler
        model_path = os.path.join(settings.MODEL_DIR, 'structured_model.pkl')
        scaler_path = os.path.join(settings.MODEL_DIR, 'scaler.pkl')
        iso_forest = joblib.load(model_path)
        scaler = joblib.load(scaler_path)

        # Data prep
        input_df = pd.DataFrame([input_dict])
        input_df = input_df.reindex(columns=scaler.feature_names_in_, fill_value=0)
        input_df = input_df.apply(pd.to_numeric, errors='coerce')
        input_scaled = scaler.transform(input_df)

        # Model prediction
        prediction = iso_forest.predict(input_scaled)
        anomaly_score = iso_forest.decision_function(input_scaled)
        fraud_prob = np.clip((1 - anomaly_score) * 100, 0, 100)

        explanation = None
        status = "Legitimate"

        if input_dict["Claim_amt"] > input_dict["Price_of_vehicle"] and input_dict["Claim_amt"] > input_dict["Market_value"]:
            status = "Fraud"
            explanation = "High Risk: Claim Amount Exceeds Vehicle & Market Value. This is a strong indicator of an inflated or fraudulent claim."

        elif input_dict["Type_of_Incident"].lower() == "theft" and input_dict["Claim_amt"] == input_dict["Market_value"]:
            status = "Verification Needed"
            explanation = "The claim equals the vehicle’s market value. Document verification recommended for authenticity."

        elif input_dict["Driving_license_valid"] == 0:
            status = "Fraud"
            explanation = "High Risk: Driving license is invalid or expired. Claims by unlicensed drivers are considered suspicious."

        elif "Drinking" in input_dict and input_dict["Drinking"] == 1:
            status = "Fraud"
            explanation = "High Risk: Drinking was involved. Such cases often violate insurance policies and raise red flags."

        elif prediction[0] == -1:
            status = "Fraud"
            explanation = "Anomaly detected based on past fraud patterns. System flags this as high-risk."

        else:
            status = "Legitimate"
            explanation = "The claim appears legitimate based on available data."

        result = {
            "prediction": status,
            "fraud_probability": f"{fraud_prob[0]:.2f}",
            "explanation": explanation
        }

        return render(request, 'myapp/fraud_result.html', {'result': result})

    return HttpResponse("Invalid Request")


from django.contrib.auth.decorators import login_required

@login_required
def profile(request):
    return render(request, 'myapp/profile.html')


def admin_dashboard(request):
    result = None
    if request.method == 'POST':
        policy_number = request.POST.get('policy_number')
        data = load_data()
        data.columns = data.columns.str.strip()
        data["Policy_no"] = data["Policy_no"].astype(str)

        filtered = data[data["Policy_no"] == policy_number.strip()]
        if not filtered.empty:
            result = filtered.to_dict(orient='records')[0]
    
    return render(request, 'myapp/admin_dashboard.html', {'result': result})

from django.contrib.auth.decorators import login_required

def user_dashboard(request):
    name = request.session.get('candidate_name')
    policy = request.session.get('candidate_policy_no')
    if name and policy:
        return render(request, 'myapp/user_dashboard.html', {
            'candidate_name': name,
            'candidate_policy_no': policy
        })
    return redirect('login')


from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect

from .models import Candidate
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.shortcuts import redirect, render

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        policy_no = request.POST.get('password')

        # Try authenticating superusers first
        user = authenticate(request, username=username, password=policy_no)
        if user:
            login(request, user)
            if user.is_superuser:
                return redirect('admin_dashboard')
        
        # Now try claimers using Candidate model
        try:
            candidate = Candidate.objects.get(name=username, policy_no=policy_no)
            request.session['candidate_name'] = candidate.name
            request.session['candidate_policy_no'] = candidate.policy_no
            return redirect('user_dashboard')
        except Candidate.DoesNotExist:
            return render(request, 'myapp/login.html', {'error': 'Invalid credentials'})

    return render(request, 'myapp/login.html')



import fitz  # PyMuPDF
import pytesseract
from sklearn.metrics.pairwise import cosine_similarity

def extract_text_from_file(file):
    ext = os.path.splitext(file.name)[1]
    text = ""

    if ext.lower() == ".pdf":
        try:
            pdf = fitz.open(stream=file.read(), filetype="pdf")
            for page in pdf:
                text += page.get_text()
        except:
            text += ""
    else:
        try:
            text += file.read().decode("utf-8")
        except:
            text += ""
    return text.strip()


def predict_fraud(request):
    if request.method == 'POST':
        form_data = request.POST

        # Extract unstructured text inputs
        desc_text = form_data.get('description', '')
        desc_file = request.FILES.get('description_file')
        if desc_file:
            desc_text = extract_text_from_file(desc_file)

        police_text = form_data.get('police_report', '')
        police_file = request.FILES.get('police_report_file')
        if police_file:
            police_text = extract_text_from_file(police_file)

        # Load NLP model + vectorizer
        vectorizer_path = os.path.join(settings.MODEL_DIR, 'tfidf_vectorizer.pkl')
        model_path = os.path.join(settings.MODEL_DIR, 'svm_tfidf_nu003_model.pkl')
        vectorizer = joblib.load(vectorizer_path)
        nlp_model = joblib.load(model_path)

        # Vectorize description
        X_desc = vectorizer.transform([desc_text])
        desc_score = np.clip((1 - nlp_model.decision_function(X_desc.toarray())[0]) * 100, 0, 100)
        nlp_pred = nlp_model.predict(X_desc.toarray())[0]


        # Extract top keywords from TF-IDF
        feature_names = vectorizer.get_feature_names_out()
        tfidf_scores = X_desc.toarray()[0]
        top_indices = np.argsort(tfidf_scores)[::-1][:5]
        top_keywords = [feature_names[i] for i in top_indices if tfidf_scores[i] > 0]

        # Cosine similarity with police report
        X_police = vectorizer.transform([police_text])
        similarity = cosine_similarity(X_desc.toarray(), X_police.toarray())[0][0] * 100


        # Existing structured model logic
        input_dict = {
            'Type_of_Incident': form_data.get('type_of_incident'),
            'Body_type': form_data.get('body_type'),
            'Driving_license_valid': 1 if form_data.get('driving_license_no') else 0,
            'Drinking': 1 if form_data.get('drinking') == 'Yes' else 0,
            'Eyewitness': 1 if form_data.get('eyewitness') == 'Yes' else 0,
            'Past_claims': 1 if form_data.get('past_claims') == 'Yes' else 0,
            'Substantial_proofs': 1 if form_data.get('substantial_proofs') == 'Yes' else 0,
            'Principal_amt': float(form_data.get('principal_amt', 0)),
            'Claim_amt': float(form_data.get('claim_amt', 0)),
            'Vehicle_age': int(form_data.get('vehicle_age', 0)),
            'Price_of_vehicle': float(form_data.get('price_of_vehicle', 0)),
            'Market_value': float(form_data.get('market_value', 0)),
        }

        if input_dict["Type_of_Incident"].lower() == "theft":
            input_dict.pop("Drinking", None)
            input_dict.pop("Eyewitness", None)
            input_dict.pop("Past_claims", None)

        model_path = os.path.join(settings.MODEL_DIR, 'structured_model.pkl')
        scaler_path = os.path.join(settings.MODEL_DIR, 'scaler.pkl')
        iso_forest = joblib.load(model_path)
        scaler = joblib.load(scaler_path)

        input_df = pd.DataFrame([input_dict])
        input_df = input_df.reindex(columns=scaler.feature_names_in_, fill_value=0)
        input_df = input_df.apply(pd.to_numeric, errors='coerce')
        input_df = input_df.fillna(0)
        input_scaled = scaler.transform(input_df)

        prediction = iso_forest.predict(input_scaled)
        anomaly_score = iso_forest.decision_function(input_scaled)
        fraud_prob = np.clip((1 - anomaly_score) * 100, 0, 100)

        status = "Legitimate"
        explanation = None
        if input_dict["Claim_amt"] > input_dict["Price_of_vehicle"] and input_dict["Claim_amt"] > input_dict["Market_value"]:
            status = "Fraud"
            explanation = "Claim exceeds vehicle and market value."
        elif input_dict["Type_of_Incident"].lower() == "theft" and input_dict["Claim_amt"] == input_dict["Market_value"]:
            status = "Verification Needed"
            explanation = "Claim equals market value."
        elif input_dict["Driving_license_valid"] == 0:
            status = "Fraud"
            explanation = "Invalid driving license."
        elif "Drinking" in input_dict and input_dict["Drinking"] == 1:
            status = "Fraud"
            explanation = "Drinking involved."
        elif prediction[0] == -1:
            status = "Fraud"
            explanation = "Anomaly detected."

        # Final Result
        result = {
            "prediction": status,
            "fraud_probability": f"{fraud_prob[0]:.2f}",
            "explanation": explanation or "No specific red flag.",
            "nlp_fraud_score": f"{desc_score:.2f}",
            "nlp_keywords": top_keywords,
            "nlp_similarity": f"{similarity:.2f}",
        }

        return render(request, 'myapp/fraud_result.html', {'result': result})

    return HttpResponse("Invalid Request")




import os
import pandas as pd
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render

def get_estimate(request):
    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.body)
            engine_no = data.get('engine_no', '').strip().upper()
        except Exception:
            return JsonResponse({'error': 'Invalid request data'}, status=400)

        if not engine_no:
            return JsonResponse({'error': 'Engine number cannot be empty.'})

        try:
            csv_path = os.path.join(settings.BASE_DIR, 'myapp', 'data', 'final_data.csv')
            if not os.path.exists(csv_path):
                return JsonResponse({'error': 'CSV file not found.'})
            
            df = pd.read_csv(csv_path)
            df['Engine_no'] = df['Engine_no'].astype(str).str.upper()

            vehicle = df[df['Engine_no'] == engine_no]

            if not vehicle.empty:
                result = {
                    'name': str(vehicle.iloc[0]['Name']),
                    'body_type': str(vehicle.iloc[0]['Body_type']),
                    'market_price': float(vehicle.iloc[0]['Market_value'])
                }
                return JsonResponse(result)
            else:
                return JsonResponse({'error': 'No vehicle found for the given engine number.'})

        except Exception as e:
            return JsonResponse({'error': f'Error: {str(e)}'})

    return JsonResponse({'error': 'Invalid request method.'}, status=405)



# import os
# import pandas as pd
# from django.conf import settings
# from django.shortcuts import render

# def get_estimate(request):
#     if request.method == 'POST':
#         engine_no = request.POST.get('engine_no', '').strip().upper()

#         if not engine_no:
#             return render(request, 'myapp/get_estimate.html', {'error': 'Engine number cannot be empty.'})

#         try:
#             # Adjust path based on your file's actual location
#             csv_path = os.path.join(settings.BASE_DIR, 'myapp', 'data', 'final_data.csv')
#             if not os.path.exists(csv_path):
#                 return render(request, 'myapp/get_estimate.html', {'error': 'CSV file not found.'})
            
#             df = pd.read_csv(csv_path)
#             df['Engine_no'] = df['Engine_no'].astype(str).str.upper()

#             vehicle = df[df['Engine_no'] == engine_no]

#             if not vehicle.empty:
#                 data = {
#                     'name': vehicle.iloc[0]['Name'],
#                     'body_type': vehicle.iloc[0]['Body_type'],
#                     'market_price': vehicle.iloc[0]['Market_value']
#                 }
#                 return render(request, 'myapp/main.html', {'data': data})
#             else:
#                 return render(request, 'myapp/main.html', {'error': 'No vehicle found for the given engine number.'})

#         except Exception as e:
#             return render(request, 'myapp/main.html', {'error': f'Error: {str(e)}'})

#     return render(request, 'myapp/main.html', {'error': 'Invalid request'})


import os
import joblib
import torch
import numpy as np
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect
from transformers import BertTokenizer, BertModel
from .utils import extract_text_from_files

# Load the IsolationForest model
MODEL_PATH = os.path.join(settings.MODEL_DIR,'unstructured_model.pkl')
model = joblib.load(MODEL_PATH)

# Load the BERT model and tokenizer
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
bert_model = BertModel.from_pretrained('bert-base-uncased')
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
bert_model.to(device)

def get_bert_embedding(text):
    """
    Converts a string of text to a BERT embedding (mean pooled).
    """
    inputs = tokenizer(text, return_tensors='pt', truncation=True, max_length=512)
    inputs = {key: val.to(device) for key, val in inputs.items()}
    with torch.no_grad():
        outputs = bert_model(**inputs)
    embedding = outputs.last_hidden_state.mean(dim=1).squeeze().cpu().numpy()
    return embedding

def document_scan_view(request):
    context = {}
    if request.method == 'POST':
        files = request.FILES.getlist('documents')
        if not files:
            messages.error(request, 'Please upload at least one document.')
            return redirect('document_scan')

        texts = extract_text_from_files(files)
        combined = ' '.join(texts)

        try:
            embedding = get_bert_embedding(combined).reshape(1, -1)
            pred = model.predict(embedding)[0]  # -1 = fraud, 1 = normal
            score = model.decision_function(embedding)[0]  # anomaly score

            context = {
                'prediction': 'Fraud' if pred == -1 else 'Genuine',
                'probability': round(score, 2),
                'reason': 'Detected patterns associated with fraud.' if pred == -1 else 'No significant fraud indicators detected.'
            }

        except Exception as e:
            messages.error(request, f'Prediction error: {e}')
            return redirect('document_scan')

    return render(request, 'myapp/document_scan.html', context)



# import os
# import joblib
# from django.shortcuts import render
# from .utils import extract_text_from_files, extract_text_from_image,extract_text_from_pdf

# model = os.path.join(settings.MODEL_DIR, 'unstructured_model.pkl.pkl')

# def document_scan_view(request):
#     if request.method == "POST":
#         files = request.FILES.getlist('documents')
#         file_type = files.content_type.lower() 
#         texts = extract_text_from_files(file_type)

#         combined_text = " ".join(texts)
#         prediction = model.predict([combined_text])[0]
#         probability = model.predict_proba([combined_text])[0][1] * 100

#         context = {
#             'prediction': "Fraud" if prediction == 1 else "Genuine",
#             'probability': round(probability, 2),
#             'details': f"Top keywords, analysis info here...",
#         }
#         return render(request, 'document_scan.html', context)

#     return render(request, 'document_scan.html')


 