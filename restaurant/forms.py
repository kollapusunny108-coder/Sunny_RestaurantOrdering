from django import forms
from .models import Order


class OrderCheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['customer_name', 'customer_phone', 'table_number', 'special_notes']
        widgets = {
            'customer_name': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Your Full Name',
                'required': True,
                'id': 'customer_name',
            }),
            'customer_phone': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Phone number (e.g. +1 555-0199)',
                'required': True,
                'id': 'customer_phone',
            }),
            'table_number': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'e.g. Table 4 or Takeout Counter',
                'required': True,
                'id': 'table_number',
            }),
            'special_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Any dietary preferences, allergy notices, or spice level requests...',
                'id': 'special_notes',
            }),
        }
        labels = {
            'customer_name': 'Full Name',
            'customer_phone': 'Phone Number',
            'table_number': 'Table Number / Dine-in or Takeaway',
            'special_notes': 'Kitchen Notes (Optional)',
        }


class OrderStatusUpdateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'form-select',
            })
        }
