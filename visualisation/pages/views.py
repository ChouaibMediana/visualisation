from django.http import JsonResponse
from django.contrib.auth import login , authenticate , logout
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from .forms import UserRegistrationForm , MedicalImageUploadForm
from .models import AnalysisHistory
import json

@csrf_exempt
@require_http_methods(["POST"])  # Only allow POST requests
def register(request):
    try:
        # Try to parse JSON data if Content-Type is application/json
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                form = UserRegistrationForm(data)
            except json.JSONDecodeError:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid JSON data'
                }, status=400)
        else:
            # Fall back to regular form data
            form = UserRegistrationForm(request.POST)
        
        if form.is_valid():
            user = form.save()
            
            # Automatically log in the user
            login(request, user)
            
            return JsonResponse({
                'status': 'success',
                'user_id': user.id,
                'username': user.username,
                'email': user.email
            }, status=201)  # 201 Created for successful resource creation
        
        # Return form errors if invalid
        return JsonResponse({
            'status': 'error',
            'errors': form.errors
        }, status=400)
        
    except Exception as e:
        
        return JsonResponse({
            'status': 'error',
            'message': 'An unexpected error occurred'
        }, status=500)
    

@csrf_exempt
@require_http_methods(["POST"])
def user_login(request):
    try:
        # Parse JSON data
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data'
            }, status=400)

        # Validation basique
        if not username or not password:
            return JsonResponse({
                'status': 'error',
                'message': 'Username and password are required'
            }, status=400)

        # Authentification
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return JsonResponse({
                'status': 'success',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'age': user.age,
                    'sex': user.get_sex_display() if hasattr(user, 'sex') else None
                }
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid credentials'
            }, status=401)

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Server error: {str(e)}'
        }, status=500)
@login_required   
@require_http_methods(["POST"])
@csrf_exempt
def user_logout(request):
    try:
        logout(request)
        return JsonResponse({
            'status': 'success',
            'message': 'Logged out successfully'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Logout failed: {str(e)}'
        }, status=500)

#@login_required
@csrf_exempt
@require_http_methods(["POST"])
def upload_medical_image(request):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Authentication required'}, status=401)

    form = MedicalImageUploadForm(request.POST, request.FILES)
    if form.is_valid():
        try:
            medical_image = form.save(commit=False)
            medical_image.user = request.user  # Associe automatiquement l'utilisateur
            
            # Maintenant patient_age() et patient_sex() seront disponibles via les méthodes
            medical_image.save()
            
            # procees image les function de resize normalisation et aussi le predictio gere le modele ann dans service monsieur RIDA
          #  diagnosis = process_image(medical_image)
            
            AnalysisHistory.objects.create(
                user=request.user,
                #diagnosis=diagnosis
            )
            
            return JsonResponse({
                'status': 'success',
                'image_id': medical_image.id,
                'patient_age': medical_image.patient_age(),  # Appel de la méthode
                'patient_sex': medical_image.patient_sex(),  # Appel de la méthode
              #  'diagnosis_id': diagnosis.id
            })
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)