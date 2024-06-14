from django.http import JsonResponse
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout
import json
import datetime
from django.views.decorators.csrf import csrf_exempt
import logging
from .models import Patient, Doctor, Appointment, User, PatientReconData, Message, Notification, TimeSlot , Rating,SPECIALIZATIONS,AIData,HistoryEntry,LOCATION_CHOICES,OTP
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
import random



def handle_patient_file(file, appointment):
    if not file:
        return

    allowed_types = ['image/jpeg', 'image/png', 'application/pdf']
    if file.content_type not in allowed_types:
        raise ValueError("Unsupported file type.")

    appointment.patient_file = file
    appointment.save()


Userr = get_user_model()

@csrf_exempt
@require_http_methods(["POST"])
def RegisterDoctor(request):
    data = request.POST
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    confirmation = data.get("confirmation")
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    specialization = data.get("specialization")
    City=data.get("City")
    clinic_location = data.get("clinic_location")
    price = data.get("price")
    id=data.get("ID_Doctor")
    certificate=data.get("Ceetificate_Doctor")
    gender=data.get("Gender")

    if password != confirmation:
        return JsonResponse({"message": "Password and confirmation do not match."}, status=406)

    try:
        user = Userr.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            gende=gender,
            type="doctor"  # Set the type field to "doctor"
        )

        Doctor.objects.create(user=user, specialization=specialization, clinic_location=clinic_location, price=price , City=City, id=id , certificate=certificate , )
        return JsonResponse({"message": "Doctor registered successfully."}, status=201)
    except IntegrityError:
        return JsonResponse({"message": "Username already taken."}, status=400)
    except Exception as e:
        return JsonResponse({"message": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def RegisterPatient(request):
    data = request.POST
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    confirmation = data.get("confirmation")
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    gender=data.get("Gender")


    if password != confirmation:
        return JsonResponse({"message": "Password and confirmation do not match."}, status=406)

    try:
        user = Userr.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            gende=gender,
            type="patient"  # Set the type field to "patient"
        )

        Patient.objects.create(user=user)
        return JsonResponse({"message": "Patient registered successfully."}, status=201)
    except IntegrityError:
        return JsonResponse({"message": "Username already taken."}, status=400)
    except Exception as e:
        return JsonResponse({"message": str(e)}, status=500)

@csrf_exempt
@login_required
@require_http_methods(["GET"])
def get_patient_own_history(request):
    """Returns the history of the logged-in patient"""
    try:
        # Ensure the user is a patient
        if not hasattr(request.user, 'patient'):
            return JsonResponse({"error": "This operation is only valid for patients."}, status=401)

        # Retrieve the patient
        patient = Patient.objects.get(user=request.user)

        # Retrieve the patient's history
        history_entries = HistoryEntry.objects.filter(patient=patient).order_by('-created_at')
        serialized_history = [entry.public_serialize() for entry in history_entries]

        return JsonResponse({"patient_history": serialized_history}, status=200)

    except Patient.DoesNotExist:
        return JsonResponse({"error": "Patient not found."}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)



@csrf_exempt
@login_required
@require_http_methods(["POST"])
def RateDoctor(request):
    try:
        data = json.loads(request.body)
        doctor_id = data.get("doctor_id")
        rating_value = data.get("rating")
        review = data.get("review", "")

        if request.user.type != "patient":
            return JsonResponse({"error": "Only patients can rate doctors."}, status=403)

        patient = Patient.objects.get(user=request.user)
        doctor = Doctor.objects.get(id=doctor_id)

        if not (1 <= rating_value <= 5):
            return JsonResponse({"error": "Rating must be between 1 and 5."}, status=400)

        rating, created = Rating.objects.update_or_create(
            doctor=doctor, patient=patient,
            defaults={"rating": rating_value, "review": review}
        )

        return JsonResponse({"message": "Rating submitted successfully."}, status=201)

    except Doctor.DoesNotExist:
        return JsonResponse({"error": "Doctor not found."}, status=404)
    except Patient.DoesNotExist:
        return JsonResponse({"error": "Patient not found."}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def LoginUser(request):
    """Logs in a user"""
    if request.method != "POST":
        return JsonResponse({"error": "POST request is required."}, status=400)

    data = json.loads(request.body)
    username = data.get("username")
    password = data.get("password")
    user_type = data.get("type")  # Get the type of user trying to login

    user = authenticate(request, username=username, password=password)

    if user is not None:
        # Check if the user is a patient
        if user_type == "patient":
            try:
                patient = Patient.objects.get(user=user)
                login(request, user)
                return JsonResponse({"message": "Patient login successful."}, status=202)
            except Patient.DoesNotExist:
                return JsonResponse({"message": "Username, type, and/or password is incorrect."}, status=406)

        # Check if the user is a doctor
        elif user_type in ["Doctor", "doctor"]:
            try:
                doctor = Doctor.objects.get(user=user)
                login(request, user)
                return JsonResponse({"message": "Doctor login successful."}, status=202)
            except Doctor.DoesNotExist:
                return JsonResponse({"message": "Username, type, and/or password is incorrect."}, status=406)

    return JsonResponse({"message": "Username, type, and/or password is incorrect."}, status=406)


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def LogoutUser(request):
    """Logs out the current user"""
    logout(request)
    return JsonResponse({"message": "Logged out"}, status=202)


def search_doctors_specialization(request):
    specialization = request.GET.get('specialization')

    if not specialization:
        return JsonResponse({'error': 'No specialization provided'}, status=400)

    doctors = Doctor.objects.filter(specialization__iexact=specialization)

    serialized_doctors = []
    for doctor in doctors:
        serialized_doctors.append({
             'username': doctor.user.username,
             'specialization': doctor.specialization,
             'first_name': doctor.user.first_name,
             'last_name': doctor.user.last_name,
             'clinic_location': doctor.clinic_location,  # Include in serialization
             'price': doctor.price,
             'average_rating': doctor.get_average_rating(),
             'City':doctor.City

             


        })

    return JsonResponse({'doctors': serialized_doctors})


def search_doctors_location(request):
    City = request.GET.get('City')

    if not City:
        return JsonResponse({'error': 'No specialization provided'}, status=400)

    doctors = Doctor.objects.filter(City__iexact=City)

    serialized_doctors = []
    for doctor in doctors:
        serialized_doctors.append({
             'username': doctor.user.username,
             'specialization': doctor.specialization,
             'first_name': doctor.user.first_name,
             'last_name': doctor.user.last_name,
             'clinic_location': doctor.clinic_location,  # Include in serialization
             'City':doctor.City,
             'price': doctor.price,
             'average_rating': doctor.get_average_rating(),


        })

    return JsonResponse({'doctors': serialized_doctors})


def get_specializations(request):
    return JsonResponse({'specializations': [spec[0] for spec in SPECIALIZATIONS]})



@require_http_methods(["GET"])
def get_all_locations(request):
    try:
        # Extract only the location names from LOCATION_CHOICES
        clinic_location = [location[0] for location in LOCATION_CHOICES]

        return JsonResponse({"locations": clinic_location}, status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)




@login_required
def CurrentUser(request):
    user = request.user
    print("User attributes:", dir(user))  # Print user attributes for debugging
    if hasattr(user, 'patient'):
        patient = user.patient
        serialized_data = patient.full_serialize()
        serialized_data['type'] = 'patient'
        return JsonResponse(serialized_data)
    elif hasattr(user, 'doctor'):
        doctor = user.doctor
        serialized_data = doctor.full_serialize()
        serialized_data['type'] = 'doctor'
        return JsonResponse(serialized_data)
    else:
        return JsonResponse({"message": "User type not recognized or user is not associated with a patient or doctor"}, status=500)



@csrf_exempt
@login_required
@require_http_methods(["POST"])
def RequestAppointment(request):
    if request.content_type == 'multipart/form-data':
        date = request.POST.get('date')
        time_slot_id = request.POST.get('time_slot_id')
        patient_message = request.POST.get('patient_message')
        patient_price = request.POST.get('patient_price')
        doctor_id = request.POST.get('doctor_id')
        patient_file = request.FILES.get('patient_file', None)
    else:
        try:
            data = json.loads(request.body)
            date = data.get('date')
            time_slot_id = data.get('time_slot_id')
            patient_message = data.get('patient_message')
            patient_price = request.POST.get('patient_price')
            doctor_id = data.get('doctor_id')
            patient_file = None
        except json.JSONDecodeError:
            return JsonResponse({"error": "Malformed JSON or empty body"}, status=400)

    try:
        doctor = Doctor.objects.get(pk=doctor_id)
        time_slot = TimeSlot.objects.get(pk=time_slot_id)
        patient = Patient.objects.get(user=request.user)

        appointment = Appointment(
            date=date,
            request_time_slot=time_slot,
            patient_message=patient_message,
            patient_price = patient_price,
            patient=patient,
            doctor=doctor,
            patient_file=patient_file
        )
        appointment.save()
        return JsonResponse({"message": "Appointment successfully requested."}, status=201)
    except Doctor.DoesNotExist:
        return JsonResponse({"error": "Doctor not found"}, status=404)
    except TimeSlot.DoesNotExist:
        return JsonResponse({"error": "Time slot not found"}, status=404)
    except Patient.DoesNotExist:
        return JsonResponse({"error": "Patient not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

logger = logging.getLogger(__name__)

# views.py

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def receive_ai_data(request):
    try:
        image = request.FILES.get('image')
        result = request.POST.get('result')

        if not image or not result:
            return JsonResponse({'error': 'Image and result are required'}, status=400)

        patient = Patient.objects.get(user=request.user)
        history_entry = HistoryEntry.objects.create(patient=patient, result=result, image=image)

        print(f"Image path: {history_entry.image.path}")  # Debug print
        print(f"Image URL: {history_entry.image.url}")    # Debug print

        appointment = Appointment.objects.filter(patient=patient, accepted=True).first()

        if appointment:
            AIData.objects.create(patient=patient, doctor=appointment.doctor, image=image, result=result)
            return JsonResponse({'message': 'Data stored for appointment', 'history_entry': history_entry.public_serialize()}, status=201)
        else:
            return JsonResponse({'message': 'Data stored in history', 'history_entry': history_entry.public_serialize()}, status=201)

    except Patient.DoesNotExist:
        return JsonResponse({'error': 'Patient not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)





@csrf_exempt
@login_required
@require_http_methods(["PATCH"])  # Adjusted to use PATCH
def EditAppointment(request):
    try:
        # Ensure the user is a patient
        if not hasattr(request.user, 'patient'):
            return JsonResponse({"error": "This operation is only valid for patients."}, status=403)

        logger.info("Received appointment edit request from patient: %s", request.user.username)

        # Parse request body
        data = json.loads(request.body)
        logger.debug("Request data: %s", data)

        # Extract appointment details from request
        date = data.get("date")
        request_time_slot_id = data.get("request_time_slot_id")
        patient_message = data.get("patient_message")
        patient_price = request.POST.get('patient_price')
        appointment_id = data.get("id")  # Change key name to "id"
        patient_file = request.FILES.get('patient_file', None)

        # Validate date format
        try:
            date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            return JsonResponse({"error": "Invalid date format. Use YYYY-MM-DD."}, status=400)

        # Ensure appointment date is valid
        date_today = datetime.datetime.today().date()
        if date < date_today + datetime.timedelta(days=1):
            return JsonResponse({"error": "Appointments must have dates later than today."}, status=406)
        elif date > date_today + datetime.timedelta(days=8):
            return JsonResponse({"error": "Appointments can only be booked for this week."}, status=406)

        # Validate time slot
        time_slot = TimeSlot.objects.filter(pk=request_time_slot_id).first()
        if not time_slot:
            return JsonResponse({"error": "Invalid time slot."}, status=406)

        # Retrieve appointment and ensure it belongs to the patient
        appointment = Appointment.objects.filter(pk=appointment_id, patient__user=request.user).first()
        if not appointment:
            return JsonResponse({"error": "Appointment not found or does not belong to the patient."}, status=404)

        # Update appointment details
        appointment.date = date
        appointment.request_time_slot = time_slot
        appointment.patient_message = patient_message
        appointment.patient_price = patient_price
        if patient_file:
            appointment.patient_file = patient_file
        appointment.save()

        logger.info("Appointment successfully edited: %s", appointment_id)

        return JsonResponse({"message": "Appointment successfully edited."}, status=200)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Malformed JSON or empty body"}, status=400)
    except ValueError:
        return JsonResponse({"error": "Invalid date format. Use YYYY-MM-DD."}, status=400)
    except Exception as e:
        logger.exception("Error editing appointment: %s", str(e))
        return JsonResponse({"error": "An error occurred while editing the appointment. Please try again later."}, status=500)


@csrf_exempt
@login_required
@require_http_methods(["DELETE"])
def DeleteAppointment(request, appointment_id):
    """Deletes an appointment if the user is a patient"""
    if request.user.type != "patient":
        return JsonResponse(
            {"error": "This operation is only valid for patients"}, status=400)

    try:
        appointment = Appointment.objects.get(
            pk=appointment_id, patient=Patient.objects.get(user=request.user))
        appointment.delete()
        return JsonResponse({"message": "Appointment successfully deleted."}, status=202)
    except Appointment.DoesNotExist:
        return JsonResponse({"error": "Invalid Appointment ID."}, status=404)
    except Patient.DoesNotExist:
        return JsonResponse({"error": "Patient not found."}, status=404)


@csrf_exempt
@login_required
@require_http_methods(["PUT"])
def AcceptAppointment(request):
    try:
        if request.method != "PUT":
            return JsonResponse({"error": "PUT request is required."}, status=400)

        # Ensure the user is authenticated and is a doctor
        if not hasattr(request.user, 'doctor'):
            return JsonResponse({"error": f"{request.user.username} is not a doctor. This operation is only valid for doctors."}, status=406)

        data = json.loads(request.body)
        doctor_message = data.get("doctor_message")
        appointment_id = data.get("id")
        accepted_start_time_str = data.get("accepted_start_time")

        if not accepted_start_time_str:
            return JsonResponse({"error": "Accepted Start Time is required."}, status=406)

        # Attempt to parse the accepted start time
        try:
            accepted_start_time = datetime.datetime.strptime(accepted_start_time_str, "%H:%M").time()
        except ValueError:
            return JsonResponse({"error": "Accepted Start Time is not valid. Use the format HH:MM."}, status=406)

        appointment = Appointment.objects.get(pk=appointment_id, doctor__user=request.user)

        # Validate the accepted start time against the appointment's time slot or business hours
        # Add your validation logic here

        appointment.accepted = True
        appointment.accepted_start_time = accepted_start_time
        appointment.doctor_message = doctor_message
        appointment.save()

        # Notify the patient about the accepted appointment
        Notification.objects.create(
            user=appointment.patient.user,
            message=f"Your appointment with Dr. {appointment.doctor.user.username} on {appointment.date} has been accepted."
        )

        return JsonResponse({"message": "Appointment successfully accepted."}, status=202)

    except Appointment.DoesNotExist:
        return JsonResponse({"error": "Invalid Appointment."}, status=404)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)




@csrf_exempt
@login_required
@require_http_methods(["PUT"])
def RejectAppointment(request):
    try:
        if request.method != "PUT":
            return JsonResponse({"error": "PUT request is required."}, status=400)

        # Ensure the user is authenticated and is a doctor
        if not hasattr(request.user, 'doctor'):
            return JsonResponse({"error": "This operation is only valid for doctors."}, status=401)

        data = json.loads(request.body)
        doctor_message = data.get("doctor_message")
        appointment_id = data.get("id")

        # Fetch the appointment associated with the given ID
        appointment = Appointment.objects.get(pk=appointment_id, doctor__user=request.user)

        # Update the appointment status to rejected
        appointment.rejected = True
        appointment.doctor_message = doctor_message
        appointment.save()

        return JsonResponse({"message": "Appointment successfully rejected."}, status=202)

    except Appointment.DoesNotExist:
        return JsonResponse({"error": "Invalid Appointment."}, status=404)

    except Exception as e:
        traceback.print_exc()  # Print traceback for debugging
        return JsonResponse({"error": str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def PatientAppointments(request):
    try:
        # Ensure the user is authenticated and is a patient
        if not hasattr(request.user, 'patient'):
            return JsonResponse({"error": f"{request.user.username} is not a patient."}, status=403)

        patient = request.user.patient
        appointments = Appointment.objects.filter(patient=patient).order_by("date")
        serialized_appointments = [appointment.serialize_for_patient() for appointment in appointments]
        return JsonResponse({"appointments": serialized_appointments}, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def AcceptedDoctorAppointments(request):
    """Returns a list of accepted appointments of a doctor"""
    if request.user.type == "doctor" or request.user.type == "Doctor" :
        doctor = Doctor.objects.get(user=request.user)
        appointments = Appointment.objects.filter(doctor=doctor, accepted=True).order_by("date")
        serialized_appointments = [appointment.serialize_for_doctor() for appointment in appointments]
        return JsonResponse({"appointments": serialized_appointments}, status=200)
    else:
        return JsonResponse({"error": "This operation is only valid for doctors."}, status=401)



@csrf_exempt
@require_http_methods(["GET"])
def RejectedDoctorAppointments(request):
    """Returns a list of rejected appointments of a doctor"""
    if request.user.type == "Doctor" or request.user.type == "doctor" :
        try:
            doctor = Doctor.objects.get(user=request.user)
            appointments = Appointment.objects.filter(doctor=doctor, rejected=True).order_by("date")
            serialized_appointments = [appointment.serialize_for_doctor() for appointment in appointments]
            return JsonResponse({"appointments": serialized_appointments}, status=200)
        except Doctor.DoesNotExist:
            return JsonResponse({"error": "Doctor not found."}, status=404)
    else:
        return JsonResponse({"error": "This operation is only valid for doctors."}, status=401)


import traceback

@require_http_methods(["GET"])
@login_required
def RequestedDoctorAppointments(request):
    try:
        # Ensure the user is authenticated and is a doctor
        if not hasattr(request.user, 'doctor'):
            return JsonResponse({"error": "This operation is only valid for doctors."}, status=401)

        # Fetch the doctor's appointments
        doctor = request.user.doctor
        appointments = Appointment.objects.filter(doctor=doctor, accepted=False, rejected=False)
        appointments_data = [appointment.serialize_for_patient() for appointment in appointments]

        # Return the serialized appointments data
        return JsonResponse({"appointments": appointments_data}, status=200)

    except Doctor.DoesNotExist:
        return JsonResponse({"error": "Doctor not found."}, status=404)

    except Exception as e:
        traceback.print_exc()  # Print traceback for debugging
        return JsonResponse({"error": str(e)}, status=500)




@require_http_methods(["GET"])
@login_required
def AvailableDoctors(request):
    try:
        # Ensure the user is authenticated and is a patient
        if not hasattr(request.user, 'patient'):
            return JsonResponse({"error": "This operation is only valid for patients."}, status=400)

        # Get the patient's appointments
        patient = request.user.patient
        patient_appointments = patient.appointments.filter(rejected=False)

        # Get doctors associated with the patient's appointments
        doctors_with_appointments = set([appointment.doctor for appointment in patient_appointments])

        # Get all doctors and exclude those with appointments
        all_doctors = Doctor.objects.exclude(pk__in=[doctor.pk for doctor in doctors_with_appointments])

        # Serialize and return the list of available doctors
        serialized_doctors = [doctor.public_serialize() for doctor in all_doctors]
        return JsonResponse({"doctors": serialized_doctors}, status=200)
    
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@login_required
def PatientReconDataView(request):
    if request.user.type != "patient":
        return JsonResponse({"error": "This operation is only valid for patients"}, status=400)

    try:
        recon_file = request.FILES.get('recon_file')
        message = request.POST.get('message')

        if not recon_file or not message:
            return JsonResponse({"error": "Both file and message are required"}, status=400)

        # File type or size validation
        allowed_types = ['image/jpeg', 'image/png', 'application/pdf']
        if recon_file.content_type not in allowed_types:
            return JsonResponse({"error": "Unsupported file type"}, status=400)

        patient = Patient.objects.get(user=request.user)
        recon_data = PatientReconData(
            patient=patient,
            recon_file=recon_file,
            message=message
        )
        recon_data.save()

        return JsonResponse({"message": "Recon data successfully saved."}, status=201)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def SendMessage(request):
    try:
        data = json.loads(request.body)
        sender = request.user
        receiver_username = data.get('receiver_username')
        content = data.get('content')

        # Validate input data
        if not receiver_username:
            return JsonResponse({"error": "Receiver username is required."}, status=400)
        if not content:
            return JsonResponse({"error": "Content is required."}, status=400)

        receiver = User.objects.filter(username__iexact=receiver_username).first()
        if not receiver:
            return JsonResponse({"error": "Receiver not found."}, status=404)

        # Create and save the message
        message = Message.objects.create(sender=sender, receiver=receiver, content=content)

        # Create notification for the receiver
        notification_message = f"You have received a new message from {sender.username}: {content}"
        Notification.objects.create(user=receiver, message=notification_message)

        return JsonResponse({"message": "Message sent successfully."}, status=201)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Malformed JSON or empty body."}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def view_notifications(request):
    """
    Returns all notifications for the logged-in user.
    """
    notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')
    notifications_data = [{
        'id': notification.id,
        'message': notification.message,
        'is_read': notification.is_read,
        'timestamp': notification.timestamp
    } for notification in notifications]

    # Optionally, you could mark notifications as read when they are fetched
    notifications.update(is_read=True)

    return JsonResponse({'notifications': notifications_data})



@require_http_methods(["POST"])
def generate_otp(request):
    email = request.data.get('email')
    if email:
        otp = ''.join(random.choices('0123456789', k=6))  # Generate OTP
        OTP.objects.create(email=email, otp=otp)  # Save OTP to database
        send_mail(
            'Password Reset OTP',
            f'Your OTP for password reset is: {otp}',
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )
        return Response({'message': 'OTP sent successfully'})
    else:
        return Response({'error': 'Email is required'}, status=400)



@require_http_methods(["POST"])
def verify_otp(request):
    email = request.data.get('email')
    otp_entered = request.data.get('otp')
    if email and otp_entered:
        otp_obj = OTP.objects.filter(email=email, otp=otp_entered).first()
        if otp_obj:
            # If OTP is valid, allow password reset
            # Implement your password reset logic here
            otp_obj.delete()  # Delete OTP record from database
            return Response({'message': 'OTP verified successfully'})
        else:
            return Response({'error': 'Invalid OTP'}, status=400)
    else:
        return Response({'error': 'Email and OTP are required'}, status=400)