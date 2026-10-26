import os

import requests
from PIL import Image
from django.conf import settings
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.cache import never_cache
from django.contrib import messages
from .models import Exposure, Location, Plant, Diagnostic

from .models import Plant


MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 Mo
ALLOWED_EXTENSIONS = ('.jpg', '.jpeg', '.png')

@never_cache
def view_dashboard(request):
    user_id = request.session.get('user_id')
    if user_id is None:
        return redirect('login')
    
    plants = (
        Plant.objects
        .filter(user_id=user_id)
        .select_related('exposure', 'location') 
        .prefetch_related('diagnostics')
    )
    
    for plant in plants:
        last = plant.diagnostics.order_by('-created_at').first()
        plant.last_diagnostic_data = last.created_at if last else None
        if last is None:
            plant.status = "warning"
        elif last.result.lower() in ('sain', 'healthy'):
            plant.status = "healthy"
        else:
            plant.status = "danger"
    
    return render(request, "dashboard/dashboard.html", {"plants": plants})

@never_cache
def add_plant(request):
    user_id = request.session.get('user_id')
    if user_id is None:
        return redirect('login')
    
    if request.method == "POST":
        name = request.POST.get('name', '').strip()
        plant_type = request.POST.get('plant_type', '').strip()
        exposure_id = request.POST.get('exposure', '')
        location_id = request.POST.get('location', '')
        
        exposure = Exposure.objects.filter(pk=exposure_id).first() if exposure_id.isdigit() else None
        location = Location.objects.filter(pk=location_id).first() if location_id.isdigit() else None
        
        if not name or not plant_type or exposure is None or location is None:
            messages.error(request, "Tout les champs sont obligatoires. ")
            return redirect('dashboard:add_plant')
        
        Plant.objects.create(
            name=name,
            plant_type=plant_type,
            user_id=user_id,
            exposure=exposure,
            location=location,    
        )
        messages.success(request, "Plante ajoutée. ")
        return redirect('dashboard:dashboard')
    
    return render(request, "dashboard/add_plant.html", {
        "exposures": Exposure.objects.all(),
        "locations": Location.objects.all(),
    })



@never_cache
def add_diagnostic(request, plant_id):
    user_id = request.session.get('user_id')
    if user_id is None:
        return redirect('login')

    # 404 si la plante n'existe pas OU n'appartient pas à l'utilisateur connecté
    plant = get_object_or_404(Plant, pk=plant_id, user_id=user_id)

    if request.method == "POST":
        image = request.FILES.get('image')

        if image is None:
            messages.error(request, "Choisis une photo.")
            return redirect('dashboard:add_diagnostic', plant_id=plant.id)

        extension = os.path.splitext(image.name)[1].lower()
        if extension not in ALLOWED_EXTENSIONS:
            messages.error(request, "Format refusé : utilise un fichier JPG ou PNG.")
            return redirect('dashboard:add_diagnostic', plant_id=plant.id)

        if image.size > MAX_IMAGE_SIZE:
            messages.error(request, "Image trop lourde (5 Mo maximum).")
            return redirect('dashboard:add_diagnostic', plant_id=plant.id)

        try:
            Image.open(image).verify()
        except Exception:
            messages.error(request, "Ce fichier n'est pas une image valide.")
            return redirect('dashboard:add_diagnostic', plant_id=plant.id)

        # On garde le contenu en mémoire pour l'envoyer au service IA
        image.seek(0)
        contenu = image.read()
        image.seek(0)

        diagnostic = Diagnostic.objects.create(plant=plant, image=image)

        # Appel du service IA
        try:
            reponse = requests.post(
                f"{settings.AI_SERVICE_URL}/predict",
                files={"file": (image.name, contenu, image.content_type)},
                timeout=60,
            )
            reponse.raise_for_status()
            analyse = reponse.json()
        except (requests.RequestException, ValueError):
            messages.warning(
                request,
                "Photo enregistrée, mais le service d'analyse est indisponible. Réessaie plus tard.",
            )
            return redirect('dashboard:dashboard')

        conseil = analyse.get("advice", "")
        if analyse.get("warning"):
            conseil = f"{conseil} {analyse['warning']}"

        diagnostic.result = analyse.get("result", "")
        diagnostic.confidence = analyse.get("confidence")
        diagnostic.advice = conseil
        diagnostic.save()

        messages.success(request, "Analyse terminée.")
        return redirect('dashboard:dashboard')

    return render(request, "dashboard/add_diagnostic.html", {"plant": plant})

@never_cache
def plant_history(request, plant_id):
    user_id = request.session.get('user_id')
    if user_id is None:
        return redirect('login')

    # 404 si la plante n'est pas à l'utilisateur connecté
    plant = get_object_or_404(Plant, pk=plant_id, user_id=user_id)

    diagnostics = list(plant.diagnostics.order_by('-created_at'))
    for d in diagnostics:
        d.percent = round(d.confidence * 100, 1) if d.confidence is not None else None

    return render(request, "dashboard/plant_history.html", {
        "plant": plant,
        "diagnostics": diagnostics,
    })
    
@require_POST
def delete_plant(request, plant_id):
    user_id = request.session.get('user_id')
    if user_id is None:
        return redirect('login')

    # 404 si la plante n'est pas à l'utilisateur connecté
    plant = get_object_or_404(Plant, pk=plant_id, user_id=user_id)

    # On supprime aussi les fichiers photo du disque (RGPD)
    for diagnostic in plant.diagnostics.all():
        diagnostic.image.delete(save=False)

    plant.delete()  # les diagnostics sont supprimés avec la plante (CASCADE)
    messages.success(request, "Plante supprimée.")
    return redirect('dashboard:dashboard')