from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator

class User(AbstractUser):
    SEX_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female')
    ]
    
    age = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(120)]
    )
    sex = models.CharField(
        max_length=1,
        choices=SEX_CHOICES,
        default='M',
        null=True,
        blank=True
    )
    def profile(self):
     return {
        "username": self.username,
        "email": self.email,
        "age": self.age,
        "sex": dict(self.SEX_CHOICES).get(self.sex, "Not specified"),
        "first_name": self.first_name,
        "last_name": self.last_name,
     }

    def __str__(self):
        return f"{self.username} {self.age} ans" if self.age else self.username
class MedicalImage(models.Model):
    VIEW_POSITION_CHOICES = [
        ('PA', 'Posteroanterior'),
        ('LAT', 'Lateral'),
        ('AP', 'Anteroposterior'),
        ('OTHER', 'Other'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='medical_images')
    upload_date = models.DateTimeField(auto_now_add=True)
    view_position = models.CharField(max_length=10, choices=VIEW_POSITION_CHOICES)
    image_file = models.ImageField(upload_to='medical_images/%Y/%m/%d/',null=True)
    
    def patient_age(self):
        """Récupère l'âge depuis le profil utilisateur"""
        return self.user.age
    
    def patient_sex(self):
        """Récupère le sexe depuis le profil utilisateur"""
        return self.user.sex

class Diagnosis(models.Model):
    image = models.OneToOneField(MedicalImage, on_delete=models.CASCADE, related_name='diagnosis')
    diagnosis_date = models.DateTimeField(auto_now_add=True)
    condition = models.CharField(max_length=255)
    confidence = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    
    def generate_report(self):
        """Génère un rapport basé sur le diagnostic"""
        return {
            'condition': self.condition,
            'confidence': self.confidence,
            'diagnosis_date': self.diagnosis_date,
            'image_id': self.image.id,
            'patient': self.image.user.username
        }
    
    
    
    def __str__(self):
        return f"Diagnosis for Image {self.image.id}"    
    
    class Meta:
        db_table = 'diagnoses'


class AnalysisHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analysis_history')
    diagnosis = models.ForeignKey(Diagnosis, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Analysis Histories"
    
    def __str__(self):
        return f"History {self.id} - User {self.user.username}"