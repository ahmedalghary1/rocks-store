import csv

from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import Group, User
from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import models, transaction
from django.db.models import Q, Sum
from django.db.models.deletion import ProtectedError
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format

from catalog.models import Product
from core.models import ContactMessage
from orders.models import Order
from orders.services import restore_order_stock, send_order_notifications

from .forms import StaffAuthenticationForm, form_for
from .registry import CHOICE_LABELS, FIELD_LABELS, GROUPS, RESOURCES, permission_name, resource_for


staff_required = user_passes_test(lambda user: user.is_active and user.is_staff, login_url="/dashboard/login/")


class PanelLoginView(LoginView):
    template_name = "controlpanel/login.html"
    authentication_form = StaffAuthenticationForm
    redirect_authenticated_user = False

    def get_success_url(self):
        return self.get_redirect_url() or reverse("controlpanel:index")


def _config_or_404(resource):
    config = resource_for(resource)
    if not config:
        raise Http404("القسم المطلوب غير موجود")
    return config


def _allowed(request, config, action="view"):
    if config["model"] in (User, Group) and action != "view" and not request.user.is_superuser:
        return False
    return request.user.has_perm(permission_name(config, action))


def _require(request, config, action="view"):
    if not _allowed(request, config, action):
        raise PermissionDenied


def _panel_context(request, active=None, **extra):
    groups = []
    for group_key, group_label in GROUPS:
        entries = []
        for key, config in RESOURCES.items():
            if config["group"] == group_key and _allowed(request, config):
                entries.append({"key": key, **config})
        if entries:
            groups.append({"key": group_key, "label": group_label, "entries": entries})
    return {
        "panel_groups": groups,
        "active_resource": active,
        "unread_message_count": ContactMessage.objects.filter(is_read=False).count() if request.user.has_perm("core.view_contactmessage") else 0,
        **extra,
    }


def _field_label(model, name):
    try:
        return FIELD_LABELS.get(name, model._meta.get_field(name).verbose_name)
    except models.FieldDoesNotExist:
        return FIELD_LABELS.get(name, name.replace("_", " "))


def _raw_display(obj, name):
    value = getattr(obj, name, None)
    field = obj._meta.get_field(name)
    display_method = getattr(obj, f"get_{name}_display", None)
    if callable(display_method):
        code = value
        return CHOICE_LABELS.get(code, display_method())
    if isinstance(field, (models.ImageField, models.FileField)):
        if value:
            try:
                return {"kind": "image", "url": value.url, "text": str(value)}
            except ValueError:
                pass
        return {"kind": "empty", "text": "—"}
    if isinstance(field, models.BooleanField):
        return {"kind": "boolean", "value": bool(value), "text": "نعم" if value else "لا"}
    if isinstance(field, models.DateTimeField) and value:
        return date_format(timezone.localtime(value), "Y-m-d، H:i")
    if isinstance(field, models.DateField) and value:
        return date_format(value, "Y-m-d")
    if value in (None, ""):
        return "—"
    return str(value)


def _queryset(config):
    queryset = config["model"].objects.all()
    if config.get("select"):
        queryset = queryset.select_related(*config["select"])
    if not queryset.ordered:
        queryset = queryset.order_by("-pk")
    return queryset


@staff_required
def index(request):
    today = timezone.localdate()
    month_start = today.replace(day=1)
    order_qs = Order.objects.all() if request.user.has_perm("orders.view_order") else Order.objects.none()
    product_qs = Product.objects.all() if request.user.has_perm("catalog.view_product") else Product.objects.none()
    messages_qs = ContactMessage.objects.all() if request.user.has_perm("core.view_contactmessage") else ContactMessage.objects.none()
    completed = order_qs.exclude(status="cancelled")
    stats = {
        "orders_today": order_qs.filter(created_at__date=today).count(),
        "pending_orders": order_qs.filter(status__in=("pending", "confirmed", "processing")).count(),
        "monthly_revenue": completed.filter(created_at__date__gte=month_start).aggregate(value=Sum("total"))["value"] or 0,
        "active_products": product_qs.filter(is_active=True).count(),
        "low_stock": product_qs.filter(is_active=True, stock_quantity__lte=5).count(),
        "unread_messages": messages_qs.filter(is_read=False).count(),
    }
    recent_orders = list(order_qs.order_by("-created_at")[:7])
    for order in recent_orders:
        order.panel_status = CHOICE_LABELS.get(order.status, order.get_status_display())
    status_counts = []
    max_count = 1
    if request.user.has_perm("orders.view_order"):
        raw_counts = {row["status"]: row["count"] for row in order_qs.values("status").annotate(count=models.Count("id"))}
        max_count = max(raw_counts.values(), default=1)
        status_counts = [
            {"code": code, "label": CHOICE_LABELS.get(code, label), "count": raw_counts.get(code, 0), "width": round(raw_counts.get(code, 0) / max_count * 100)}
            for code, label in Order.STATUSES
        ]
    access = {
        "orders": request.user.has_perm("orders.view_order"),
        "products": request.user.has_perm("catalog.view_product"),
        "messages": request.user.has_perm("core.view_contactmessage"),
        "add_product": request.user.has_perm("catalog.add_product"),
    }
    context = _panel_context(
        request,
        page_title="نظرة عامة",
        stats=stats,
        recent_orders=recent_orders,
        low_stock_products=product_qs.filter(is_active=True, stock_quantity__lte=5).order_by("stock_quantity")[:6],
        recent_messages=messages_qs.order_by("-created_at")[:5],
        status_counts=status_counts,
        dashboard_access=access,
    )
    return render(request, "controlpanel/index.html", context)


def _apply_filters(request, queryset, config):
    q = request.GET.get("q", "").strip()
    if q and config.get("search"):
        query = Q()
        for field in config["search"]:
            query |= Q(**{f"{field}__icontains": q})
        queryset = queryset.filter(query)
    for name in config.get("filters", ()):
        value = request.GET.get(name, "")
        if value != "":
            queryset = queryset.filter(**{name: value})
    return queryset, q


def _filter_options(request, config):
    options = []
    model = config["model"]
    for name in config.get("filters", ()):
        field = model._meta.get_field(name)
        values = []
        if isinstance(field, models.BooleanField):
            values = [("1", "نعم"), ("0", "لا")]
        elif field.choices:
            values = [(value, CHOICE_LABELS.get(value, label)) for value, label in field.choices]
        elif isinstance(field, models.ForeignKey):
            values = [(str(item.pk), str(item)) for item in field.remote_field.model.objects.all()[:200]]
        options.append({"name": name, "label": _field_label(model, name), "values": values, "selected": request.GET.get(name, "")})
    return options


def _export_csv(queryset, config):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response.write("\ufeff")
    response["Content-Disposition"] = f'attachment; filename="{config["model"]._meta.model_name}.csv"'
    writer = csv.writer(response)
    writer.writerow([_field_label(config["model"], name) for name in config["list"]])
    for obj in queryset.iterator():
        row = []
        for name in config["list"]:
            displayed = _raw_display(obj, name)
            row.append(displayed.get("text", "") if isinstance(displayed, dict) else displayed)
        writer.writerow(row)
    return response


def _bulk_action(request, queryset, config):
    ids = request.POST.getlist("selected")
    action = request.POST.get("action")
    selected = queryset.filter(pk__in=ids)
    if not ids:
        messages.warning(request, "اختر عنصرًا واحدًا على الأقل.")
        return
    if action in ("activate", "deactivate") and any(field.name == "is_active" for field in config["model"]._meta.fields):
        _require(request, config, "change")
        count = selected.update(is_active=action == "activate")
        messages.success(request, f"تم تحديث {count} عنصر بنجاح.")
    elif action == "mark_read" and config["model"] is ContactMessage:
        _require(request, config, "change")
        count = selected.update(is_read=True)
        messages.success(request, f"تم تعليم {count} رسالة كمقروءة.")
    elif action == "retry_notifications" and config["model"]._meta.model_name == "ordernotification":
        _require(request, config, "change")
        sent = sum(1 for item in selected if send_order_notifications(item.order_id))
        messages.success(request, f"تم إرسال {sent} من أصل {selected.count()} إشعار.")
    elif action == "delete":
        _require(request, config, "delete")
        try:
            count = selected.count()
            selected.delete()
            messages.success(request, f"تم حذف {count} عنصر.")
        except ProtectedError:
            messages.error(request, "تعذر الحذف لأن بعض العناصر مرتبطة ببيانات أخرى.")
    else:
        messages.error(request, "الإجراء المحدد غير متاح لهذا القسم.")


@staff_required
def resource_list(request, resource):
    config = _config_or_404(resource)
    _require(request, config)
    queryset, q = _apply_filters(request, _queryset(config), config)
    if request.GET.get("export") == "csv":
        return _export_csv(queryset, config)
    if request.method == "POST":
        _bulk_action(request, queryset, config)
        return redirect("controlpanel:list", resource=resource)
    if config.get("singleton") and queryset.count() == 1:
        return redirect("controlpanel:edit", resource=resource, pk=queryset.first().pk)
    page = Paginator(queryset, 25).get_page(request.GET.get("page"))
    preserved_query = request.GET.copy()
    preserved_query.pop("page", None)
    preserved_query.pop("export", None)
    columns = [{"name": name, "label": _field_label(config["model"], name)} for name in config["list"]]
    rows = [{"object": obj, "cells": [_raw_display(obj, name) for name in config["list"]]} for obj in page]
    context = _panel_context(
        request,
        active=resource,
        page_title=config["label"],
        config=config,
        resource=resource,
        page=page,
        columns=columns,
        rows=rows,
        query=q,
        filter_options=_filter_options(request, config),
        can_add=_allowed(request, config, "add") and not (config.get("singleton") and config["model"].objects.exists()),
        can_change=_allowed(request, config, "change"),
        can_delete=_allowed(request, config, "delete"),
        supports_active=any(field.name == "is_active" for field in config["model"]._meta.fields),
        query_string=preserved_query.urlencode(),
    )
    return render(request, "controlpanel/resource_list.html", context)


@staff_required
def resource_form(request, resource, pk=None):
    config = _config_or_404(resource)
    action = "change" if pk else "add"
    _require(request, config, action)
    if not pk and config.get("singleton") and config["model"].objects.exists():
        existing = config["model"].objects.first()
        return redirect("controlpanel:edit", resource=resource, pk=existing.pk)
    instance = get_object_or_404(config["model"], pk=pk) if pk else None
    previous_order_status = instance.status if isinstance(instance, Order) else None
    FormClass = form_for(config)
    form = FormClass(request.POST or None, request.FILES or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        if isinstance(instance, User) and instance == request.user and (not form.cleaned_data.get("is_active") or not form.cleaned_data.get("is_staff")):
            form.add_error("is_staff", "لا يمكنك تعطيل حسابك الإداري الحالي أو إزالة صفة الموظف منه.")
        else:
            with transaction.atomic():
                obj = form.save()
                if isinstance(obj, Order) and obj.status == "cancelled" and previous_order_status != "cancelled":
                    restore_order_stock(obj.pk)
            messages.success(request, f"تم حفظ {config['singular']} بنجاح.")
            if request.POST.get("save_continue"):
                return redirect("controlpanel:edit", resource=resource, pk=obj.pk)
            return redirect("controlpanel:list", resource=resource)
    context = _panel_context(
        request,
        active=resource,
        page_title=f"{'تعديل' if pk else 'إضافة'} {config['singular']}",
        config=config,
        resource=resource,
        form=form,
        object=instance,
        can_delete=bool(instance and _allowed(request, config, "delete") and instance != request.user),
    )
    return render(request, "controlpanel/resource_form.html", context)


@staff_required
def resource_delete(request, resource, pk):
    config = _config_or_404(resource)
    _require(request, config, "delete")
    obj = get_object_or_404(config["model"], pk=pk)
    if obj == request.user:
        messages.error(request, "لا يمكنك حذف حسابك المستخدم حاليًا.")
        return redirect("controlpanel:edit", resource=resource, pk=pk)
    if request.method == "POST":
        try:
            obj.delete()
            messages.success(request, f"تم حذف {config['singular']} بنجاح.")
            return redirect("controlpanel:list", resource=resource)
        except ProtectedError:
            messages.error(request, "تعذر الحذف لأن هذا العنصر مرتبط ببيانات أخرى.")
    context = _panel_context(request, active=resource, page_title="تأكيد الحذف", config=config, resource=resource, object=obj)
    return render(request, "controlpanel/confirm_delete.html", context)
