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

        # ---------------------------
        # RULE-BASED EXPLANATION LOGIC
        # ---------------------------
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
