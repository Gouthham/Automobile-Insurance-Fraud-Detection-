import os
import pandas as pd
from datetime import datetime
from django.core.management.base import BaseCommand
from myapp.models import Candidate
from django.conf import settings

class Command(BaseCommand):
    help = 'Load data from final_data.csv into the database'

    def handle(self, *args, **kwargs):
        self.load_dataset()

    def parse_date(self, date_str):
        try:
            return datetime.strptime(date_str, '%d-%m-%Y').date()
        except ValueError:
            return None

    def load_dataset(self):
        file_path = os.path.join(settings.BASE_DIR, "myapp", "data", "final_data.csv")



        print("Loading dataset from:", file_path)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        df = pd.read_csv(file_path)

        df.rename(columns={
            'Type_of_Incident': 'type_of_incident',
            'Damage_Severity': 'damage_severity'
        }, inplace=True)

        for _, row in df.iterrows():
            Candidate.objects.create(
                name=row['Name'],
                age=row['Age'],
                driving_license_no=row['Driving_License_No'],
                engine_no=row['Engine_no'],
                body_type=row['Body_type'],
                vehicle_use=row['Vehicle_use'],
                driving_license_valid=row['Driving_license_valid'] == 'Yes',
                commercial_permit=row['Commercial_permit'] == 'Yes',
                policy_no=row['Policy_no'],
                policy_start_date=self.parse_date(row['Policy_start_date']),
                policy_End_date=self.parse_date(row['Policy_End_date']),
                type_of_incident=row['type_of_incident'],
                damage_severity=row['damage_severity'],
                drinking=row['Drinking'] == 'Yes',
                eyewitness=row['Eyewitness'] == 'Yes',
                past_claims=row['Past_claims'] == 'Yes',
                substantial_proofs=row['Substantial_proofs'] == 'Yes',
                principal_amt=row['Principal_amt'],
                claim_amt=row['Claim_amt'],
                vehicle_age=row['Vehicle_age'],
                price_of_vehicle=row['Price_of_vehicle'],
                market_value=row['Market_value'],
                description=row['description'],
                Police_report=row['Police_Report']
            )

        print("✅ Data successfully loaded into the database!")
