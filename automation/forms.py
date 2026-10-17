from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import os


class UserRegistrationForm(forms.ModelForm):
    """
    Form for new user registration with password confirmation and validation.
    """
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password (min 6 characters)'
        }),
        min_length=6,
        help_text='Must be at least 6 characters long.'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Re-enter your password'
        }),
        label='Confirm Password'
    )

    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Choose a unique username'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'name@example.com'
            }),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise ValidationError("Email address is required.")
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match. Please verify and retype.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class UserLoginForm(forms.Form):
    """
    Form for user authentication.
    """
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter username',
            'autocomplete': 'username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password',
            'autocomplete': 'current-password'
        })
    )


class MoveJpgForm(forms.Form):
    """
    Form for moving JPG/JPEG files between safe approved workspace directories.
    """
    source_folder = forms.CharField(
        max_length=255,
        required=True,
        initial='source_sample',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. source_sample (relative to approved workspace)'
        }),
        help_text='Subfolder or relative path inside the approved workspace containing JPG/JPEG images.'
    )
    dest_folder = forms.CharField(
        max_length=255,
        required=True,
        initial='destination',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. destination (relative to approved workspace)'
        }),
        help_text='Subfolder or relative path inside the approved workspace where images will be organized.'
    )

    def clean_source_folder(self):
        folder = self.cleaned_data.get('source_folder', '').strip()
        if not folder:
            raise ValidationError("Source folder name cannot be empty.")
        if '..' in folder:
            raise ValidationError("Path traversal (..) is not permitted for security reasons.")
        return folder

    def clean_dest_folder(self):
        folder = self.cleaned_data.get('dest_folder', '').strip()
        if not folder:
            raise ValidationError("Destination folder name cannot be empty.")
        if '..' in folder:
            raise ValidationError("Path traversal (..) is not permitted for security reasons.")
        return folder


class ExtractEmailsForm(forms.Form):
    """
    Form for uploading a .txt file to extract email addresses.
    """
    file = forms.FileField(
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'form-file-input',
            'accept': '.txt,text/plain'
        }),
        help_text='Select a .txt file (maximum size: 5 MB).'
    )

    def clean_file(self):
        uploaded_file = self.cleaned_data.get('file')
        if not uploaded_file:
            raise ValidationError("Please select a file to upload.")

        # Check extension
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        if ext != '.txt':
            raise ValidationError("Only .txt files are supported. Please upload a valid text document.")

        # Check file size (5MB max)
        max_size = 5 * 1024 * 1024
        if uploaded_file.size > max_size:
            raise ValidationError(f"File size exceeds the 5MB limit ({uploaded_file.size / (1024*1024):.1f} MB).")

        return uploaded_file


class ScrapeTitleForm(forms.Form):
    """
    Form for providing a public URL to scrape its <title> tag.
    """
    url = forms.URLField(
        required=True,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://example.com'
        }),
        help_text='Enter a public webpage URL starting with http:// or https://'
    )

    def clean_url(self):
        url = self.cleaned_data.get('url', '').strip()
        if not url:
            raise ValidationError("URL cannot be empty.")
        if not (url.startswith('http://') or url.startswith('https://')):
            raise ValidationError("Only HTTP and HTTPS URLs are supported.")
        return url
