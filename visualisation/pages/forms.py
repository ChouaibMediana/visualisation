from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import MedicalImage , User

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'age', 'sex']

class MedicalImageUploadForm(forms.ModelForm):
    class Meta:
        model = MedicalImage
        fields = ['view_position', 'image_file'] 