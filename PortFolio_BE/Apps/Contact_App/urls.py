from django.urls import path
from .views import ContactCreateView, ContactListView, ContactDetailView

urlpatterns = [
    path('create/', ContactCreateView.as_view(), name='contact-create'),
    path('list/', ContactListView.as_view(), name='contact-list'),
    path('list/<int:pk>/', ContactDetailView.as_view(), name='contact-detail'),
]