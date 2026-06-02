from datetime import datetime, timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Count, Q, F
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.timesince import timesince
from django.core.files.storage import default_storage
import uuid

from .models import *
from .forms import *

from .dropbox_utils import DropboxManager
import os
from django.core.files.base import ContentFile


# ── Notifications API ──────────────────────────────────────────────────────────────
def notifications_api(request):
    notifs = Notification.objects.order_by('-sent_at')[:10]
    data = []
    for n in notifs:
        data.append({
            'id':      n.id,
            'title':   n.title,
            'message': n.message,
            'link':    n.link or '',
            'time':    timesince(n.sent_at) + ' ago',
        })
    return JsonResponse({'notifications': data, 'count': len(data)})


# ── Edit Profile ──────────────────────────────────────────────────────────────
@login_required
def edit_profile(request):
    if request.method == 'POST':
        username         = request.POST.get('username', '').strip()
        email            = request.POST.get('email', '').strip()
        first_name       = request.POST.get('first_name', '').strip()
        last_name        = request.POST.get('last_name', '').strip()
        password         = request.POST.get('password', '').strip()
        password_confirm = request.POST.get('password_confirm', '').strip()
        user = request.user
        if username and username != user.username:
            if User.objects.filter(username=username).exclude(pk=user.pk).exists():
                messages.error(request, 'That username is already taken.')
                return redirect('edit_profile')
        if username:
            user.username   = username
        user.email          = email
        user.first_name     = first_name
        user.last_name      = last_name
        if password:
            if password != password_confirm:
                messages.error(request, 'Passwords do not match.')
                return redirect('edit_profile')
            user.set_password(password)
            user.save()
            update_session_auth_hash(request, user)
        else:
            user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('edit_profile')
    return render(request, 'edit_profile.html')


# ── My Purchases ──────────────────────────────────────────────────────────────
@login_required
def my_purchases(request):
    purchases = []
    return render(request, 'my_purchases.html', {'purchases': purchases})


# ── Cart helpers ──────────────────────────────────────────────────────────────
def _get_cart(request):
    return request.session.get('cart', {})

def _save_cart(request, cart):
    request.session['cart'] = cart
    request.session.modified = True

def _build_cart_items(cart):
    """Resolve cart session dict into rich item list."""
    items = []
    for key, data in cart.items():
        item_type = data.get('type')
        try:
            if item_type == 'pdf':
                obj = ELibraryModel.objects.get(id=data['id'])
                thumb = obj.thumbnail.url if obj.thumbnail else None
                items.append({
                    'id':             key,
                    'item_type':      'PDF Course',
                    'name':           obj.name,
                    'thumbnail':      thumb,
                    'category':       obj.category.name if obj.category else '',
                    'price':          obj.current_price,
                    'original_price': obj.original_price,
                })
            elif item_type == 'book':
                obj = HardBook.objects.get(id=data['id'])
                first_img = obj.images.first()
                thumb = first_img.image.url if first_img and first_img.image else None
                items.append({
                    'id':             key,
                    'item_type':      'Physical Book',
                    'name':           obj.title,
                    'thumbnail':      thumb,
                    'category':       '',
                    'price':          obj.price,
                    'original_price': obj.original_price,
                })
        except Exception:
            pass
    return items


# ── Add to Cart ──────────────────────────────────────────────────────────────
@require_POST
def add_to_cart(request):
    item_id   = request.POST.get('item_id', '').strip()
    item_type = request.POST.get('item_type', '').strip()  # 'pdf' or 'book'
    redirect_back = request.META.get('HTTP_REFERER', '/')
    if not item_id or item_type not in ('pdf', 'book'):
        messages.error(request, 'Invalid item.')
        return redirect(redirect_back)
    cart = _get_cart(request)
    key  = f"{item_type}_{item_id}"
    if key in cart:
        messages.info(request, 'Item is already in your cart.')
    else:
        cart[key] = {'id': item_id, 'type': item_type}
        _save_cart(request, cart)
        messages.success(request, '✅ Added to cart!')
    return redirect(redirect_back)


# ── Remove from Cart ──────────────────────────────────────────────────────────────
@require_POST
def remove_from_cart(request, item_key):
    cart = _get_cart(request)
    cart.pop(item_key, None)
    _save_cart(request, cart)
    messages.success(request, 'Item removed from cart.')
    return redirect('cart')


# ── Cart Page ──────────────────────────────────────────────────────────────
def cart_view(request):
    cart       = _get_cart(request)
    cart_items = _build_cart_items(cart)
    subtotal   = sum(item['price'] for item in cart_items)
    applied    = None
    coupon_id  = request.session.get('applied_coupon_id')
    if coupon_id:
        try:
            applied = Coupon.objects.get(id=coupon_id, is_active=True)
        except Coupon.DoesNotExist:
            request.session.pop('applied_coupon_id', None)
    discount    = applied.amount if applied else 0
    grand_total = max(0, subtotal - discount)
    return render(request, 'cart.html', {
        'cart_items':    cart_items,
        'subtotal':      subtotal,
        'applied_coupon': applied,
        'grand_total':   grand_total,
    })


# ── Apply Coupon (cart page) ──────────────────────────────────────────────────────────────
@require_POST
def apply_cart_coupon(request):
    code = request.POST.get('code', '').strip().upper()
    if not code:
        messages.error(request, 'Enter a coupon code.')
        return redirect('cart')
    try:
        coupon = Coupon.objects.get(code__iexact=code, is_active=True)
    except Coupon.DoesNotExist:
        messages.error(request, '❌ Invalid or expired coupon.')
        return redirect('cart')
    if coupon.is_expired:
        messages.error(request, '❌ Coupon has expired.')
        return redirect('cart')
    if coupon.remaining_uses <= 0:
        messages.error(request, '❌ Coupon usage limit reached.')
        return redirect('cart')
    request.session['applied_coupon_id']     = coupon.id
    request.session['applied_coupon_code']   = coupon.code
    request.session['applied_coupon_amount'] = str(coupon.amount)
    messages.success(request, f'✅ Coupon \'{coupon.code}\' applied! Save ₹{coupon.amount}')
    return redirect('cart')


# ── Remove Cart Coupon ──────────────────────────────────────────────────────────────
@require_POST
def remove_cart_coupon(request):
    for key in ('applied_coupon_id', 'applied_coupon_code', 'applied_coupon_amount'):
        request.session.pop(key, None)
    messages.info(request, 'Coupon removed.')
    return redirect('cart')


# ── Checkout Page ──────────────────────────────────────────────────────────────
@login_required
def checkout(request):
    cart       = _get_cart(request)
    if not cart:
        messages.warning(request, 'Your cart is empty.')
        return redirect('cart')
    cart_items = _build_cart_items(cart)
    subtotal   = sum(item['price'] for item in cart_items)
    applied    = None
    coupon_id  = request.session.get('applied_coupon_id')
    if coupon_id:
        try:
            applied = Coupon.objects.get(id=coupon_id, is_active=True)
        except Coupon.DoesNotExist:
            pass
    discount    = applied.amount if applied else 0
    grand_total = max(0, subtotal - discount)
    return render(request, 'checkout.html', {
        'cart_items':     cart_items,
        'subtotal':       subtotal,
        'applied_coupon': applied,
        'grand_total':    grand_total,
    })


# ── Place Order ──────────────────────────────────────────────────────────────
@login_required
@require_POST
def place_order(request):
    cart = _get_cart(request)
    if not cart:
        messages.warning(request, 'Your cart is empty.')
        return redirect('cart')
    request.session.pop('cart', None)
    for key in ('applied_coupon_id', 'applied_coupon_code', 'applied_coupon_amount'):
        request.session.pop(key, None)
    order_ref = str(uuid.uuid4())[:8].upper()
    return render(request, 'order_success.html', {'order_ref': order_ref})


# ─────────────────────────────────────────────────────────────────────────────

def all_categories(request):
    """Public page listing all active categories."""
    categories = Category.objects.filter(is_active=True).annotate(
        pdf_count=Count('elibrary_courses')
    ).order_by('name')
    total_categories = categories.count()
    total_courses = ELibraryModel.objects.filter(is_active=True).count() + \
                    HardBook.objects.filter(is_active=True).count()
    navbar  = NavbarSetting.objects.first()
    footer  = FooterSetting.objects.first()
    cart_count = len(request.session.get('cart', {}))
    return render(request, 'all_categories.html', {
        'categories':       categories,
        'total_categories': total_categories,
        'total_courses':    total_courses,
        'navbar':           navbar,
        'footer':           footer,
        'cart_count':       cart_count,
    })


def category_courses_view(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    elibrary_courses = category.elibrary_courses.filter(is_active=True)
    hardcopy_courses = category.hardcopy_courses.filter(is_active=True) if hasattr(category, 'hardcopy_courses') else []
    total_courses = elibrary_courses.count() + (hardcopy_courses.count() if hasattr(hardcopy_courses, 'count') else 0)
    navbar  = NavbarSetting.objects.first()
    footer  = FooterSetting.objects.first()
    cart_count = len(request.session.get('cart', {}))
    context = {
        'category':        category,
        'elibrary_courses': elibrary_courses,
        'hardcopy_courses': hardcopy_courses,
        'total_courses':   total_courses,
        'navbar':          navbar,
        'footer':          footer,
        'cart_count':      cart_count,
    }
    return render(request, 'category_courses.html', context)


def search(request):
    query = request.GET.get('q', '').strip()
    navbar = NavbarSetting.objects.first()
    footer = FooterSetting.objects.first()
    category_results  = Category.objects.filter(name__icontains=query)      if query else Category.objects.none()
    elibrary_results  = ELibraryModel.objects.filter(name__icontains=query) if query else ELibraryModel.objects.none()
    hardbook_results  = HardBook.objects.filter(title__icontains=query)     if query else HardBook.objects.none()
    total_results = category_results.count() + elibrary_results.count() + hardbook_results.count()
    active_coupons = Coupon.objects.filter(
        is_active=True,
        expiry_date__gte=timezone.now().date(),
        usage_limit__gt=F('times_used')
    ).order_by('-created_at')[:6]
    context = {
        'navbar': navbar, 'footer': footer, 'search_query': query,
        'category_results': category_results, 'elibrary_results': elibrary_results,
        'hardbook_results': hardbook_results, 'total_results': total_results,
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
                        HardBookImage.objects.create(book=book, image=file_obj, dropbox_path=result['dropbox_path'])
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
            existing_count  = book.images.count()
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
                        HardBookImage.objects.create(book=book, image=file_obj, dropbox_path=result['dropbox_path'])
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
    courses = ELibraryModel.objects.all()
    category_id = request.GET.get('category')
    if category_id:
        courses = courses.filter(category_id=category_id)
    categories = Category.objects.filter(is_active=True)
    return render(request, 'elibrary/dashboard.html', {'courses': courses, 'categories': categories})


@login_required
def elibrary_add(request):
    if request.method == 'POST':
        form = ELibraryForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "E-Library course added successfully!")
            return redirect('elibrary_dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ELibraryForm()
    return render(request, 'elibrary/add.html', {'form': form})


@login_required
def elibrary_edit(request, pk):
    course = get_object_or_404(ELibraryModel, pk=pk)
    if request.method == 'POST':
        form = ELibraryForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, "E-Library course updated successfully!")
            return redirect('elibrary_dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ELibraryForm(instance=course)
    return render(request, 'elibrary/edit.html', {'form': form, 'course': course})


@login_required
def elibrary_delete(request, id):
    course = get_object_or_404(ELibraryModel, id=id)
    if request.method == 'POST':
        course.delete()
        messages.success(request, "Course deleted successfully!")
        return redirect('elibrary_dashboard')
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
    return render(request, 'elibrary/upload_pdf.html', {'form': form, 'course': course})


@login_required
def elibrary_pdf_delete(request, pk):
    pdf = get_object_or_404(ELibraryPDF, pk=pk)
    if request.method == 'POST':
        if pdf.dropbox_path:
            DropboxManager.delete_file(pdf.dropbox_path)
        pdf.delete()
        messages.success(request, "PDF deleted successfully!")
    return redirect('elibrary_dashboard')


def get_or_create_setting(model, defaults=None):
    setting, created = model.objects.get_or_create(id=1, defaults=defaults or {})
    return setting


@login_required
def navbar_custom(request):
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
        'upload_form': upload_form,
        'desktop_banners': desktop_banners,
        'mobile_banners': mobile_banners,
    })


@login_required
def stats_custom(request):
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
    stat = get_object_or_404(StatsSetting, pk=pk)
    stat.delete()
    messages.success(request, "Stats item deleted successfully!")
    return redirect('stats_custom')


@login_required
def about_custom(request):
    setting = AboutSetting.objects.first()
    if not setting:
        setting = AboutSetting.objects.create(
            heading="About BoosterNotes",
            text1="BoosterNotes provides exam-focused PDFs.",
            text2="",
            pdf_count="343+", books_count="500+", users_count="2456+", categories_count="10+",
            feature1_icon="fa-solid fa-bolt",     feature1_icon_color="#1a3a8f",
            feature1_title="Fast Download",        feature1_desc="Get instant access to PDF study material after purchase.",
            feature2_icon="fa-solid fa-bullseye",  feature2_icon_color="#28a745",
            feature2_title="Exam Targeted",        feature2_desc="Curated content for NEET, JEE, UPSC, SSC, and more.",
            feature3_icon="fa-solid fa-comments",  feature3_icon_color="#ffc107",
            feature3_title="Support",              feature3_desc="Support available on WhatsApp during working hours."
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
    setting = FooterSetting.objects.first()
    if not setting:
        setting = FooterSetting.objects.create(
            brand_name="BoosterNotes", tagline="Smart Notes. Smart Rank.",
            description="Reliable study resources.",
            copyright_text="\u00a9 2026 BoosterNotes."
        )
    if request.method == 'POST':
        form = FooterSettingForm(request.POST, instance=setting)
        if form.is_valid():
            form.save()
            messages.success(request, "Footer updated!")
            return redirect('footer_custom')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = FooterSettingForm(instance=setting)
    return render(request, 'footer.html', {'form': form})


@login_required
def category_list(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            category = form.save()
            messages.success(request, f"Category '{category.name}' created!")
            return redirect('category_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CategoryForm()
    return render(request, 'categories.html', {'categories': categories, 'form': form})


@login_required
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        name        = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        is_active   = request.POST.get('is_active') == 'on'
        if name:
            category.name        = name
            category.description = description
            category.is_active   = is_active
            if 'image' in request.FILES:
                if category.image and default_storage.exists(category.image.name):
                    default_storage.delete(category.image.name)
                category.image = request.FILES['image']
            category.save()
            messages.success(request, f"Category '{category.name}' updated!")
        else:
            messages.error(request, "Category name is required.")
    return redirect('category_list')


@login_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        if category.image and default_storage.exists(category.image.name):
            default_storage.delete(category.image.name)
        category.delete()
        messages.success(request, "Category deleted!")
        return redirect('category_list')
    return redirect('category_list')


@login_required
def category_toggle_active(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.is_active = not category.is_active
        category.save()
        status = 'activated' if category.is_active else 'deactivated'
        messages.success(request, f"Category '{category.name}' {status}!")
    return redirect('category_list')


@login_required
def coupon_list(request):
    coupons = Coupon.objects.all()
    if request.method == 'POST':
        form = CouponForm(request.POST)
        if form.is_valid():
            coupon = form.save()
            messages.success(request, f"Coupon '{coupon.code}' created!")
            return redirect('coupon_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CouponForm()
    return render(request, 'coupon.html', {'coupons': coupons, 'form': form})


@login_required
def coupon_delete(request, pk):
    coupon = get_object_or_404(Coupon, pk=pk)
    if request.method == 'POST':
        coupon.delete()
        messages.success(request, "Coupon deleted!")
        return redirect('dashboard')
    return redirect('dashboard')


@login_required
def coupon_toggle_active(request, pk):
    coupon = get_object_or_404(Coupon, pk=pk)
    new_status = not coupon.is_active
    Coupon.objects.filter(pk=pk).update(is_active=new_status)
    messages.success(request, f"Coupon '{coupon.code}' {'activated' if new_status else 'deactivated'}!")
    return redirect('coupon_list')


def is_admin(user):
    return user.is_staff


@login_required
@user_passes_test(is_admin)
def notifications_section(request):
    if request.method == 'POST':
        form = NotificationForm(request.POST)
        if form.is_valid():
            notification = form.save(commit=False)
            notification.sent_at = timezone.now()
            notification.save()
            messages.success(request, 'Notification sent!')
            return redirect('notifications_section')
    else:
        form = NotificationForm()
    notifications       = Notification.objects.all()[:50]
    total_notifications = Notification.objects.count()
    sent_today          = Notification.objects.filter(sent_at__date=timezone.now().date()).count()
    context = {
        'title': 'Notifications', 'subtitle': 'Send notifications to users',
        'form': form, 'notifications': notifications,
        'total_notifications': total_notifications, 'sent_today': sent_today,
    }
    return render(request, 'notification.html', context)


@login_required
@user_passes_test(is_admin)
def delete_notification(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id)
    if request.method == 'POST':
        notification.delete()
        messages.success(request, 'Notification deleted!')
        return redirect('notifications_section')
    return render(request, 'admin/confirm_delete.html', {
        'object': notification, 'action': 'delete notification', 'next_url': 'notifications_section'
    })


def add_user(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'User created!')
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'add_user.html', {'form': form, 'title': 'Add New User', 'section': 'users'})


def edit_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'User {user.username} updated!')
            return redirect('dashboard')
    else:
        form = CustomUserChangeForm(instance=user)
    return render(request, 'edit_user.html', {'form': form, 'user': user,
                                               'title': f'Edit User: {user.username}', 'section': 'users'})


def delete_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User {username} deleted!')
        return redirect('users_section')
    return redirect('dashboard')


def home(request):
    navbar = NavbarSetting.objects.first()
    if not navbar:
        navbar = NavbarSetting.objects.create(
            brand_name="BoosterNotes", tagline="Smart Notes. Smart Rank",
            search_placeholder="Search pdf courses, exams...",
            whatsapp_number="6350331916", whatsapp_hours="10 AM to 7 PM",
            coupon_text="\U0001f39f\ufe0f Apply Coupon"
        )
    desktop_banners = BannerSetting.objects.filter(is_active=True, banner_type='desktop').order_by('order')
    mobile_banners  = BannerSetting.objects.filter(is_active=True, banner_type='mobile').order_by('order')
    if not desktop_banners.exists():
        BannerSetting.objects.create(banner_type='desktop', order=1, is_active=True)
        desktop_banners = BannerSetting.objects.filter(is_active=True, banner_type='desktop').order_by('order')
    if not mobile_banners.exists():
        BannerSetting.objects.create(banner_type='mobile', order=1, is_active=True)
        mobile_banners = BannerSetting.objects.filter(is_active=True, banner_type='mobile').order_by('order')
    stats = StatsSetting.objects.filter(is_active=True).order_by('display_order')
    about = AboutSetting.objects.first()
    footer = FooterSetting.objects.first()
    if request.user.is_authenticated:
        used_coupon_ids = CouponUsage.objects.filter(user=request.user).values_list('coupon_id', flat=True)
        active_coupons = Coupon.objects.filter(
            is_active=True, expiry_date__gte=timezone.now().date(),
        ).exclude(id__in=used_coupon_ids).annotate(
            remaining=F('usage_limit') - F('times_used')
        ).filter(remaining__gt=0).order_by('-created_at')[:6]
    else:
        active_coupons = Coupon.objects.filter(
            is_active=True, expiry_date__gte=timezone.now().date(),
        ).annotate(
            remaining=F('usage_limit') - F('times_used')
        ).filter(remaining__gt=0).order_by('-created_at')[:6]
    categories   = Category.objects.filter(is_active=True).annotate(pdf_count=Count('elibrary_courses')).order_by('name')[:10]
    popular_pdfs = ELibraryModel.objects.filter(is_active=True).select_related('category').order_by('-created_at')[:8]
    hard_books   = HardBook.objects.filter(is_active=True).prefetch_related('images').order_by('-created_at')[:8]
    site_settings = NavbarSetting.objects.first()
    cart_count = len(request.session.get('cart', {}))
    context = {
        'navbar': navbar, 'site_settings': site_settings,
        'desktop_banners': desktop_banners, 'mobile_banners': mobile_banners,
        'stats': stats, 'about': about, 'footer': footer,
        'categories': categories, 'active_coupons': active_coupons,
        'popular_pdfs': popular_pdfs, 'hard_books': hard_books,
        'cart_count': cart_count,
    }
    return render(request, 'index.html', context)


def hard_book_detail(request, pk):
    book = get_object_or_404(HardBook.objects.prefetch_related('images'), pk=pk, is_active=True)
    return render(request, 'hard_book_detail.html', {'book': book, 'book_images': book.images.all()})


def elibrary_detail(request, pk):
    pdf = get_object_or_404(
        ELibraryModel.objects.select_related('category').prefetch_related('pdfs'), pk=pk, is_active=True
    )
    uploaded_pdfs = pdf.pdfs.filter(is_active=True).order_by('uploaded_at')
    return render(request, 'elibrary_detail.html', {'pdf': pdf, 'uploaded_pdfs': uploaded_pdfs})


@login_required
@require_POST
def apply_coupon(request):
    code = request.POST.get("code", "").strip().upper()
    redirect_url = request.META.get("HTTP_REFERER", "/")
    if not code:
        messages.error(request, "Please enter a coupon code.")
        return redirect(redirect_url)
    try:
        coupon = Coupon.objects.get(code__iexact=code)
    except Coupon.DoesNotExist:
        messages.error(request, "\u274c Invalid coupon code.")
        return redirect(redirect_url)
    if not coupon.is_active:
        messages.error(request, "\u274c This coupon is no longer active.")
        return redirect(redirect_url)
    if coupon.is_expired:
        messages.error(request, "\u274c This coupon has expired.")
        return redirect(redirect_url)
    if CouponUsage.objects.filter(user=request.user, coupon=coupon).exists():
        messages.warning(request, "\u26a0\ufe0f You have already used this coupon.")
        return redirect(redirect_url)
    if coupon.remaining_uses <= 0:
        messages.error(request, "\u274c This coupon has reached its usage limit.")
        return redirect(redirect_url)
    try:
        with transaction.atomic():
            CouponUsage.objects.create(user=request.user, coupon=coupon, discount_applied=coupon.amount)
            new_times_used = coupon.times_used + 1
            update_fields  = {'times_used': new_times_used}
            if new_times_used >= coupon.usage_limit:
                update_fields['is_active'] = False
            Coupon.objects.filter(pk=coupon.pk).update(**update_fields)
        request.session['applied_coupon_id']     = coupon.id
        request.session['applied_coupon_code']   = coupon.code
        request.session['applied_coupon_amount'] = str(coupon.amount)
        messages.success(request, f"\u2705 Coupon '{coupon.code}' applied! You saved \u20b9{coupon.amount}")
    except Exception:
        messages.error(request, "Something went wrong. Please try again.")
    return redirect(redirect_url)


@login_required
def dashboard(request):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "You don't have permission.")
        return redirect('home')
    users          = User.objects.all().order_by('-date_joined')
    total_users    = users.count()
    active_users   = users.filter(is_active=True).count()
    inactive_users = users.filter(is_active=False).count()
    thirty_days_ago = datetime.now() - timedelta(days=30)
    new_users      = users.filter(date_joined__gte=thirty_days_ago).count()
    staff_users    = users.filter(is_staff=True).count()
    add_form       = CustomUserCreationForm()
    context = {
        'users': users, 'total_users': total_users, 'active_users': active_users,
        'inactive_users': inactive_users, 'new_users': new_users,
        'staff_users': staff_users, 'form': add_form,
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
        email    = request.POST.get("email")
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
