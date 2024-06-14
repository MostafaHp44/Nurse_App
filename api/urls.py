from django.urls import path

from .views import RegisterPatient , RegisterDoctor, LoginUser, LogoutUser, CurrentUser, AvailableDoctors, RequestAppointment, \
    PatientAppointments, RequestedDoctorAppointments, AcceptedDoctorAppointments, RejectedDoctorAppointments, AcceptAppointment, RejectAppointment, \
    EditAppointment, DeleteAppointment, PatientReconDataView , SendMessage ,view_notifications,RateDoctor,get_specializations,receive_ai_data ,get_patient_own_history ,get_all_locations,search_doctors_location,search_doctors_specialization


urlpatterns = [
    path('register_patient', RegisterPatient, name="register_patient"),
    path('register_doctor', RegisterDoctor, name="register_doctor"),
    path('login', LoginUser, name="login"),
    path('logout', LogoutUser, name="logout"),
    path('current_user', CurrentUser, name="current_user"),
    path('available_doctors', AvailableDoctors, name="available_doctors"),
    path('request_appointment', RequestAppointment, name="request_appointment"),
    path('accept_appointment', AcceptAppointment, name="accept_appointment"),
    path('reject_appointment', RejectAppointment, name="reject_appointment"),
    path('patient_appointments', PatientAppointments,name="patient_appointments"),
    path('requested_doctor_appointments', RequestedDoctorAppointments,name="pending_doctor_appointments"),
    path('accepted_doctor_appointments', AcceptedDoctorAppointments,name="accepted_doctor_appointments"),
    path('reject_doctor_appointments',RejectedDoctorAppointments, name="reject_doctor_appointments"),
    path('edit_appointment', EditAppointment, name="edit_appointment"),
    path('delete_appointment', DeleteAppointment, name="delete_appointment"),
    path('delete_appointment/<int:appointment_id>', DeleteAppointment, name='delete-appointment'),
    path('patient-recon-data', PatientReconDataView, name='patient-recon-data'),
    path('send-message', SendMessage, name='send-message'),
    path('notifications', view_notifications, name='view_notifications'),
    path('rate_doctor', RateDoctor, name='rate_doctor'),
    path('search_doctors_specialization', search_doctors_specialization, name='search_doctors_specialization'),
    path('search_doctors_location', search_doctors_location, name='search_doctors_location'),
    path('get_all_specializations', get_specializations, name='specializations'),
    path('get_all_locations', get_all_locations, name='locations'),
    path('receive_ai_data', receive_ai_data, name='receive_ai_data'),
    path('get_patient_own_history', get_patient_own_history, name='get_patient_own_history'),

]
