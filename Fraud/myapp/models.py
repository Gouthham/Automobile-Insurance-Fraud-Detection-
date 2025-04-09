from django.db import models

# Create your models here.

class Candidate(models.Model):
    name = models.CharField(max_length=255)
    age = models.IntegerField()
    driving_license_no = models.CharField(max_length=50)
    engine_no = models.CharField(max_length=50)
    body_type = models.CharField(max_length=50)  # Changed to CharField
    vehicle_use = models.CharField(max_length=50)
    driving_license_valid = models.BooleanField()
    commercial_permit = models.BooleanField()
    policy_no = models.CharField(max_length=50)
    policy_start_date = models.DateField()
    policy_End_date = models.DateField()  # Fixed casing  # If manually assigned
    type_of_incident = models.CharField(max_length=100)  # Added field
    damage_severity = models.CharField(max_length=50)  # Added field
    drinking = models.BooleanField()
  # Yes/No for police report, fixed name
    eyewitness = models.BooleanField()
    past_claims = models.BooleanField()
    substantial_proofs = models.BooleanField()
    principal_amt = models.DecimalField(max_digits=10, decimal_places=2)
    claim_amt = models.DecimalField(max_digits=10, decimal_places=2)
    vehicle_age = models.IntegerField()
    price_of_vehicle = models.DecimalField(max_digits=15, decimal_places=2)
    market_value = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.CharField(max_length=500)
    Police_Report=models.CharField(max_length=500)
    
    

    def __str__(self):
        return f"Claim {self.name} - {self.claim_amt}"
