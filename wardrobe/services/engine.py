# wardrobe/services/engine.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict
from enum import Enum

# ===== Domain (DTOs & Enums) =====

class Category(Enum):
    TOP="TOP"; BOTTOM="BOTTOM"; DRESS="DRESS"; OUTERWEAR="OUTERWEAR"; SHOES="SHOES"; BAG="BAG"

class Occasion(Enum):
    CASUAL="casual"; WORK="work"; EVENING="evening"; FORMAL="formal"; DATE="date"

@dataclass
class ColorPalette:
    season: str
    neutrals: List[str]
    accents: List[str]

@dataclass
class ClimateProfile:
    typical_temp_c: float
    rainy: bool=False

@dataclass
class GarmentDTO:
    name: str
    category: Category
    color: str
    fit: str
    formality: int
    warmth: int
    price: float
    tags: List[str]

# ===== Strategies =====

class ColorStrategy:
    COMPLEMENTS = {"navy":"rust","rust":"navy","black":"white","white":"black",
                   "beige":"forest","forest":"beige","pink":"olive","olive":"pink","red":"camel","camel":"red"}
    def compatible(self, a: str, b: str, palette: ColorPalette) -> bool:
        a,b=a.lower(),b.lower()
        if a==b: return True                 # monochrome
        if a in palette.neutrals or b in palette.neutrals: return True
        return self.COMPLEMENTS.get(a)==b or self.COMPLEMENTS.get(b)==a

class SilhouetteStrategy:
    def top_ok_with_bottom(self, top: GarmentDTO, bottom: GarmentDTO) -> bool:
        if bottom.fit in ("relaxed","oversized") and top.fit=="fitted": return True
        if bottom.fit=="fitted" and top.fit in ("relaxed","oversized"): return True
        if bottom.fit=="tailored" and top.fit in ("fitted","tailored"): return True
        return top.fit==bottom.fit  # fallback

class OccasionStrategy:
    def ok(self, pieces: List[GarmentDTO], occasion: Occasion) -> bool:
        need = {Occasion.CASUAL:1, Occasion.WORK:3, Occasion.EVENING:3, Occasion.FORMAL:4, Occasion.DATE:2}[occasion]
        avg = sum(p.formality for p in pieces)/len(pieces)
        if occasion==Occasion.FORMAL and any("sneaker" in p.tags for p in pieces): return False
        return avg >= need - 0.3

class WeatherGuard:
    def ok(self, pieces: List[GarmentDTO], climate: ClimateProfile) -> bool:
        warmth = sum(p.warmth for p in pieces)
        if climate.typical_temp_c <= 10 and warmth < 6: return False
        if climate.typical_temp_c >= 24 and warmth > 8: return False
        if climate.rainy and any("suede" in p.tags for p in pieces): return False
        return True

# ===== Outfit Engine =====

@dataclass
class Outfit:
    pieces: List[GarmentDTO]
    score: float
    notes: str

class OutfitEngine:
    def __init__(self, color: ColorStrategy, silhouette: SilhouetteStrategy, occasion: OccasionStrategy, weather: WeatherGuard):
        self.color=color; self.silhouette=silhouette; self.occasion=occasion; self.weather=weather

    def propose(self, items: List[GarmentDTO], occ: Occasion, palette: ColorPalette, climate: ClimateProfile) -> List[Outfit]:
        # group by category
        by_cat: Dict[Category, List[GarmentDTO]] = {c:[] for c in Category}
        for it in items: by_cat[it.category].append(it)

        outfits: List[Outfit] = []

        # Dress looks
        for d in by_cat[Category.DRESS]:
            for sh in by_cat[Category.SHOES]:
                pieces=[d, sh] + (by_cat[Category.BAG][:1] if by_cat[Category.BAG] else [])
                if self.occasion.ok(pieces, occ) and self.weather.ok(pieces, climate):
                    outfits.append(Outfit(pieces, self._score([d.color, sh.color], palette), "dress look"))

        # Top+Bottom looks
        for t in by_cat[Category.TOP]:
            for b in by_cat[Category.BOTTOM]:
                if not self.silhouette.top_ok_with_bottom(t, b): continue
                if not self.color.compatible(t.color, b.color, palette): continue
                for sh in by_cat[Category.SHOES]:
                    pieces=[t,b,sh]
                    if self.occasion.ok(pieces, occ) and self.weather.ok(pieces, climate):
                        outfits.append(Outfit(pieces, self._score([t.color,b.color,sh.color], palette), "separates look"))

        # bonus outerwear/bag
        enriched: List[Outfit] = []
        for o in outfits:
            best=o
            if by_cat[Category.OUTERWEAR]:
                ow = by_cat[Category.OUTERWEAR][0]
                if self.color.compatible(ow.color, o.pieces[0].color, palette):
                    new = o.pieces+[ow]
                    if self.weather.ok(new, climate): best = Outfit(new, o.score+0.2, o.notes+" + outerwear")
            if by_cat[Category.BAG]:
                best = Outfit(best.pieces+[by_cat[Category.BAG][0]], best.score+0.1, best.notes+" + bag")
            enriched.append(best)

        enriched.sort(key=lambda x: x.score, reverse=True)
        return enriched[:12]

    def _score(self, colors: List[str], palette: ColorPalette) -> float:
        s=0.0
        for c in colors:
            if c in palette.neutrals: s+=0.6
            if c in palette.accents: s+=0.8
        if len(set(colors))>=2: s+=0.2
        return round(s/(len(colors)+1e-4), 2)

# ===== Adapters (Django model -> DTO) =====
def model_to_dto(m) -> GarmentDTO:
    tags = [t.strip().lower() for t in (m.tags or "").split(",") if t.strip()]
    return GarmentDTO(
        name=m.name, category=Category[m.category], color=m.color.lower(),
        fit=m.fit, formality=int(m.formality), warmth=int(m.warmth),
        price=float(m.price or 0), tags=tags
    )
