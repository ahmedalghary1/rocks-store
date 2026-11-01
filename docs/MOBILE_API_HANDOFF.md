# تسليم API تطبيق ROCKS ELECTRIC

هذا الملف جاهز للإرسال إلى مطوّر تطبيق موبايل أو إلى أداة AI. المصدر الدقيق لكل الحقول والاستجابات هو [مخطط OpenAPI](../api/openapi.yaml)، ويمكن استيراده مباشرة في Postman أو مولّد عميل Flutter/React Native.

## معلومات الاتصال

- `baseUrl`: `https://<your-domain>/api/v1/`، واستبدل النطاق بعنوان الخادم المنشور.
- Swagger: `https://<your-domain>/api/docs/`
- ReDoc: `https://<your-domain>/api/redoc/`
- المخطط الحي: `https://<your-domain>/api/schema/`
- أرسل `Content-Type: application/json` و`Accept-Language: ar` أو `en`.
- الأسعار والقيم المالية نصوص عشرية بعملة الجنيه المصري `EGP`. لا تستخدم `float` لحساب الإجمالي داخل التطبيق؛ الخادم هو مرجع السعر النهائي.
- روابط الصور في الاستجابات مطلقة؛ يجب ضبط `SITE_URL` و`MEDIA_ROOT` وربط `/media/` على الخادم.

## المصادقة

| الغرض | الطلب | الصلاحية |
| --- | --- | --- |
| إنشاء حساب مع رموز الدخول | `POST auth/register/` | عام |
| تسجيل الدخول باسم المستخدم وكلمة المرور | `POST auth/token/` | عام |
| تجديد رمز الوصول | `POST auth/token/refresh/` | عام |
| تسجيل الخروج وإبطال رمز التحديث | `POST auth/logout/` | عام، يحتاج `refresh` في الجسم |
| بيانات الحساب وتعديلها | `GET/PATCH auth/me/` | Bearer |
| تغيير كلمة المرور | `POST auth/change-password/` | Bearer |
| عناوين التوصيل | `GET/POST auth/addresses/` و`GET/PATCH/DELETE auth/addresses/{id}/` | Bearer |
| تعيين عنوان افتراضي | `POST auth/addresses/{id}/set-default/` | Bearer |
| المفضلة | `GET/POST auth/favorites/` و`DELETE auth/favorites/{product_id}/` | Bearer |

مثال تسجيل الدخول:

```json
{"username":"customer","password":"YourPassword"}
```

الاستجابة تشمل `access` و`refresh`. أرسل `Authorization: Bearer <access>` للطلبات المحمية. مدة `access` هي 15 دقيقة ومدة `refresh` هي 30 يومًا. عند التجديد يُعاد **رمز تحديث جديد**، ويجب استبدال القديم به وحفظه في التخزين الآمن للهاتف. عند تسجيل الخروج أرسل `{"refresh":"..."}` ثم احذف الرمزين محليًا. يظل رمز الوصول الصادر صالحًا حتى انتهاء مدته.

إضافة مفضلة: `POST auth/favorites/` بجسم `{"product_id":123}`. القائمة مرقمة الصفحات، والحذف يستخدم رقم المنتج.
مفضلة التطبيق محفوظة في حساب المستخدم؛ مفضلة موقع الويب الحالية تعتمد على الجلسة ولا تتزامن تلقائيًا معها.

## الكتالوج والواجهة

| الغرض | الطلب |
| --- | --- |
| أقسام المتجر | `GET catalog/categories/` |
| تفاصيل قسم بالـ slug | `GET catalog/categories/{slug}/` |
| المنتجات والبحث والترشيح | `GET catalog/products/` |
| تفاصيل منتج بالـ slug | `GET catalog/products/{slug}/` |
| اقتراحات البحث | `GET catalog/products/suggest/?q=charger` |
| عناصر الصفحة الرئيسية | `GET catalog/homepage/` |
| البانرات | `GET marketing/banners/` |
| إعدادات التواصل والهوية | `GET core/settings/` |

مثال بحث: `catalog/products/?category=chargers&search=smart&in_stock=true&min_price=100&ordering=-created_at&page=1&page_size=20`. استجابة القوائم المرقمة تضم `count`, `total_pages`, `current_page`, `next`, `previous`, `results`. المنتج يضم الصور والمواصفات والضمان والخيارات `variants`. إذا كان للمنتج خيارات نشطة، أرسل `variant_id` عند الطلب.

## السلة والدفع والطلبات

- السلة عبر `GET cart/`, `POST cart/items/`, `PATCH/DELETE cart/items/{key}/`, `POST/DELETE cart/coupon/`, `POST cart/clear/` تعتمد على **Cookie الجلسة**. احتفظ بها عبر جميع طلبات السلة إن أردت استخدام هذه المسارات من الهاتف.
- الخيار الأبسط للموبايل هو حفظ السلة محليًا ثم إرسال عناصرها داخل `POST orders/checkout/`؛ لا تحتاج Cookie أو حسابًا للشراء كضيف.
- مناطق الشحن: `GET orders/shipping-zones/`. تحقق من الكوبون اختياريًا عبر `POST orders/validate-coupon/` بجسم `{"code":"SAVE10","subtotal":"1000.00"}`. يتحقق الخادم من الأسعار والكوبون والشحن مجددًا وقت إنشاء الطلب.
- طريقة الدفع المتاحة حاليًا هي **الدفع عند الاستلام فقط**. لا تفترض وجود دفع إلكتروني.

مثال إنشاء طلب:

```json
{
  "customer_name": "Ahmed Ali",
  "phone": "01012345678",
  "email": "ahmed@example.com",
  "governorate": "Cairo",
  "city": "Nasr City",
  "address": "Street 1, building 2",
  "notes": "",
  "coupon_code": "",
  "checkout_token": "82dd44fb-144e-4c55-927e-27a846813908",
  "items": [{"product_id": 123, "variant_id": null, "quantity": 2}]
}
```

ولّد `checkout_token` كـ UUID جديد لكل محاولة شراء، وأعد استخدامه عند إعادة إرسال **نفس الطلب** بسبب انقطاع الشبكة. أول نجاح يعيد `201`، وإعادة المحاولة تعيد `200` دون تكرار الطلب. الرمز المستخدم لعميل آخر يعيد `409`. احفظ `order_number` و`public_token` من الاستجابة. تتضمن الاستجابة الأسعار النهائية وحالة الطلب والعناصر.

- طلباتي للمستخدم المسجل: `GET orders/my-orders/` و`GET orders/my-orders/{order_number}/`.
- تتبع الضيف: `POST orders/track/` بجسم `{"order_number":"RK-...","phone":"01012345678"}`.
- إيصال الطلب: `GET orders/receipt/{public_token}/`. عامل رمز الإيصال كرابط خاص ولا تنشره.
- حالات الطلب: `pending`, `confirmed`, `processing`, `shipped`, `delivered`, `cancelled`.

## خدمات إضافية

- الاشتراك بالنشرة: `POST marketing/newsletter/`.
- رسالة تواصل: `POST core/contact/`، بحد طلب واحد للدقيقة لكل IP.
- مسارات `admin/*` مخصصة للموظفين فقط؛ لا تضعها في تطبيق العميل.
- الأخطاء المعتادة: `400` بيانات غير صحيحة، `401` مصادقة مطلوبة أو رمز منتهٍ، `403` صلاحية غير كافية، `404` غير موجود، `409` رمز شراء مستخدم، `429` تجاوز حد الطلبات. تعرض أخطاء الحقول كقائمة تحت اسم الحقل، والأخطاء العامة داخل `detail`.

## تعليمات جاهزة لأي AI يبني التطبيق

> ابنِ تطبيق موبايل لمتجر ROCKS ELECTRIC بالاعتماد على ملف `api/openapi.yaml` المرفق. استخدم `docs/MOBILE_API_HANDOFF.md` لفهم تسلسل الدخول والكتالوج والشراء. أنشئ طبقة API موحدة مع تخزين JWT الآمن وتدوير refresh token، ودعم العربية والإنجليزية، وصفحات الرئيسية والأقسام والبحث وتفاصيل المنتج والخيارات والمفضلة والسلة المحلية والعناوين والدفع عند الاستلام وطلباتي وتتبع الطلب. استخدم أسعار الخادم النهائية، وروابط الصور من الاستجابة، وأرسل UUID ثابتًا عند إعادة محاولة إنشاء نفس الطلب. لا تخترع حقولًا أو مسارات غير موجودة في OpenAPI.

## تشغيل الخادم بعد رفع التغييرات

```bash
pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py check
```

أعد تحميل تطبيق الويب بعد ذلك. تشمل الـ migrations الجديدة جدول المفضلة وجداول إبطال JWT. تأكد من HTTPS وضبط `SECRET_KEY`, `ALLOWED_HOSTS`, `SITE_URL` وربط `/media/` قبل ربط تطبيق الإنتاج.
