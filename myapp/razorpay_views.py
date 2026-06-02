import json
import hmac
import hashlib
import razorpay

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Order, OrderItem, ELibraryModel, HardBook, Coupon


def _get_razorpay_client():
    return razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )


def _get_cart(request):
    return request.session.get('cart', {})


def _build_cart_items(cart):
    items = []
    for key, data in cart.items():
        item_type = data.get('type')
        try:
            if item_type == 'pdf':
                obj = ELibraryModel.objects.get(id=data['id'])
                thumb = obj.thumbnail.url if obj.thumbnail else None
                items.append({
                    'id':    str(obj.id),
                    'key':   key,
                    'type':  'pdf',
                    'name':  obj.name,
                    'thumb': thumb,
                    'price': obj.current_price,
                })
            elif item_type == 'book':
                obj = HardBook.objects.get(id=data['id'])
                first_img = obj.images.first()
                thumb = first_img.image.url if first_img and first_img.image else None
                items.append({
                    'id':    str(obj.id),
                    'key':   key,
                    'type':  'book',
                    'name':  obj.title,
                    'thumb': thumb,
                    'price': obj.price,
                })
        except Exception:
            pass
    return items


@login_required
def razorpay_create_order(request):
    """AJAX: Create Razorpay order + pending DB Order."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    cart = _get_cart(request)
    if not cart:
        return JsonResponse({'success': False, 'error': 'Cart is empty'}, status=400)

    cart_items = _build_cart_items(cart)
    if not cart_items:
        return JsonResponse({'success': False, 'error': 'No valid items in cart'}, status=400)

    subtotal = sum(item['price'] for item in cart_items)

    # Check applied coupon
    discount = 0
    coupon_obj = None
    coupon_id = request.session.get('applied_coupon_id')
    if coupon_id:
        try:
            coupon_obj = Coupon.objects.get(id=coupon_id, is_active=True)
            discount = coupon_obj.amount
        except Coupon.DoesNotExist:
            pass

    grand_total = max(0, subtotal - discount)
    amount_paise = int(grand_total * 100)  # Razorpay uses paise

    # Create Razorpay order
    try:
        client = _get_razorpay_client()
        rz_order = client.order.create({
            'amount':   amount_paise,
            'currency': 'INR',
            'payment_capture': 1,
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Razorpay error: {str(e)}'}, status=500)

    # Create pending DB order
    order = Order.objects.create(
        user=request.user,
        full_name=body.get('full_name', ''),
        email=body.get('email', request.user.email),
        mobile=body.get('mobile', ''),
        address=body.get('address', ''),
        city=body.get('city', ''),
        state=body.get('state', ''),
        pincode=body.get('pincode', ''),
        country=body.get('country', 'India'),
        subtotal=subtotal,
        discount_amount=discount,
        grand_total=grand_total,
        coupon=coupon_obj,
        payment_method='razorpay',
        razorpay_order_id=rz_order['id'],
        status='pending',
        is_paid=False,
    )

    # Create order items
    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            item_type=item['type'],
            item_id=item['id'],
            item_name=item['name'],
            item_price=item['price'],
        )

    return JsonResponse({
        'success':           True,
        'razorpay_key':      settings.RAZORPAY_KEY_ID,
        'razorpay_order_id': rz_order['id'],
        'amount':            amount_paise,
        'order_number':      order.order_number,
        'internal_order_id': str(order.id),
    })


@login_required
def razorpay_verify_payment(request):
    """AJAX: Verify Razorpay payment signature."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    rz_order_id   = body.get('razorpay_order_id', '')
    rz_payment_id = body.get('razorpay_payment_id', '')
    rz_signature  = body.get('razorpay_signature', '')
    order_id      = body.get('internal_order_id', '')

    # Signature verification
    msg = f"{rz_order_id}|{rz_payment_id}"
    expected_sig = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode(),
        msg.encode(),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_sig, rz_signature):
        return JsonResponse({'success': False, 'error': 'Invalid payment signature'}, status=400)

    # Mark order as paid
    try:
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Order not found'}, status=404)

    order.razorpay_payment_id = rz_payment_id
    order.razorpay_signature  = rz_signature
    order.is_paid  = True
    order.status   = 'paid'
    order.paid_at  = timezone.now()
    order.save()

    # Clear cart + coupon from session
    for key in ('cart', 'applied_coupon_id', 'applied_coupon_code', 'applied_coupon_amount'):
        request.session.pop(key, None)

    return JsonResponse({
        'success':      True,
        'redirect_url': f'/order/success/{order.id}/',
    })


@login_required
def razorpay_cancel_order(request):
    """AJAX: Cancel pending order when user dismisses Razorpay modal."""
    if request.method != 'POST':
        return JsonResponse({'success': False}, status=405)
    try:
        body = json.loads(request.body)
        order = Order.objects.get(id=body.get('internal_order_id'), user=request.user, is_paid=False)
        order.status = 'cancelled'
        order.save()
    except Exception:
        pass
    return JsonResponse({'success': True})


@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user, is_paid=True)
    return render(request, 'order_success.html', {'order': order})


# ── Admin: Orders Dashboard ───────────────────────────────────────────────────────────
@login_required
def orders_dashboard(request):
    if not request.user.is_staff:
        return redirect('home')

    qs = Order.objects.prefetch_related('items').select_related('user', 'coupon')

    # Filter
    current_status = request.GET.get('status', '')
    search_q       = request.GET.get('q', '')
    if current_status:
        qs = qs.filter(status=current_status)
    if search_q:
        qs = qs.filter(
            Q(order_number__icontains=search_q) |
            Q(full_name__icontains=search_q) |
            Q(email__icontains=search_q) |
            Q(mobile__icontains=search_q)
        )

    # Stats
    total_orders   = Order.objects.count()
    paid_orders    = Order.objects.filter(is_paid=True).count()
    pending_orders = Order.objects.filter(status='pending').count()
    total_revenue  = Order.objects.filter(is_paid=True).aggregate(r=Sum('grand_total'))['r'] or 0

    paginator = Paginator(qs, 20)
    page      = request.GET.get('page', 1)
    orders    = paginator.get_page(page)

    return render(request, 'orders_dashboard.html', {
        'orders':          orders,
        'status_choices':  Order.STATUS_CHOICES,
        'current_status':  current_status,
        'search_q':        search_q,
        'total_orders':    total_orders,
        'paid_orders':     paid_orders,
        'pending_orders':  pending_orders,
        'total_revenue':   total_revenue,
    })


@login_required
def order_detail(request, order_id):
    if not request.user.is_staff:
        return redirect('home')
    order = get_object_or_404(Order.objects.prefetch_related('items').select_related('user', 'coupon'), id=order_id)
    return render(request, 'order_detail.html', {
        'order':          order,
        'status_choices': Order.STATUS_CHOICES,
    })


@login_required
@require_POST
def order_update_status(request, order_id):
    if not request.user.is_staff:
        return redirect('home')
    order = get_object_or_404(Order, id=order_id)
    new_status = request.POST.get('status', '')
    valid = [s[0] for s in Order.STATUS_CHOICES]
    if new_status in valid:
        order.status = new_status
        if new_status == 'paid' and not order.is_paid:
            order.is_paid = True
            order.paid_at = timezone.now()
        order.save()
        messages.success(request, f'Order #{order.order_number} status updated to {order.get_status_display()}.')
    else:
        messages.error(request, 'Invalid status.')
    return redirect(request.META.get('HTTP_REFERER', 'orders_dashboard'))


@login_required
@require_POST
def order_delete(request, order_id):
    if not request.user.is_staff:
        return redirect('home')
    order = get_object_or_404(Order, id=order_id)
    num = order.order_number
    order.delete()
    messages.success(request, f'Order #{num} deleted.')
    return redirect('orders_dashboard')
