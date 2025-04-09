
# Register your models here.
from django.contrib import admin
from .models import Candidate

admin.site.register(Candidate)
class ClaimAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'policy_no', 'claim_amt', 'vehicle_age', 'police_report')
    search_fields = ('name', 'policy_no', 'driving_license_no')
    list_filter = ('drinking', 'multiple_insurance', 'past_claims')
    ordering = ('-id',)