from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import Avg
from datetime import time




class TimeSlot(models.Model):
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        app_label = 'api'

    @classmethod
    def initialize_slots(cls):
        # Define two time slots if they don't exist
        slots_data = [
            (time(9, 0), time(15, 0)),
            (time(15, 0), time(21, 0))
        ]
        for start, end in slots_data:
            cls.objects.get_or_create(start_time=start, end_time=end)

    def __str__(self):
        return f"{self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"



SPECIALIZATIONS = [
    ('Cardiology', 'Cardiology'),
    ('Dermatology', 'Dermatology'),
    ('Neurology', 'Neurology'),
    ('Pediatrics', 'Pediatrics'),
    # Add other specializations as needed
]

GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ]


LOCATION_CHOICES = [
    ('Cairo', 'Cairo'),
    ('Giza', 'Giza'),
    ('Alexandria', 'Alexandria'),
    ('Aswan', 'Aswan'),
    ('Port Said', 'Port Said'),
    ('Suez', 'Suez'),
    ('al-Mansura', 'al-Mansura'),
    ('Tanta', 'Tanta'),
    ('Ismailia', 'Ismailia'),
    ('Fayyum', 'Fayyum'),
    ('Qena', 'Qena'),
    ('Sohag', 'Sohag'),
    ('Damanhur', 'Damanhur'),
]





def profile_upload_path(instance, filename):
    return '/'.join(['profile_pictures', instance.username, filename])


class User(AbstractUser):
    profile_picture = models.ImageField(null=True, blank=True, upload_to=profile_upload_path)
   # ID_User = models.ImageField(null=True, blank=True, upload_to=profile_upload_path)
   # Certificate_User = models.ImageField(null=True, blank=True, upload_to=profile_upload_path)


    type = models.CharField(max_length=64, null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.username} of type {self.type}"






class HistoryEntry(models.Model):
    patient = models.ForeignKey('Patient', related_name='history_entries', on_delete=models.CASCADE)
    result = models.TextField()
    image = models.ImageField(upload_to='ai_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"HistoryEntry for {self.patient.user.username} at {self.created_at}"

    def public_serialize(self):
        from django.conf import settings
        return {
            "id": self.pk,
            "result": self.result,
            "image_url": f"mostafahp.pythonanywhere.com{settings.MEDIA_URL}{self.image}" if self.image else None,  # Provide full image URL
            "created_at": self.created_at.isoformat()  # Serialize datetime as string
        }


class OTP(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(default=time)

    def _str_(self):
        return f"OTP for {self.email}"


class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    City = models.CharField(max_length=255, choices=SPECIALIZATIONS , null=True , blank=True)
    Gender = models.CharField(max_length=255, choices=GENDER_CHOICES , null=True , blank=True)

    def __str__(self):
        return f"Patient {self.user.username}"

    def public_serialize(self):
        return {
            "id": self.pk,
            "username": self.user.username,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "profile_picture_url": self.user.profile_picture.url if self.user.profile_picture else None,
            "type":"patient",
            "Gender":self.Gender,
            "City":self.City

        }

    def full_serialize(self):
        history_entries = self.history_entries.order_by('-created_at')
        return {
            "id": self.pk,
            "username": self.user.username,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "profile_picture_url": self.user.profile_picture.url if self.user.profile_picture else None,
            "type": "patient",
            'history': [entry.public_serialize() for entry in history_entries],
        }





class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    specialization = models.CharField(max_length=100, choices=SPECIALIZATIONS , null=True, blank=True)
    clinic_location = models.CharField(max_length=255 , null=True)
    City = models.CharField(max_length=255, choices=SPECIALIZATIONS , null=True , blank=True)
    Gender = models.CharField(max_length=255, choices=GENDER_CHOICES , null=True , blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Add this line
    available_slots = models.ManyToManyField(TimeSlot, related_name="doctors")
    patient_histories = models.ManyToManyField(HistoryEntry, related_name="doctors", blank=True)
    ID_Doctor = models.FileField(upload_to='recon_files/', null=True, blank=True)
    Ceetificate_Doctor = models.FileField(upload_to='recon_files/', null=True, blank=True)



    



    def __str__(self) -> str:
        return f"Doctor {self.user.username}"

    def calculate_rating(self):
        ratings = self.ratings.all()
        if ratings:
            avg_rating = sum(rating.rating for rating in ratings) / ratings.count()
            return round(avg_rating, 2)
        return None



    def public_serialize(self):
        return {
           "id": self.id,
           "username": self.user.username,
           "specialization": self.specialization,
           "clinic_location": self.clinic_location,
           "price": str(self.price),  # Ensure price is serialized as string
           "rating": self.calculate_rating(),  # Assuming a calculate_rating method exists
           "City":self.City ,
           "Gender":self.Gender ,
           "ID_Doctor": self.ID_Doctor.url if self.ID_Doctor else None,
           "Certificate_Dotor": self.Ceetificate_Doctor.url if self.Ceetificate_Doctor else None,


    }

    def full_serialize(self):
        return {
            "id": self.pk,
            "username": self.user.username,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "specialization": self.specialization,
            "profile_picture_url": self.user.profile_picture.url if self.user.profile_picture else None,
            "type": "Doctor",
            "clinic_location": self.clinic_location,  # Include in serialization
            "price": self.price,
            "average_rating": self.get_average_rating(),
            "City":self.City ,
            "Gender":self.Gender 


        }

    def get_average_rating(self):
        avg_rating = self.ratings.aggregate(avg_rating=Avg('rating'))['avg_rating']
        return avg_rating if avg_rating is not None else 0



class AIData(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='ai_images/')
    result = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)




class Rating(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='ratings')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    rating = models.IntegerField(default=0)  # Set a default value for rating
    review = models.TextField(blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)


    class Meta:
        unique_together = ('doctor', 'patient')  # Prevent a patient from rating the same doctor multiple times

def update_doctor_rating(doctor):
    ratings = doctor.ratings.all()
    if ratings.exists():
        average_rating = ratings.aggregate(models.Avg('score'))['score__avg']
        doctor.rating = average_rating
        doctor.save()



class Appointment(models.Model):
    date = models.DateField()
    request_time_slot = models.ForeignKey(TimeSlot, on_delete=models.SET_NULL, null=True, blank=True)
    accepted_start_time = models.TimeField(null=True, blank=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="appointments")
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="appointments")
    accepted = models.BooleanField(default=False)
    rejected = models.BooleanField(default=False)
    patient_message = models.CharField(max_length=280, null=True, blank=True)
    patient_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    doctor_message = models.CharField(max_length=280, null=True, blank=True)
    patient_file = models.FileField(upload_to='patient_files/', null=True, blank=True)

    class Meta:
        unique_together = ('patient', 'doctor', 'date', 'request_time_slot')

    def __str__(self) -> str:
        slot = f"{self.request_time_slot.start_time.strftime('%H:%M')} - {self.request_time_slot.end_time.strftime('%H:%M')}" if self.request_time_slot else "Unscheduled"
        return f"{self.patient}'s appointment with {self.doctor} on {self.date} at {slot}"
    def serialize_for_patient(self):
        patient_histories = HistoryEntry.objects.filter(patient=self.patient)

        return {
            "id": self.pk,
            "patient_name": self.patient.user.get_full_name(),  # Get patient's full name
            "patient_email": self.patient.user.email,  # Get patient's email
            "accepted": self.accepted,
            "rejected": self.rejected,
            "date": self.date,
            "request_time_slot": self.request_time_slot.start_time.strftime(
                '%H:%M') + ' - ' + self.request_time_slot.end_time.strftime(
                '%H:%M') if self.request_time_slot else None,
            "accepted_start_time": self.accepted_start_time,
            "patient_message": self.patient_message,
            "doctor_message": self.doctor_message,
            "patient_file": self.patient_file.url if self.patient_file else None,
            "doctor_details": self.doctor.public_serialize(),
             "patient_history": [history.public_serialize() for history in patient_histories]

        }

    def serialize_for_doctor(self):
        patient_histories = HistoryEntry.objects.filter(patient=self.patient)

        return {
            "id": self.pk,
            "patient_name": self.patient.user.get_full_name(),  # Get patient's full name
            "patient_email": self.patient.user.email,  # Get patient's email
            "doctor_details": self.doctor.public_serialize(),
            "accepted": self.accepted,
            "rejected": self.rejected,
            "date": self.date,
            "request_time_slot": self.request_time_slot.start_time.strftime(
                '%H:%M') + ' - ' + self.request_time_slot.end_time.strftime(
                '%H:%M') if self.request_time_slot else None,
            "accepted_start_time": self.accepted_start_time,
            "patient_message": self.patient_message,
            "doctor_message": self.doctor_message,
            "patient_file": self.patient_file.url if self.patient_file else None,
            "patient_histories": [history.public_serialize() for history in patient_histories]



        }



class PatientReconData(models.Model):
    patient = models.ForeignKey('Patient', on_delete=models.CASCADE, related_name='recon_data')
    recon_file = models.FileField(upload_to='recon_files/', null=True, blank=True)
    message = models.TextField()
    medical_history_result = models.FileField(upload_to='medical_history/', editable=False, blank=True, null=True)

    def __str__(self):
        return f"Recon Data for {self.patient.user.username}"

    def serialize(self):
        return {
            "id": self.pk,
            "patient_id": self.patient.pk,
            "recon_file_url": self.recon_file.url if self.recon_file else None,
            "message": self.message,
            "result": self.result
        }


class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_messages" , null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    content = models.TextField()

    def __str__(self):
        return f"Message from {self.sender} to {self.receiver} at {self.timestamp}"

    def serialize(self):
        return {
            "id": self.pk,
            "sender": self.sender.username,
            "receiver": self.receiver.username,
            "timestamp": self.timestamp.isoformat(),
            "content": self.content,
        }



class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message}"
