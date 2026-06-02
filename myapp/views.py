from datetime import datetime, timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Count, Q ,F
from django.http import JsonResponse , HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string
from django.utils import timezone
from django.core.files.storage import default_storage

from .models import *
from .forms import *

#elibrary dropbox
from .dropbox_utils import DropboxManager
import os
from django.core.files.base import ContentFile

def search(request):
    query = request.GET.get('q', '').strip()

    navbar = NavbarSetting.objects.first()
    footer = FooterSetting.objects.first()

    category_results = Category.objects.filter(name__icontains=query) if query else Category.objects.none()
    elibrary_results = ELibraryModel.objects.filter(name__icontains=query) if query else ELibraryModel.objects.none()
    hardbook_results = HardBook.objects.filter(title__icontains=query) if query else HardBook.objects.none()

    total_results = category_results.count() + elibrary_results.count() + hardbook_results.count()

    active_coupons = Coupon.objects.filter(
        is_active=True,
        expiry_date__gte=timezone.now().date(),
        usage_limit__gt=F('times_used')
    ).order_by('-created_at')[:6]

    context = {
        'navbar': navbar,
        'footer': footer,
        'search_query': query,
        'category_results': category_results,
        'elibrary_results': elibrary_results,
        'hardbook_results': hardbook_results,
        'total_results': total_results,
        'active_coupons': active_coupons,
    }
    return render(request, 'search_results.html', context)

@login_required
def hard_books_list(request):
    books = HardBook.objects.prefetch_related('images').all()
    return render(request, 'hard_books_list.html', {'books': books})

@login_required
def hard_book_add(request):
    if request.method == 'POST':
        form = HardBookForm(request.POST)
        files = request.FILES.getlist('images')

        if form.is_valid():
            book = form.save()

            if files:
                files = files[:5]
                for i, file_obj in enumerate(files, start=1):
                    result = DropboxManager.upload_file(
                        file_obj=file_obj,
                        file_name=f"{book.title.replace(' ', '_')}_{i}_{file_obj.name}",
                        folder_path='hardbooks/images'
                    )
                    if result['success']:
                        HardBookImage.objects.create(
                            book=book,
                            image=file_obj,
                            dropbox_path=result['dropbox_path']
                        )
                    else:
                        messages.error(request, f"Image {i} upload failed: {result['error']}")

            messages.success(request, "Hard book added successfully!")
            return redirect('hard_books_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = HardBookForm()

    return render(request, 'hard_book_form.html', {'form': form})

@login_required
def hard_book_edit(request, pk):
    book = get_object_or_404(HardBook, pk=pk)

    if request.method == 'POST':
        form = HardBookForm(request.POST, instance=book)
        files = request.FILES.getlist('images')

        if form.is_valid():
            book = form.save()

            existing_count = book.images.count()
            available_slots = max(0, 5 - existing_count)

            if files and available_slots > 0:
                files = files[:available_slots]
                for i, file_obj in enumerate(files, start=1):
                    result = DropboxManager.upload_file(
                        file_obj=file_obj,
                        file_name=f"{book.title.replace(' ', '_')}_{i}_{file_obj.name}",
                        folder_path='hardbooks/images'
                    )
                    if result['success']:
                        HardBookImage.objects.create(
                            book=book,
                            image=file_obj,
                            dropbox_path=result['dropbox_path']
                        )
                    else:
                        messages.error(request, f"Image upload failed: {result['error']}")

            messages.success(request, "Hard book updated successfully!")
            return redirect('hard_books_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = HardBookForm(instance=book)

    return render(request, 'hard_book_form.html', {'form': form, 'book': book})

@login_required
def hard_book_delete(request, pk):
    book = get_object_or_404(HardBook, pk=pk)
    if request.method == 'POST':
        book.delete()
        messages.success(request, "Hard book deleted successfully!")
    return redirect('hard_books_list')

@login_required
def hard_book_image_delete(request, pk):
    img = get_object_or_404(HardBookImage, pk=pk)
    if request.method == 'POST':
        DropboxManager.delete_file(img.dropbox_path)
        img.delete()
        messages.success(request, "Image deleted successfully!")
    return redirect('hard_books_list')

@login_required
def elibrary_dashboard(request):
    """E-Library dashboard - list all courses"""
    courses = ELibraryModel.objects.all()
    
    # Optional: Filter by category
    category_id = request.GET.get('category')
    if category_id:
        courses = courses.filter(category_id=category_id)
    
    categories = Category.objects.filter(is_active=True)
    
    return render(request, 'elibrary/dashboard.html', {
        'courses': courses,
        'categories': categories
    })


@login_required
def elibrary_add(request):
    """Add new E-Library course"""
    if request.method == 'POST':
        form = ELibraryForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save()
            messages.success(request, "E-Library course added successfully!")
            return redirect('elibrary_dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ELibraryForm()
    
    return render(request, 'elibrary/add.html', {'form': form})


@login_required
def elibrary_edit(request, pk):
    """Edit E-Library course"""
    course = get_object_or_404(ELibraryModel, pk=pk)
    
    if request.method == 'POST':
        form = ELibraryForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            course = form.save()
            messages.success(request, "E-Library course updated successfully!")
            return redirect('elibrary_dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ELibraryForm(instance=course)
    
    return render(request, 'elibrary/edit.html', {'form': form, 'course': course})


@login_required
def elibrary_delete(request, id):  # Changed from 'pk' to 'id' to match URL
    course = get_object_or_404(ELibraryModel, id=id)
    
    # Only allow POST requests (JavaScript confirm first)
    if request.method == 'POST':
        course.delete()
        messages.success(request, "Course deleted successfully!")
        return redirect('elibrary_dashboard')
    
    # This shouldn't be reached since we use POST with confirm()
    return redirect('elibrary_dashboard')


from django.conf import settings
@login_required
def elibrary_upload_pdf(request, pk):
    course = get_object_or_404(ELibraryModel, pk=pk)

    if request.method == 'POST':
        form = ELibraryPDFForm(request.POST, request.FILES)
        if form.is_valid():
            pdf = form.save(commit=False)
            pdf.course = course

            result = DropboxManager.upload_file(
                request.FILES['pdf_file'],
                request.FILES['pdf_file'].name,
                f"{settings.DROPBOX_FOLDER}/pdfs/{course.id}"
            )

            if result['success']:
                pdf.dropbox_path = result['dropbox_path']
                pdf.save()
                messages.success(request, "PDF uploaded successfully!")
                return redirect('elibrary_upload_pdf', pk=course.pk)
            else:
                messages.error(request, f"Dropbox upload failed: {result['error']}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ELibraryPDFForm()

    return render(request, 'elibrary/upload_pdf.html', {
        'form': form,
        'course': course
    })



@login_required
def elibrary_pdf_delete(request, pk):
    """Delete a PDF"""
    pdf = get_object_or_404(ELibraryPDF, pk=pk)
    
    if request.method == 'POST':
        # Delete from Dropbox
        if pdf.dropbox_path:
            DropboxManager.delete_file(pdf.dropbox_path)
        
        pdf.delete()
        messages.success(request, "PDF deleted successfully!")
    
    return redirect('elibrary_dashboard')

# Helper to get or create single instance
def get_or_create_setting(model, defaults=None):
    setting, created = model.objects.get_or_create(id=1, defaults=defaults or {})
    return setting



@login_required
def navbar_custom(request):
    """Navbar customization"""
    setting = get_or_create_setting(NavbarSetting)
    
    if request.method == 'POST':
        form = NavbarSettingForm(request.POST, request.FILES, instance=setting)
        if form.is_valid():
            form.save()
            messages.success(request, "Navbar settings updated successfully!")
            return redirect('dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = NavbarSettingForm(instance=setting)
    
    return render(request, 'navbar.html', {'form': form})


@login_required
def banner_custom(request):
    desktop_banners = BannerSetting.objects.filter(banner_type='desktop').order_by('order')
    mobile_banners  = BannerSetting.objects.filter(banner_type='mobile').order_by('order')
    upload_form     = BannerUploadForm()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'upload':
            upload_form = BannerUploadForm(request.POST, request.FILES)
            if upload_form.is_valid():
                BannerSetting.objects.create(
                    image=upload_form.cleaned_data['image'],
                    banner_type=upload_form.cleaned_data['banner_type'],
                    is_active=True
                )
                messages.success(request, "Banner uploaded successfully!")
                return redirect('banner_custom')
            else:
                messages.error(request, "Please select a valid image.")

        elif action == 'toggle':
            banner = get_object_or_404(BannerSetting, pk=request.POST.get('banner_id'))
            banner.is_active = not banner.is_active
            banner.save()
            messages.success(request, f"Banner {'activated' if banner.is_active else 'deactivated'}.")
            return redirect('banner_custom')

        elif action == 'delete':
            banner = get_object_or_404(BannerSetting, pk=request.POST.get('banner_id'))
            banner.image.delete(save=False)
            banner.delete()
            messages.success(request, "Banner deleted successfully!")
            return redirect('banner_custom')

    return render(request, 'banner.html', {
        'upload_form':     upload_form,
        'desktop_banners': desktop_banners,
        'mobile_banners':  mobile_banners,
    })


@login_required
def stats_custom(request):
    """Stats section customization - list + create + edit + delete"""
    stats = StatsSetting.objects.all()
    
    if request.method == 'POST':
        form = StatsSettingForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Stats item added successfully!")
            return redirect('stats_custom')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = StatsSettingForm()
    
    return render(request, 'stats.html', {'stats': stats, 'form': form})


@login_required
def stats_edit(request, pk):
    """Edit stats item"""
    stat = get_object_or_404(StatsSetting, pk=pk)
    
    if request.method == 'POST':
        form = StatsSettingForm(request.POST, instance=stat)
        if form.is_valid():
            form.save()
            messages.success(request, "Stats item updated successfully!")
            return redirect('stats_custom')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = StatsSettingForm(instance=stat)
    
    return render(request, 'stats_edit.html', {'form': form, 'stat': stat})


@login_required
def stats_delete(request, pk):
    """Delete stats item - no confirmation page"""
    stat = get_object_or_404(StatsSetting, pk=pk)
    stat.delete()
    messages.success(request, "Stats item deleted successfully!")
    return redirect('stats_custom')

@login_required
def about_custom(request):
    """About section customization"""
    setting = AboutSetting.objects.first()
    if not setting:
        setting = AboutSetting.objects.create(
            heading="About BoosterNotes",
            text1="BoosterNotes provides exam-focused PDFs, revision notes, and physical books for students preparing for competitive exams across India.",
            text2="Our material is organized by category, updated regularly, and designed for quick revision and better results.",
            pdf_count="343+",
            books_count="500+",
            users_count="2456+",
            categories_count="10+",
            feature1_icon="fa-solid fa-bolt",
            feature1_icon_color="#1a3a8f",
            feature1_title="Fast Download",
            feature1_desc="Get instant access to PDF study material after purchase.",
            feature2_icon="fa-solid fa-bullseye",
            feature2_icon_color="#28a745",
            feature2_title="Exam Targeted",
            feature2_desc="Curated content for NEET, JEE, UPSC, SSC, and more.",
            feature3_icon="fa-solid fa-comments",
            feature3_icon_color="#ffc107",
            feature3_title="Support",
            feature3_desc="Support available on WhatsApp during working hours."
        )
    
    if request.method == 'POST':
        form = AboutSettingForm(request.POST, instance=setting)
        if form.is_valid():
            form.save()
            messages.success(request, "About section updated successfully!")
            return redirect('about_custom')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = AboutSettingForm(instance=setting)
    
    return render(request, 'about.html', {'form': form})

@login_required
def footer_custom(request):
    """Footer section customization"""
    setting = FooterSetting.objects.first()
    if not setting:
        setting = FooterSetting.objects.create(
            brand_name="BoosterNotes",
            tagline="Smart Notes. Smart Rank.",
            description="Reliable study resources for competitive exams.",
            quick_links_title="Quick Links",
            support_title="Support",
            contact_title="Contact",
            whatsapp_contact="WhatsApp: 6350331916",
            hours_contact="10 AM - 7 PM",
            copyright_text="© 2026 BoosterNotes. All rights reserved.",
            social_facebook="",
            social_linkedin="",
            social_instagram="",
            social_youtube="",
            social_facebook_color="#1877f2",
            social_linkedin_color="#0a66c2",
            social_instagram_color="#e4405f",
            social_youtube_color="#ff0000"
        )
    
    if request.method == 'POST':
        form = FooterSettingForm(request.POST, instance=setting)
        if form.is_valid():
            form.save()
            messages.success(request, "Footer section updated successfully!")
            return redirect('footer_custom')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = FooterSettingForm(instance=setting)
    
    return render(request, 'footer.html', {'form': form})

@login_required
def category_list(request):
    """Display all categories and handle category creation"""
    categories = Category.objects.all()
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            category = form.save()
            messages.success(
                request, 
                f"Category '{category.name}' created successfully!"
            )
            return redirect('category_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CategoryForm()
    
    context = {
        'categories': categories,
        'form': form,
    }
    return render(request, 'categories.html', context)


@login_required
def category_delete(request, pk):
    """Delete a category"""
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        # Delete image file if exists
        if category.image and default_storage.exists(category.image.name):
            default_storage.delete(category.image.name)
        
        category.delete()
        messages.success(request, "Category deleted successfully!")
        return redirect('category_list')
    
    return render(request, 'category_confirm_delete.html', {'category': category})


@login_required
def coupon_list(request):
    """Display all coupons and handle coupon creation"""
    coupons = Coupon.objects.all()
    
    if request.method == 'POST':
        form = CouponForm(request.POST)
        if form.is_valid():
            coupon = form.save()
            messages.success(
                request, 
                f"Coupon '{coupon.code}' created successfully!"
            )
            return redirect('coupon_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CouponForm()
    
    context = {
        'coupons': coupons,
        'form': form,
    }
    return render(request, 'coupon.html', context)


@login_required
def coupon_delete(request, pk):
    """Delete a coupon"""
    coupon = get_object_or_404(Coupon, pk=pk)
    
    if request.method == 'POST':
        coupon.delete()
        messages.success(request, "Coupon deleted successfully!")
        return redirect('dashboard')
    
    return redirect('dashboard')


@login_required
def coupon_toggle_active(request, pk):
    """Toggle coupon active/inactive status"""
    coupon = get_object_or_404(Coupon, pk=pk)
    coupon.is_active = not coupon.is_active
    coupon.save()
    
    status = "activated" if coupon.is_active else "deactivated"
    messages.success(request, f"Coupon '{coupon.code}' {status}!")
    return redirect('coupon_list')


def is_admin(user):
    return user.is_staff


@login_required
@user_passes_test(is_admin)
def notifications_section(request):
    """Display notifications section with form and table"""
    
    if request.method == 'POST':
        form = NotificationForm(request.POST)
        if form.is_valid():
            notification = form.save(commit=False)
            notification.sent_at = timezone.now()
            notification.save()
            messages.success(request, 'Notification sent successfully!')
            return redirect('notifications_section')
    else:
        form = NotificationForm()

    # Fetch all notifications for the table
    notifications = Notification.objects.all()[:50]

    # Get statistics
    total_notifications = Notification.objects.count()
    sent_today = Notification.objects.filter(
    sent_at__date=timezone.now().date()
).count()

    context = {
        'title': 'Notifications',
        'subtitle': 'Send notifications to users',
        'form': form,
        'notifications': notifications,
        'total_notifications': total_notifications,
        'sent_today': sent_today,
    }

    return render(request, 'notification.html', context)


@login_required
@user_passes_test(is_admin)
def delete_notification(request, notification_id):
    """Delete a notification"""
    notification = get_object_or_404(Notification, id=notification_id)
    
    if request.method == 'POST':
        notification.delete()
        messages.success(request, 'Notification deleted successfully!')
        return redirect('notifications_section')
    
    return render(request, 'admin/confirm_delete.html', {
        'object': notification,
        'action': 'delete notification',
        'next_url': 'notifications_section'
    })



def add_user(request):
    """Handle adding a new user"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'User created successfully!')
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    
    context = {
        'form': form,
        'title': 'Add New User',
        'section': 'users'
    }
    return render(request, 'add_user.html', context)


def edit_user(request, user_id):
    """Handle editing an existing user"""
    user = get_object_or_404(User, pk=user_id)
    
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'User {user.username} updated successfully!')
            return redirect('dashboard')
    else:
        form = CustomUserChangeForm(instance=user)
    
    context = {
        'form': form,
        'user': user,
        'title': f'Edit User: {user.username}',
        'section': 'users'
    }
    return render(request, 'edit_user.html', context)


def delete_user(request, user_id):
    """Handle deleting a user"""
    user = get_object_or_404(User, pk=user_id)
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User {username} deleted successfully!')
        return redirect('users_section')
    
    return redirect('dashboard')



def home(request):
    """Home page with dynamic customization data and active coupons"""
    
    # Get customization settings (create defaults if they don't exist)
    navbar = NavbarSetting.objects.first()
    if not navbar:
        navbar = NavbarSetting.objects.create(
            brand_name="BoosterNotes",
            tagline="Smart Notes. Smart Rank",
            search_placeholder="Search pdf courses, exams...",
            whatsapp_number="6350331916",
            whatsapp_hours="10 AM to 7 PM",
            coupon_text="🎟️ Apply Coupon"
        )
    
    # Get active banners for desktop and mobile
    desktop_banners = BannerSetting.objects.filter(
        is_active=True, 
        banner_type='desktop'
    ).order_by('order')
    
    mobile_banners = BannerSetting.objects.filter(
        is_active=True, 
        banner_type='mobile'
    ).order_by('order')
    
    # Create default banners if none exist
    if not desktop_banners.exists():
        BannerSetting.objects.create(
            banner_type='desktop',
            order=1,
            is_active=True
        )
        desktop_banners = BannerSetting.objects.filter(
            is_active=True, 
            banner_type='desktop'
        ).order_by('order')
    
    if not mobile_banners.exists():
        BannerSetting.objects.create(
            banner_type='mobile',
            order=1,
            is_active=True
        )
        mobile_banners = BannerSetting.objects.filter(
            is_active=True, 
            banner_type='mobile'
        ).order_by('order')
    
    stats = StatsSetting.objects.filter(is_active=True).order_by('display_order')
    if not stats.exists():
        StatsSetting.objects.bulk_create([
            StatsSetting(icon="📚", value="343", title="E-Library Courses", 
                        note="Exam-ready PDFs and revision packs", display_order=1),
            StatsSetting(icon="📦", value="500+", title="Physical Books",
                        note="Printed material delivered to students", display_order=2),
            StatsSetting(icon="👥", value="2456+", title="Active Users",
                        note="Trusted by learners across India", display_order=3),
        ])
        stats = StatsSetting.objects.filter(is_active=True).order_by('display_order')
    
    about = AboutSetting.objects.first()
    if not about:
        about = AboutSetting.objects.create(
            heading="About BoosterNotes",
            text1="BoosterNotes provides exam-focused PDFs, revision notes, and physical books for students preparing for competitive exams across India.",
            text2="Our material is organized by category, updated regularly, and designed for quick revision and better results.",
            pdf_count="343+",
            books_count="500+",
            users_count="2456+",
            categories_count="10+"
        )
    
    footer = FooterSetting.objects.first()
    if not footer:
        footer = FooterSetting.objects.create(
            brand_name="BoosterNotes",
            tagline="Smart Notes. Smart Rank.",
            description="Reliable study resources for competitive exams.",
            copyright_text="© 2026 BoosterNotes. All rights reserved."
        )
    
    # Get active coupons - exclude ones user has already used
    if request.user.is_authenticated:
        used_coupon_ids = CouponUsage.objects.filter(
            user=request.user
        ).values_list('coupon_id', flat=True)
        
        active_coupons = Coupon.objects.filter(
            is_active=True,
            expiry_date__gte=timezone.now().date(),
        ).exclude(
            id__in=used_coupon_ids
        ).annotate(
            remaining=F('usage_limit') - F('times_used')
        ).filter(
            remaining__gt=0
        ).order_by('-created_at')[:6]
    else:
        active_coupons = Coupon.objects.filter(
            is_active=True,
            expiry_date__gte=timezone.now().date(),
        ).annotate(
            remaining=F('usage_limit') - F('times_used')
        ).filter(
            remaining__gt=0
        ).order_by('-created_at')[:6]
    
    categories = Category.objects.all()[:10]

    # Popular PDFs: use only fields that exist on ELibraryModel
    popular_pdfs = (
        ELibraryModel.objects.filter(
            is_active=True,
            # remove product_type filter – it doesn't exist
        )
        .order_by('-created_at')
        [:8]
    )
    
    context = {
        'navbar': navbar,
        'desktop_banners': desktop_banners,
        'mobile_banners': mobile_banners,
        'stats': stats,
        'about': about,
        'footer': footer,
        'categories': categories,
        'active_coupons': active_coupons,
        'popular_pdfs': popular_pdfs,  
    }
    
    return render(request, 'index.html', context)


@login_required
@require_POST
def apply_coupon(request):
    code = request.POST.get("code", "").strip().upper()

    # Step 1: Check if code is provided
    if not code:
        messages.error(request, "Please enter a coupon code.")
        return redirect(request.META.get("HTTP_REFERER", "/"))

    # Step 2: Check if coupon exists
    try:
        coupon = Coupon.objects.get(code__iexact=code)
    except Coupon.DoesNotExist:
        messages.error(request, "Invalid coupon code.")
        return redirect(request.META.get("HTTP_REFERER", "/"))

    # Step 3: Check if coupon is active
    if not coupon.is_active:
        messages.error(request, "This coupon is no longer active.")
        return redirect(request.META.get("HTTP_REFERER", "/"))

    # Step 4: Check if coupon is expired
    if coupon.is_expired:
        messages.error(request, "This coupon has expired.")
        return redirect(request.META.get("HTTP_REFERER", "/"))

    # Step 5: Check if user already used this coupon
    if CouponUsage.objects.filter(user=request.user, coupon=coupon).exists():
        messages.error(request, "You have already used this coupon.")
        return redirect(request.META.get("HTTP_REFERER", "/"))

    # Step 6: Check if coupon has remaining uses
    if coupon.remaining_uses <= 0:
        messages.error(request, "This coupon has reached its usage limit.")
        return redirect(request.META.get("HTTP_REFERER", "/"))

    # Step 7: Save the coupon usage (NO EDIT/DELETE)
    try:
        with transaction.atomic():
            # Create permanent usage record
            CouponUsage.objects.create(
                user=request.user, 
                coupon=coupon,
                discount_applied=coupon.amount
            )
            
            # Update coupon usage count
            coupon.times_used += 1
            if coupon.times_used >= coupon.usage_limit:
                coupon.is_active = False
            coupon.save()

        # Store in session for current checkout
        request.session["applied_coupon_id"] = coupon.id
        request.session["applied_coupon_code"] = coupon.code
        request.session["applied_coupon_amount"] = str(coupon.amount)
        
        messages.success(request, f"Coupon '{coupon.code}' applied! You saved ₹{coupon.amount}")
        
    except Exception as e:
        messages.error(request, "Error applying coupon. Please try again.")
    
    return redirect(request.META.get("HTTP_REFERER", "/"))

@login_required
def dashboard(request):
    # Check if user is admin/superuser
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "You don't have permission to access the dashboard.")
        return redirect('home')
    
    # Get all users with their data
    users = User.objects.all().order_by('-date_joined')
    
    # Calculate statistics
    total_users = users.count()
    active_users = users.filter(is_active=True).count()
    inactive_users = users.filter(is_active=False).count()
    
    # Users joined in last 30 days
    thirty_days_ago = datetime.now() - timedelta(days=30)
    new_users = users.filter(date_joined__gte=thirty_days_ago).count()
    
    # Staff/Admin users
    staff_users = users.filter(is_staff=True).count()
    
    # Create empty form for add mode
    add_form = CustomUserCreationForm()
    
    context = {
        'users': users,
        'total_users': total_users,
        'active_users': active_users,
        'inactive_users': inactive_users,
        'new_users': new_users,
        'staff_users': staff_users,
        'form': add_form,
    }
    
    return render(request, "admin_dashboard.html", context)



def user_login(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Login successful!")
            next_url = request.POST.get("next") or request.GET.get("next") or 'home'
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password")
            return redirect('login')

    return render(request, "login.html")


def signup(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == "POST":
        username = request.POST.get("name")
        email = request.POST.get("email")
        password = request.POST.get("password")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return redirect('signup')

        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()
        login(request, user)
        messages.success(request, "Account created successfully!")
        return redirect('home')

    return render(request, "signup.html")