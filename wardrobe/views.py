from django.shortcuts import render
from django.http import HttpResponse

def home(request):
    return HttpResponse("Hello, Capsule Stylist is running!")

# wardrobe/views.py
from django.shortcuts import render, redirect
from .models import Garment
from .services.engine import (
    OutfitEngine, ColorStrategy, SilhouetteStrategy, OccasionStrategy, WeatherGuard,
    ColorPalette, ClimateProfile, Occasion, model_to_dto
)

engine = OutfitEngine(ColorStrategy(), SilhouetteStrategy(), OccasionStrategy(), WeatherGuard())

# simple defaults for now
PALETTE = ColorPalette(
    "spring",
    neutrals=["black","white","beige","camel","navy","ivory"],
    accents=["pink","red","olive","rust","forest"]
)
CLIMATE = ClimateProfile(typical_temp_c=18.0, rainy=False)

def index(request):
    msg = None
    outfits = []
    capsule = []
    occ = request.POST.get("occasion", "WORK")  # WORK / CASUAL / DATE / EVENING / FORMAL

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "add":
            Garment.objects.create(
                name=request.POST["name"],
                category=request.POST["category"],
                color=request.POST["color"].strip().lower(),
                fit=request.POST["fit"],
                formality=int(request.POST["formality"]),
                warmth=int(request.POST["warmth"]),
                price=request.POST.get("price") or 0,
                tags=request.POST.get("tags","")
            )
            return redirect("index")

        items = [model_to_dto(g) for g in Garment.objects.all()]
        if not items:
            msg = "Add a few garments first (top/bottom/shoes or a dress)."
        else:
            occasion = Occasion[occ]
            outfits = engine.propose(items, occasion, PALETTE, CLIMATE)
            if action == "capsule":
                seen = {}
                for o in outfits[:6]:
                    for p in o.pieces:
                        seen[p.name] = p
                capsule = list(seen.values())

    return render(request, "wardrobe/index.html", {
        "items": Garment.objects.all(),
        "outfits": outfits,
        "capsule": capsule,
        "occ": occ,
        "msg": msg
    })
