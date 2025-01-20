# Uncomment the following imports before adding the Model code

from django.db import models
from django.utils.timezone import now
from django.core.validators import MaxValueValidator, MinValueValidator


# Create your models here.
class CarMake(models.Model):
  name = models.CharField(max_length=100)
  description = models.TextField()
  year = models.IntegerField(default=2023,
    validators=[
      MaxValueValidator(2023),
      MinValueValidator(2015)
    ])

  def __str__(self):
    return self.name

class CarModel(models.Model):
  car_make = models.ForeignKey(CarMake, on_delete=models.CASCADE) # Many-to-One relationship
  name = models.CharField(max_length=100)
  CAR_TYPES = [
    ('SEDAN', 'Sedan'),
    ('SUV', 'SUV'),
    ('WAGON', 'Wagon'),
  ]
  type = models.CharField(max_length=10, choices=CAR_TYPES, default='SUV')
  year = models.IntegerField(default=2023,
    validators=[
      MaxValueValidator(2023),
      MinValueValidator(2015)
    ])
  
  def __str__(self):
    return self.name
  


