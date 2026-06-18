from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from src.database.connection import get_db
from src.modules.testimonials import models, schemas

router = APIRouter()

SEED_TESTIMONIALS = [
    {
        "name": "Dr. Sarah Johnson",
        "role": "Chief Surgeon",
        "content": "The quality of the surgical equipment from MediStore is unparalleled. Their precision tools have significantly improved our efficiency.",
        "rating": 5,
        "image": "https://images.unsplash.com/photo-1559839734-2b71f1e3c7e5?auto=format&fit=crop&q=80&w=200"
    },
    {
        "name": "Mark Thompson",
        "role": "Clinic Administrator",
        "content": "MediStore's customer service and reliable delivery schedules make them our go-to partner for all our diagnostic equipment needs.",
        "rating": 5,
        "image": "https://images.unsplash.com/photo-1537368910025-700350fe46c7?auto=format&fit=crop&q=80&w=200"
    },
    {
        "name": "Emma Williams",
        "role": "Home Care Specialist",
        "content": "The home care medical devices are user-friendly and very accurate. It has made monitoring patients remotely a much smoother process.",
        "rating": 4,
        "image": "https://images.unsplash.com/photo-1594824476967-48c8b964273f?auto=format&fit=crop&q=80&w=200"
    },
    {
        "name": "Dr. James Wilson",
        "role": "Pediatrician",
        "content": "We've been using their thermometers and scales for over a year. The durability is impressive even with high patient volume.",
        "rating": 5,
        "image": "https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?auto=format&fit=crop&q=80&w=200"
    },
    {
        "name": "Linda Chen",
        "role": "Nursing Director",
        "content": "The safety standards on their hospital beds and mobility equipment are top-tier. Our staff finds them very easy to operate safely.",
        "rating": 5,
        "image": "https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&q=80&w=200"
    },
    {
        "name": "Robert Davis",
        "role": "Laboratory Manager",
        "content": "High-quality microscopes and lab gear. The technical support team helped us set everything up within 24 hours of delivery.",
        "rating": 5,
        "image": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?auto=format&fit=crop&q=80&w=200"
    }
]

@router.get("/", response_model=List[schemas.TestimonialResponse])
def get_testimonials(db: Session = Depends(get_db)):
    count = db.query(models.Testimonial).count()
    if count == 0:
        # Seed initial testimonials
        for t_data in SEED_TESTIMONIALS:
            db_t = models.Testimonial(**t_data)
            db.add(db_t)
        db.commit()
    
    return db.query(models.Testimonial).order_by(models.Testimonial.created_at.desc()).all()

@router.post("/", response_model=schemas.TestimonialResponse, status_code=status.HTTP_201_CREATED)
def create_testimonial(payload: schemas.TestimonialCreate, db: Session = Depends(get_db)):
    db_testimonial = models.Testimonial(
        name=payload.name,
        role=payload.role,
        content=payload.content,
        rating=payload.rating,
        image=payload.image
    )
    db.add(db_testimonial)
    db.commit()
    db.refresh(db_testimonial)
    return db_testimonial
