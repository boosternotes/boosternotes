from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import *


class HardBookForm(forms.ModelForm):
    class Meta:
        model = HardBook
        fields = ['title', 'description', 'original_price', 'price', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Enter book title'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 4, 'placeholder': 'Enter description'}),
            'original_price': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Original price', 'step': '0.01'}),
            'price': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Sale price', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-input'}),
        }

class ELibraryForm(forms.ModelForm):
    class Meta:
        model = ELibraryModel
        fields = ['name', 'description', 'original_price', 'current_price', 
                  'thumbnail', 'category', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter course name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': '4',
                'placeholder': 'Enter course description'
            }),
            'original_price': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Original price',
                'step': '0.01'
            }),
            'current_price': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Current price',
                'step': '0.01'
            }),
            'thumbnail': forms.FileInput(attrs={
                'class': 'form-input'
            }),
            'category': forms.Select(attrs={'class': 'form-input'}),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-input'
            }),
        }


class ELibraryPDFForm(forms.ModelForm):
    class Meta:
        model = ELibraryPDF
        fields = ['pdf_name', 'pdf_file']
        widgets = {
            'pdf_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'PDF name'
            }),
            'pdf_file': forms.FileInput(attrs={
                'class': 'form-input',
                'accept': 'application/pdf'
            }),
        }

class SiteSettingForm(forms.ModelForm):
    class Meta:
        model = SiteSetting
        fields = ['key', 'value', 'description']
        widgets = {
            'key': forms.TextInput(attrs={'class': 'form-input', 'required': 'required'}),
            'value': forms.Textarea(attrs={'class': 'form-input', 'rows': '3'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': '2'}),
        }


class NavbarSettingForm(forms.ModelForm):
    class Meta:
        model = NavbarSetting
        fields = '__all__'
        widgets = {
            'brand_name': forms.TextInput(attrs={'class': 'form-input'}),
            'tagline': forms.TextInput(attrs={'class': 'form-input'}),
            'logo': forms.FileInput(attrs={'class': 'form-input', 'accept': 'image/*'}),
            'favicon': forms.FileInput(attrs={'class': 'form-input', 'accept': 'image/*'}),
            'search_placeholder': forms.TextInput(attrs={'class': 'form-input'}),
            'whatsapp_number': forms.TextInput(attrs={'class': 'form-input'}),
            'whatsapp_hours': forms.TextInput(attrs={'class': 'form-input'}),
            'coupon_text': forms.TextInput(attrs={'class': 'form-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-input'}),
        }


class BannerUploadForm(forms.Form):
    image = forms.ImageField(
        widget=forms.FileInput(attrs={
            'class': 'form-input',
            'accept': 'image/*',
        }),
        label="Select Banner Image"
    )
    banner_type = forms.ChoiceField(
        choices=BannerSetting.BANNER_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-input'}),
        label="Banner Type"
    )


class StatsSettingForm(forms.ModelForm):
    class Meta:
        model = StatsSetting
        fields = '__all__'
        widgets = {
            'icon': forms.TextInput(attrs={
                'class': 'form-input', 
                'placeholder': 'e.g., fa-solid fa-book, fa-solid fa-box'
            }),
            'icon_color': forms.TextInput(attrs={
                'class': 'form-input',
                'type': 'color',
                'value': '#1a3a8f',
                'style': 'height: 45px; cursor: pointer;'
            }),
            'value': forms.TextInput(attrs={'class': 'form-input'}),
            'title': forms.TextInput(attrs={'class': 'form-input'}),
            'note': forms.TextInput(attrs={'class': 'form-input'}),
            'display_order': forms.NumberInput(attrs={'class': 'form-input', 'min': '0'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-input'}),
        }

class AboutSettingForm(forms.ModelForm):
    class Meta:
        model = AboutSetting
        fields = '__all__'
        widgets = {
            'heading': forms.TextInput(attrs={'class': 'form-input'}),
            'text1': forms.Textarea(attrs={'class': 'form-input', 'rows': '3'}),
            'text2': forms.Textarea(attrs={'class': 'form-input', 'rows': '3'}),
            'pdf_count': forms.TextInput(attrs={'class': 'form-input'}),
            'books_count': forms.TextInput(attrs={'class': 'form-input'}),
            'users_count': forms.TextInput(attrs={'class': 'form-input'}),
            'categories_count': forms.TextInput(attrs={'class': 'form-input'}),
            
            # Feature 1
            'feature1_icon': forms.TextInput(attrs={
                'class': 'form-input', 
                'placeholder': 'e.g., fa-solid fa-bolt'
            }),
            'feature1_icon_color': forms.TextInput(attrs={
                'class': 'form-input',
                'type': 'color',
                'value': '#1a3a8f',
                'style': 'height: 45px; cursor: pointer; padding: 2px;'
            }),
            'feature1_title': forms.TextInput(attrs={'class': 'form-input'}),
            'feature1_desc': forms.Textarea(attrs={'class': 'form-input', 'rows': '2'}),
            
            # Feature 2
            'feature2_icon': forms.TextInput(attrs={
                'class': 'form-input', 
                'placeholder': 'e.g., fa-solid fa-bullseye'
            }),
            'feature2_icon_color': forms.TextInput(attrs={
                'class': 'form-input',
                'type': 'color',
                'value': '#28a745',
                'style': 'height: 45px; cursor: pointer; padding: 2px;'
            }),
            'feature2_title': forms.TextInput(attrs={'class': 'form-input'}),
            'feature2_desc': forms.Textarea(attrs={'class': 'form-input', 'rows': '2'}),
            
            # Feature 3
            'feature3_icon': forms.TextInput(attrs={
                'class': 'form-input', 
                'placeholder': 'e.g., fa-solid fa-comments'
            }),
            'feature3_icon_color': forms.TextInput(attrs={
                'class': 'form-input',
                'type': 'color',
                'value': '#ffc107',
                'style': 'height: 45px; cursor: pointer; padding: 2px;'
            }),
            'feature3_title': forms.TextInput(attrs={'class': 'form-input'}),
            'feature3_desc': forms.Textarea(attrs={'class': 'form-input', 'rows': '2'}),
            
            'is_active': forms.CheckboxInput(attrs={'class': 'form-input'}),
        }

class FooterSettingForm(forms.ModelForm):
    class Meta:
        model = FooterSetting
        fields = '__all__'
        widgets = {
            'brand_name': forms.TextInput(attrs={'class': 'form-input'}),
            'tagline': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': '2'}),
            'quick_links_title': forms.TextInput(attrs={'class': 'form-input'}),
            'support_title': forms.TextInput(attrs={'class': 'form-input'}),
            'contact_title': forms.TextInput(attrs={'class': 'form-input'}),
            'whatsapp_contact': forms.TextInput(attrs={'class': 'form-input'}),
            'hours_contact': forms.TextInput(attrs={'class': 'form-input'}),
            'copyright_text': forms.TextInput(attrs={'class': 'form-input'}),
            
            # Social URLs
            'social_facebook': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://facebook.com/yourpage'}),
            'social_linkedin': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://linkedin.com/in/yourprofile'}),
            'social_instagram': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://instagram.com/yourhandle'}),
            'social_youtube': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://youtube.com/c/yourchannel'}),
            
            # Social Icon Colors
            'social_facebook_color': forms.TextInput(attrs={
                'class': 'form-input',
                'type': 'color',
                'value': '#1877f2',
                'style': 'height: 45px; cursor: pointer; padding: 2px;'
            }),
            'social_linkedin_color': forms.TextInput(attrs={
                'class': 'form-input',
                'type': 'color',
                'value': '#0a66c2',
                'style': 'height: 45px; cursor: pointer; padding: 2px;'
            }),
            'social_instagram_color': forms.TextInput(attrs={
                'class': 'form-input',
                'type': 'color',
                'value': '#e4405f',
                'style': 'height: 45px; cursor: pointer; padding: 2px;'
            }),
            'social_youtube_color': forms.TextInput(attrs={
                'class': 'form-input',
                'type': 'color',
                'value': '#ff0000',
                'style': 'height: 45px; cursor: pointer; padding: 2px;'
            }),
            
            'is_active': forms.CheckboxInput(attrs={'class': 'form-input'}),
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'image', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'e.g., Electronics',
                'class': 'form-input',
                'required': 'required'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-input',
                'accept': 'image/*'
            }),
            'description': forms.Textarea(attrs={
                'placeholder': 'Enter category description (optional)',
                'class': 'form-input',
                'rows': '3'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-input'
            }),
        }
        labels = {
            'name': 'Category Name',
            'image': 'Category Image',
            'description': 'Description',
            'is_active': 'Active',
        }

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=False)
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    is_staff = forms.BooleanField(required=False)
    is_superuser = forms.BooleanField(required=False)

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "password1",
            "password2",
            "is_staff",
            "is_superuser",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"class": "form-input", "placeholder": "Username"})
        self.fields["email"].widget.attrs.update({"class": "form-input", "placeholder": "email@example.com"})
        self.fields["first_name"].widget.attrs.update({"class": "form-input", "placeholder": "First Name"})
        self.fields["last_name"].widget.attrs.update({"class": "form-input", "placeholder": "Last Name"})
        self.fields["password1"].widget.attrs.update({"class": "form-input", "placeholder": "Password"})
        self.fields["password2"].widget.attrs.update({"class": "form-input", "placeholder": "Confirm Password"})
        self.fields["is_staff"].widget.attrs.update({"class": "form-check-input"})
        self.fields["is_superuser"].widget.attrs.update({"class": "form-check-input"})


class CustomUserChangeForm(UserChangeForm):
    email = forms.EmailField(required=False)
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=150, required=False)

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "is_staff",
            "is_superuser",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "password" in self.fields:
            del self.fields["password"]

        self.fields["username"].widget.attrs.update({"class": "form-input", "placeholder": "Username"})
        self.fields["email"].widget.attrs.update({"class": "form-input", "placeholder": "email@example.com"})
        self.fields["first_name"].widget.attrs.update({"class": "form-input", "placeholder": "First Name"})
        self.fields["last_name"].widget.attrs.update({"class": "form-input", "placeholder": "Last Name"})
        self.fields["is_active"].widget.attrs.update({"class": "form-check-input"})
        self.fields["is_staff"].widget.attrs.update({"class": "form-check-input"})
        self.fields["is_superuser"].widget.attrs.update({"class": "form-check-input"})


class NotificationForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = ['title', 'message', 'link']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter notification title'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Enter notification message',
                'rows': 4
            }),
            'link': forms.URLInput(attrs={
                'class': 'form-input',
                'placeholder': 'https://example.com (optional)'
            }),
        }

class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = ['code', 'amount', 'expiry_date', 'usage_limit']
        widgets = {
            'code': forms.TextInput(attrs={
                'placeholder': 'e.g., SAVE20',
                'class': 'form-input',
                'required': 'required'
            }),
            'amount': forms.NumberInput(attrs={
                'placeholder': 'e.g., 100',
                'class': 'form-input',
                'min': '0',
                'step': '0.01',
                'required': 'required'
            }),
            'expiry_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-input',
                'required': 'required'
            }),
            'usage_limit': forms.NumberInput(attrs={
                'placeholder': 'e.g., 10',
                'class': 'form-input',
                'min': '1',
                'required': 'required'
            }),
        }
        labels = {
            'code': 'Coupon Code',
            'amount': 'Discount Amount',
            'expiry_date': 'Expiry Date',
            'usage_limit': 'Usage Limit',
        }