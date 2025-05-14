from django.http import JsonResponse
from django.contrib.auth import login , authenticate , logout
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from .forms import UserRegistrationForm , MedicalImageUploadForm
from .models import AnalysisHistory , Diagnosis
import numpy as np
import json
from keras.models import load_model
import os
from skimage.transform import resize
from skimage.io import imread, imshow

current_dir = os.path.dirname(__file__)
model_dir = os.path.abspath(os.path.join(current_dir, '..', 'ModelANN'))
model_path = os.path.join(model_dir, 'imageclassifier.keras')  # Using .keras format

model = load_model(model_path)

@csrf_exempt
@require_http_methods(["POST"])
def register(request):
    try:
        print(f"Request body: {request.body}")  # Log du corps de la requête
        
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                print(f"Parsed data: {data}") 
            except json.JSONDecodeError:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid JSON data. Please check your JSON format.'
                }, status=400)
            
            form = UserRegistrationForm(data)
        else:
            form = UserRegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return JsonResponse({
                'status': 'success',
                'user_id': user.id,
                'username': user.username,
                'email': user.email
            }, status=201)

        return JsonResponse({
            'status': 'error',
            'errors': form.errors
        }, status=400)

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
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
            # Sauvegarde de l’image médicale sans encore enregistrer le diagnostic
            medical_image = form.save(commit=False)
            medical_image.user = request.user
            medical_image.save()

            # Traitement et diagnostic
            diagnosis = process_image(medical_image.image_file.path, request.user, medical_image)

            # Historique d’analyse
            AnalysisHistory.objects.create(
                user=request.user,
                diagnosis=diagnosis
            )

            return JsonResponse({
                'status': 'success',
                'username': medical_image.user.username,
                'image_id': medical_image.id,
                'patient_age': medical_image.patient_age(),
                'patient_sex': medical_image.patient_sex(),
                'diagnosis_id': diagnosis.id,
                'condition': diagnosis.condition,
                'confidence': diagnosis.confidence
            })

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)



def process_image(path, user, medical_image):
    # Charger et prétraiter l'image
    img = imread(path, as_gray=True)
    img_res = resize(img, (64, 64), anti_aliasing=True)
    img_flat = img_res.flatten() / 255.0

    # S'assurer que la forme est (1, 4096)
    img_input = np.expand_dims(img_flat, axis=0)  # shape devient (1, 4096)

    # Prédiction
    prediction_proba = model.predict(img_input)[0]
    prediction_index = int(np.round(prediction_proba))  # sigmoid → arrondi à 0 ou 1
    confidence = float(prediction_proba)

    # Mapper la prédiction à un label
    labels = {0: "normal", 1: "pneumonia"}
    condition = labels.get(prediction_index, "unknown")

    # Créer l'objet Diagnosis (Django)
    diagnosis = Diagnosis.objects.create(
        image=medical_image,
        condition=condition,
        confidence=confidence
    )

    return diagnosis



def download_diagnosis_pdf(request, diagnosis_id):
    # Récupérer l'objet Diagnosis en fonction de l'ID
    diagnosis = get_object_or_404(Diagnosis, id=diagnosis_id)

    # Générer le PDF
    pdf_filename = f"diagnosis_report_{diagnosis_id}.pdf"
    pdf_path = diagnosis.generate_pdf(pdf_filename)

    # Lire le fichier PDF et le retourner dans la réponse
    with open(pdf_path, "rb") as f:
        response = HttpResponse(f.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{pdf_filename}"'
        return response




@csrf_exempt
@require_http_methods(["GET"])
#@login_required  
    try:
        user = request.user  # Récupère l'utilisateur connecté depuis la session
        history_entries = AnalysisHistory.objects.filter(user=user)\
                              .select_related('diagnosis', 'diagnosis__image')\
                              .order_by('-diagnosis__diagnosis_date')
        
        data = {
            'username': user.username,
            'history': [
                {
                    'upload_date': entry.diagnosis.image.upload_date.strftime('%Y-%m-%d %H:%M'),
                    'condition': entry.diagnosis.condition,
                    'image_url': request.build_absolute_uri(entry.diagnosis.image.image_file.url) 
                                 if entry.diagnosis.image.image_file else None,
                    'image_id': entry.diagnosis.image.id
                }
                for entry in history_entries
                if hasattr(entry, 'diagnosis') and entry.diagnosis and hasattr(entry.diagnosis, 'image')
            ]
        }
        
        return JsonResponse(data)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)