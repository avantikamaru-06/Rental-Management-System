from django import forms
from django.contrib.auth.models import User
from customers.models import Customer

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}))
    phone = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}))
    saved_address = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Delivery Address'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class CustomerUpdateForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['phone', 'profile_image', 'saved_address', 'payment_info']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_image': forms.FileInput(attrs={'class': 'form-control'}),
            'saved_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'payment_info': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Visa **** 1234'}),
        }
