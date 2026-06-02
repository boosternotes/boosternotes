from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
import uuid


class HardBook(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, verbose_name="Book Title")
    description = models.TextField(verbose_name="Description")
    original_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Original Price"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Sale Price"
    )
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Hard Book"
        verbose_name_plural = "Hard Books"

    def __str__(self):
        return self.title


class HardBookImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    book = models.ForeignKey(
        HardBook,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name="Book"
    )
    image = models.ImageField(upload_to='hardbooks/images/', verbose_name="Book Image")
    dropbox_path = models.CharField(max_length=500, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['uploaded_at']
        verbose_name = "Hard Book Image"
        verbose_name_plural = "Hard Book Images"

    def __str__(self):
        return f"{self.book.title} - Image"
    

class SiteSetting(models.Model):
    """Generic site setting for single-value settings"""
    key = models.CharField(max_length=100, unique=True, verbose_name="Setting Key")
    value = models.TextField(blank=True, null=True, verbose_name="Setting Value")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['key']
        verbose_name = "Site Setting"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return f"{self.key} = {self.value[:50]}..." if self.value and len(self.value) > 50 else f"{self.key} = {self.value}"



class NavbarSetting(models.Model):
    """Navbar customization settings"""
    brand_name = models.CharField(max_length=100, default="BoosterNotes", verbose_name="Brand Name")
    tagline = models.CharField(max_length=100, default="Smart Notes. Smart Rank", verbose_name="Tagline")
    logo = models.ImageField(
        upload_to='logos/',
        blank=True,
        null=True,
        verbose_name="Logo Image"
    )
    favicon = models.ImageField(
        upload_to='favicons/',
        blank=True,
        null=True,
        verbose_name="Favicon"
    )
    search_placeholder = models.CharField(
        max_length=200,
        default="Search pdf courses, exams...",
        verbose_name="Search Placeholder"
    )
    whatsapp_number = models.CharField(
        max_length=20,
        default="6350331916",
        verbose_name="WhatsApp Number"
    )
    whatsapp_hours = models.CharField(
        max_length=50,
        default="10 AM to 7 PM",
        verbose_name="WhatsApp Hours"
    )
    coupon_text = models.CharField(
        max_length=100,
        default="🎟️ Apply Coupon",
        verbose_name="Coupon Button Text"
    )
    is_active = models.BooleanField(default=True, verbose_name="Is Active")

    class Meta:
        verbose_name = "Navbar Setting"
        verbose_name_plural = "Navbar Settings"

    def __str__(self):
        return f"Navbar - {self.brand_name}"

class BannerSetting(models.Model):
    """Banner customization settings"""
    BANNER_TYPE_CHOICES = [
        ('desktop', 'Desktop'),
        ('mobile', 'Mobile'),
    ]
    
    image = models.ImageField(
        upload_to='banners/',
        verbose_name="Banner Image",
        blank=True,      # ← add this
        null=True,   
    )
    banner_type = models.CharField(
        max_length=10,
        choices=BANNER_TYPE_CHOICES,
        default='desktop',
        verbose_name="Banner Type"
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Display Order"
    )
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Banner Setting"
        verbose_name_plural = "Banner Settings"
        ordering = ['banner_type', 'order']

    def __str__(self):
        return f"{self.get_banner_type_display()} Banner #{self.pk}"


class StatsSetting(models.Model):
    """Stats section customization"""
    icon = models.CharField(max_length=50, verbose_name="Icon (Font Awesome class)")
    icon_color = models.CharField(
        max_length=20, 
        default="#1a3a8f",
        verbose_name="Icon Color (hex code)"
    )
    value = models.CharField(max_length=50, verbose_name="Value (e.g., 343, 500+)")
    title = models.CharField(max_length=100, verbose_name="Title")
    note = models.CharField(max_length=200, blank=True, null=True, verbose_name="Note/Subtitle")
    display_order = models.PositiveIntegerField(default=0, verbose_name="Display Order")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")

    class Meta:
        ordering = ['display_order', 'id']
        verbose_name = "Stats Setting"
        verbose_name_plural = "Stats Settings"

    def __str__(self):
        return f"{self.title} - {self.value}"

class AboutSetting(models.Model):
    """About section customization"""
    heading = models.CharField(max_length=200, default="About BoosterNotes", verbose_name="Heading")
    text1 = models.TextField(verbose_name="First Paragraph")
    text2 = models.TextField(blank=True, null=True, verbose_name="Second Paragraph (optional)")
    pdf_count = models.CharField(max_length=20, default="343+", verbose_name="PDF Resources Count")
    books_count = models.CharField(max_length=20, default="500+", verbose_name="Books Count")
    users_count = models.CharField(max_length=20, default="2456+", verbose_name="Users Count")
    categories_count = models.CharField(max_length=20, default="10+", verbose_name="Exam Categories Count")
    
    # Feature 1
    feature1_icon = models.CharField(max_length=50, default="fa-solid fa-bolt", verbose_name="Feature 1 Icon (Font Awesome class)")
    feature1_icon_color = models.CharField(max_length=20, default="#1a3a8f", verbose_name="Feature 1 Icon Color")
    feature1_title = models.CharField(max_length=100, default="Fast Download", verbose_name="Feature 1 Title")
    feature1_desc = models.TextField(default="Get instant access to PDF study material after purchase.", verbose_name="Feature 1 Description")
    
    # Feature 2
    feature2_icon = models.CharField(max_length=50, default="fa-solid fa-bullseye", verbose_name="Feature 2 Icon (Font Awesome class)")
    feature2_icon_color = models.CharField(max_length=20, default="#28a745", verbose_name="Feature 2 Icon Color")
    feature2_title = models.CharField(max_length=100, default="Exam Targeted", verbose_name="Feature 2 Title")
    feature2_desc = models.TextField(default="Curated content for NEET, JEE, UPSC, SSC, and more.", verbose_name="Feature 2 Description")
    
    # Feature 3
    feature3_icon = models.CharField(max_length=50, default="fa-solid fa-comments", verbose_name="Feature 3 Icon (Font Awesome class)")
    feature3_icon_color = models.CharField(max_length=20, default="#ffc107", verbose_name="Feature 3 Icon Color")
    feature3_title = models.CharField(max_length=100, default="Support", verbose_name="Feature 3 Title")
    feature3_desc = models.TextField(default="Support available on WhatsApp during working hours.", verbose_name="Feature 3 Description")
    
    is_active = models.BooleanField(default=True, verbose_name="Is Active")

    class Meta:
        verbose_name = "About Setting"
        verbose_name_plural = "About Settings"
        ordering = ['id']

    def __str__(self):
        return "About Section"

class FooterSetting(models.Model):
    """Footer customization"""
    brand_name = models.CharField(max_length=100, default="BoosterNotes", verbose_name="Brand Name")
    tagline = models.CharField(max_length=200, default="Smart Notes. Smart Rank.", verbose_name="Tagline")
    description = models.TextField(default="Reliable study resources for competitive exams.", verbose_name="Description")
    quick_links_title = models.CharField(max_length=100, default="Quick Links", verbose_name="Quick Links Title")
    support_title = models.CharField(max_length=100, default="Support", verbose_name="Support Title")
    contact_title = models.CharField(max_length=100, default="Contact", verbose_name="Contact Title")
    whatsapp_contact = models.CharField(max_length=50, default="WhatsApp: 6350331916", verbose_name="WhatsApp Contact")
    hours_contact = models.CharField(max_length=50, default="10 AM - 7 PM", verbose_name="Hours")
    copyright_text = models.CharField(max_length=200, default="© 2026 BoosterNotes. All rights reserved.", verbose_name="Copyright Text")
    
    # Social Media URLs
    social_facebook = models.CharField(max_length=200, blank=True, null=True, verbose_name="Facebook URL")
    social_linkedin = models.CharField(max_length=200, blank=True, null=True, verbose_name="LinkedIn URL")
    social_instagram = models.CharField(max_length=200, blank=True, null=True, verbose_name="Instagram URL")
    social_youtube = models.CharField(max_length=200, blank=True, null=True, verbose_name="YouTube URL")
    
    # Social Media Icon Colors
    social_facebook_color = models.CharField(max_length=20, default="#1877f2", verbose_name="Facebook Icon Color")
    social_linkedin_color = models.CharField(max_length=20, default="#0a66c2", verbose_name="LinkedIn Icon Color")
    social_instagram_color = models.CharField(max_length=20, default="#e4405f", verbose_name="Instagram Icon Color")
    social_youtube_color = models.CharField(max_length=20, default="#ff0000", verbose_name="YouTube Icon Color")
    
    is_active = models.BooleanField(default=True, verbose_name="Is Active")

    class Meta:
        verbose_name = "Footer Setting"
        verbose_name_plural = "Footer Settings"
        ordering = ['id']

    def __str__(self):
        return "Footer Setting"

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Category Name")
    image = models.ImageField(
        upload_to='categories/',
        blank=True,
        null=True,
        verbose_name="Category Image"
    )
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

    @property
    def image_url(self):
        if self.image and hasattr(self.image, 'url'):
            return self.image.url
        return None

class Notification(models.Model):
    title = models.CharField(max_length=200, verbose_name="Title")
    message = models.TextField(verbose_name="Message")
    link = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="Link"
    )
    sent_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="Time (Auto-generated)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-sent_at']
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def __str__(self):
        return self.title
    





from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name="Coupon Code")
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Discount Amount"
    )
    expiry_date = models.DateField(verbose_name="Expiry Date")
    usage_limit = models.PositiveIntegerField(
        default=1,
        verbose_name="Usage Limit"
    )
    times_used = models.PositiveIntegerField(default=0, editable=False)
    is_active = models.BooleanField(default=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)


    class Meta:
        ordering = ['-created_at']
        verbose_name = "Coupon"
        verbose_name_plural = "Coupons"


    def __str__(self):
        return f"{self.code} - ₹{self.amount}"


    def save(self, *args, **kwargs):
        # Auto-deactivate if expired
        if self.expiry_date and self.expiry_date < timezone.now().date():
            self.is_active = False
        super().save(*args, **kwargs)


    @property
    def is_expired(self):
        return self.expiry_date < timezone.now().date()


    @property
    def remaining_uses(self):
        return max(0, self.usage_limit - self.times_used)



class CouponUsage(models.Model):
    """Track which users have used which coupons - READ ONLY"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='coupon_usages',
        verbose_name="User"
    )
    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.CASCADE,
        related_name='usages',
        verbose_name="Coupon"
    )
    used_at = models.DateTimeField(auto_now_add=True, verbose_name="Used At")
    discount_applied = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Discount Applied",
        editable=False
    )
   
    class Meta:
        ordering = ['-used_at']
        verbose_name = "Coupon Usage"
        verbose_name_plural = "Coupon Usages"
        unique_together = ('user', 'coupon')  # One coupon per user only


    def __str__(self):
        return f"{self.user.username} - {self.coupon.code}"


#dropbox
class ELibraryModel(models.Model):
    """E-Library Course/Resource Model"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, verbose_name="Course Name")
    description = models.TextField(verbose_name="Description")
    original_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Original Price"
    )
    current_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Current Price"
    )
    thumbnail = models.ImageField(
        upload_to='elibrary/thumbnails/',
        verbose_name="Thumbnail Image"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='elibrary_courses',
        verbose_name="Category"
    )
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "E-Library Item"
        verbose_name_plural = "E-Library Items"
    
    def __str__(self):
        return self.name


class ELibraryPDF(models.Model):
    """Multiple PDF uploads for each E-Library item"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(
        ELibraryModel,
        on_delete=models.CASCADE,
        related_name='pdfs',
        verbose_name="Course"
    )
    pdf_name = models.CharField(max_length=200, verbose_name="PDF Name")
    pdf_file = models.FileField(
        upload_to='elibrary/pdfs/',
        verbose_name="PDF File (will be saved to Dropbox)"
    )
    dropbox_path = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="Dropbox Path"
    )
    is_active = models.BooleanField(default=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['uploaded_at']
        verbose_name = "E-Library PDF"
        verbose_name_plural = "E-Library PDFs"
    
    def __str__(self):
        return f"{self.pdf_name} - {self.course.name}"