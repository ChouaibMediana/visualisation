from django.contrib import admin
from .models import User, MedicalImage,Diagnosis, AnalysisHistory

# Personnalisation de l'affichage des modèles dans l'interface d'administration

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email','age','password', 'sex', 'is_active', 'date_joined')
    search_fields = ('username', 'email')


@admin.register(MedicalImage)
class MedicalImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'view_position', 'upload_date')
    list_filter = ('view_position', 'upload_date')
    search_fields = ('user__username', 'view_position')



@admin.register(Diagnosis)
class DiagnosisAdmin(admin.ModelAdmin):
    list_display = ('id', 'condition', 'confidence', 'diagnosis_date')
    list_filter = ('condition', 'diagnosis_date')
    search_fields = ('condition',)


@admin.register(AnalysisHistory)
class AnalysisHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'diagnosis', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('user__username',)