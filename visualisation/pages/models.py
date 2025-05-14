from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO

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
    
    def generate_pdf(self, filename="diagnosis_report.pdf"):
        """Génère un rapport PDF avec les informations du diagnostic"""

        # Créer un buffer pour le PDF
        buffer = BytesIO()

        # Créer le PDF avec ReportLab
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        # Titre du document
        p.setFont("Helvetica", 12)
        p.drawString(100, height - 50, f"Diagnostic Report for {self.image.user.username}")

        # Ajouter les informations du diagnostic
        p.drawString(100, height - 100, f"Patient Username: {self.image.user.username}")
        p.drawString(100, height - 120, f"Image ID: {self.image.id}")
        p.drawString(100, height - 140, f"Patient Age: {self.image.patient_age()}")
        p.drawString(100, height - 160, f"Patient Sex: {self.image.patient_sex()}")
        p.drawString(100, height - 180, f"Condition: {self.condition}")
        p.drawString(100, height - 200, f"Confidence: {self.confidence:.2f}")
        p.drawString(100, height - 220, f"Diagnosis Date: {self.diagnosis_date.strftime('%Y-%m-%d %H:%M:%S')}")

        # Sauvegarder le PDF dans un fichier
        p.showPage()
        p.save()

        # Revenir au début du buffer et sauvegarder le fichier
        buffer.seek(0)
        file_path = os.path.join('pdf_reports', filename)
        with open(file_path, "wb") as f:
            f.write(buffer.read())
        
        buffer.close()
        return file_path
    
    
    
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
        ordering = ['-timestamp']  
    
    def __str__(self):
        return f"{self.user.username} - Image {self.diagnosis.image.id} - {self.diagnosis.condition} ({self.timestamp.strftime('%Y-%m-%d %H:%M')})"