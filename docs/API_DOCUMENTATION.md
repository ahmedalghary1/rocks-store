# توثيق الـ API الشامل — متجر روكس للكهرباء (ROCKS ELECTRIC API Documentation)

للتسليم إلى مطوّر تطبيق موبايل أو AI، استخدم [ملف التسليم المختصر](MOBILE_API_HANDOFF.md) مع [مخطط OpenAPI المولّد](../api/openapi.yaml). المخطط هو المرجع النهائي لأسماء الحقول والاستجابات.

واجهة برمجية متكاملة واحترافية (RESTful API) مبنية بأحدث معايير **Django REST Framework (DRF)** و **OpenAPI 3 / Swagger** و **JWT Authentication**، ومصممة لدعم تطبيقات الموبايل (Flutter / React Native / iOS / Android)، والواجهات الأمامية المنفصلة (React / Next.js / Vue)، والأنظمة الإدارية والتكاملات الخارجية.

---

## 1. نظرة عامة والمعمارية (Architecture & Highlights)

- **معيار التصميم**: RESTful Architecture متوافق بالكامل مع معايير OpenAPI 3.0.3.
- **التوثيق التفاعلي الحي**: مدمج عبر `drf-spectacular` مع واجهتي **Swagger UI** و **ReDoc**.
- **المصادقة والأمان**: JWT (JSON Web Tokens) عبر `rest_framework_simplejwt` مع دعم `SessionAuthentication` و `CORS`.
- **التدويل واللغات (i18n)**: دعم كامل للغتين العربية والإنجليزية عبر ترويسة `Accept-Language: ar` أو باراميتر `?lang=ar`.
- **التحكم بالمخزون**: خصم المخزون اللحظي الآمن ذرياً (Atomic Transactions) مع استعادة المخزون التلقائية (Stock Restoration) عند إلغاء أي طلب.
- **إشعارات الطلبات**: إرسال بريد إلكتروني تلقائي للإدارة والعميل فور تأكيد الطلب.
- **الحماية من الإغراق (Rate Limiting)**: حماية نماذج التواصل والطلبات الحساسة عبر ذاكرة التخزين المؤقت (Cache).

---

## 2. الروابط التفاعلية والتوثيق (Interactive API Explorers)

| المورد | المسار (Path) | الوصف |
| :--- | :--- | :--- |
| **Swagger UI** | `/api/docs/` | واجهة تفاعلية لتجربة جميع الـ Endpoints مباشرة من المتصفح مع إمكانية إدخال JWT Bearer Token |
| **ReDoc** | `/api/redoc/` | توثيق مرئي احترافي ومرتب لجميع النماذج والـ Endpoints |
| **OpenAPI Schema** | `/api/schema/` | ملف مواصفات OpenAPI 3.0 بصيغة YAML / JSON لتوليد SDKs تلقائياً لأي لغة |

---

## 3. المصادقة وحسابات المستخدمين (Authentication & Accounts)

المسار الأساسي: `/api/v1/auth/`

### 1. تسجيل حساب جديد (Register)
- **المسار**: `POST /api/v1/auth/register/`
- **الصلاحية**: متاح للجميع (AllowAny).
- **البيانات المطلوبة**:
```json
{
  "username": "mohamed_ali",
  "email": "mohamed@example.com",
  "first_name": "محمد",
  "last_name": "علي",
  "password": "StrongPassword123!",
  "password_confirm": "StrongPassword123!"
}
```
- **الاستجابة (201 Created)**: يتم إنشاء الحساب وإرجاع بيانات المستخدم مع توكنات الدخول الفورية (`access` و `refresh`):
```json
{
  "id": 1,
  "username": "mohamed_ali",
  "email": "mohamed@example.com",
  "first_name": "محمد",
  "last_name": "علي",
  "tokens": {
    "access": "eyJhbGciOiJIUzI1NiIs...",
    "refresh": "eyJhbGciOiJIUzI1NiIs..."
  }
}
```

### 2. تسجيل الدخول والحصول على توكن (Obtain Token)
- **المسار**: `POST /api/v1/auth/token/`
- **البيانات المطلوبة**:
```json
{
  "username": "mohamed_ali",
  "password": "StrongPassword123!"
}
```
- **الاستجابة (200 OK)**:
```json
{
  "access": "eyJhbGciOiJIUzI1NiIs...",
  "refresh": "eyJhbGciOiJIUzI1NiIs..."
}
```

### 3. تجديد التوكن (Refresh Token)
- **المسار**: `POST /api/v1/auth/token/refresh/`
- **البيانات المطلوبة**:
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIs..."
}
```

### 4. الملف الشخصي (User Profile)
- **المسار**: `GET /api/v1/auth/me/` و `PATCH /api/v1/auth/me/`
- **الترويسة**: `Authorization: Bearer <access_token>`
- **الاستجابة**: بيانات الحساب الحالية وتحديثها (الاسم، البريد الإلكتروني).

### 5. تغيير كلمة المرور (Change Password)
- **المسار**: `POST /api/v1/auth/change-password/`
- **الترويسة**: `Authorization: Bearer <access_token>`
- **البيانات المطلوبة**:
```json
{
  "old_password": "OldPassword123!",
  "new_password": "NewStrongPass456!",
  "confirm_password": "NewStrongPass456!"
}
```

### 6. إدارة عناوين التوصيل (Saved Delivery Addresses)
- **المسار الأساسي**: `/api/v1/auth/addresses/` (مطلوب تسجيل الدخول)
  - `GET /api/v1/auth/addresses/`: قائمة العناوين المحفوظة للعميل.
  - `POST /api/v1/auth/addresses/`: إضافة عنوان جديد (الاسم، الهاتف، المحافظة، المدينة، تفاصيل العنوان، تعيين كافتراضي).
  - `GET /api/v1/auth/addresses/{id}/`: تفاصيل العنوان.
  - `PATCH /api/v1/auth/addresses/{id}/`: تعديل العنوان.
  - `DELETE /api/v1/auth/addresses/{id}/`: حذف العنوان.
  - `POST /api/v1/auth/addresses/{id}/set-default/`: تعيين هذا العنوان كعنوان رئيسي مفضل للطلب.

---

## 4. الكتالوج والمنتجات (Catalog & Products)

المسار الأساسي: `/api/v1/catalog/`

### 1. الأقسام والتصنيفات (Categories)
- **المسار**: `GET /api/v1/catalog/categories/`
- **الاستجابة**: قائمة التصنيفات النشطة مرتبة، مع عدد المنتجات التابعة لكل تصنيف:
```json
{
  "count": 4,
  "results": [
    {
      "id": 1,
      "name": "Wallbox Chargers",
      "name_ar": "شواحن جدارية",
      "slug": "wallbox-chargers",
      "display_name": "شواحن جدارية",
      "image": "/media/categories/wallbox.webp",
      "icon": "zap",
      "products_count": 12
    }
  ]
}
```
- **المسار**: `GET /api/v1/catalog/categories/{slug}/`: تفاصيل تصنيف معين.

### 2. قائمة المنتجات والفلترة المتقدمة (Products Listing & Filtering)
- **المسار**: `GET /api/v1/catalog/products/`
- **الفلاتر والباراميترات المتاحة**:
  - `?category=<category_slug>`: تصفية حسب القسم.
  - `?search=<keyword>`: بحث في الاسم، الاسم بالعربية، الـ SKU، والوصف.
  - `?is_featured=true`: المنتجات المميزة.
  - `?is_best_seller=true`: الأكثر مبيعاً.
  - `?is_new=true`: المنتجات الجديدة.
  - `?is_coming_soon=false`: استبعاد المنتجات قيد التجهيز.
  - `?in_stock=true`: المنتجات المتوفرة في المخزون فقط.
  - `?min_price=1000&max_price=20000`: تحديد نطاق السعر.
  - `?ordering=-created_at|price|-price|name`: ترتيب النتائج.
  - `?page=1&page_size=20`: ترقيم الصفحات والتحكم بعدد العناصر.

### 3. تفاصيل المنتج الكاملة (Product Detail)
- **المسار**: `GET /api/v1/catalog/products/{slug}/`
- **الاستجابة**: تتضمن:
  - كافة البيانات الأساسية والسعر ونسبة الخصم.
  - مواصفات المنتج الكاملة (Product Specifications + Specification Template).
  - نصوص وسياسات الضمان (Warranty Text + Template).
  - معرض الصور عالي الدقة (Product Images Gallery مع Alt texts).
  - الخيارات والمتغيرات النشطة (Variants: الأطوال، السعات، الأسعار، وحالة التوفر).
  - المنتجات ذات الصلة المقترحة (Related Products).

### 4. الإكمال التلقائي للبحث السريع (Search Autocomplete)
- **المسار**: `GET /api/v1/catalog/products/suggest/?q=شاحن`
- **الاستجابة**: قائمة سريعة وخفيفة بالمنتجات المطابقة (الاسم، السعر، الصورة، والرابط) مخصصة لحقول البحث الفوري في التطبيقات.

### 5. واجهة الصفحة الرئيسية (Homepage Showcase)
- **المسار**: `GET /api/v1/catalog/homepage/`
- **الاستجابة**: إرجاع بنر الهيرو الإعلاني النشط + المنتجات المميزة والمثبتة في الصفحة الرئيسية بطلب واحد سريع لتسريع فتح التطبيق والموقع.

---

## 5. سلة المشتريات (Shopping Cart)

المسار الأساسي: `/api/v1/cart/`

تعمل سلة المشتريات بسلاسة مع جلسات المتصفح وتطبيقات الهاتف الذكي:

| العملية | المسار (Method & Path) | البيانات المطلوبة / الوصف |
| :--- | :--- | :--- |
| **عرض السلة** | `GET /api/v1/cart/` | إرجاع عناصر السلة، السعر الإجمالي، تكلفة الشحن، والخصم المطبق |
| **إضافة عنصر** | `POST /api/v1/cart/items/` | `{"product_id": 1, "variant_id": 2, "quantity": 1}` |
| **تعديل الكمية** | `PATCH /api/v1/cart/items/{key}/` | `{"quantity": 3}` (وضع الكمية 0 يحذف العنصر) |
| **حذف عنصر** | `DELETE /api/v1/cart/items/{key}/` | حذف العنصر من السلة |
| **تطبيق كوبون خصم** | `POST /api/v1/cart/coupon/` | `{"code": "ROCKS10"}` |
| **إلغاء كوبون الخصم** | `DELETE /api/v1/cart/coupon/` | إلغاء الكوبون المطبق |
| **تفريغ السلة** | `POST /api/v1/cart/clear/` | حذف كافة العناصر والكوبونات من السلة |

---

## 6. الشحن، الدفع، وتتبع الطلبات (Shipping, Checkout & Orders)

المسار الأساسي: `/api/v1/orders/`

### 1. مناطق الشحن المتاحة والأسعار (Shipping Zones)
- **المسار**: `GET /api/v1/orders/shipping-zones/`
- **الاستجابة**: قائمة محافظات التوصيل، تكلفة الشحن لكل محافظة، وحد الشحن المجاني (Free shipping threshold).

### 2. فحص صلاحية كوبون الخصم (Validate Coupon)
- **المسار**: `POST /api/v1/orders/validate-coupon/`
- **البيانات المطلوبة**:
```json
{
  "code": "SUMMER2026",
  "subtotal": "5500.00"
}
```
- **الاستجابة**: تفاصيل صحة الكوبون وقيمة الخصم المحسوبة بدقة.

### 3. إتمام الطلب والدفع عند الاستلام (Checkout)
- **المسار**: `POST /api/v1/orders/checkout/`
- **المميزات**:
  - يدعم الشراء من السلة الحالية **أو** عبر إرسال مصفوفة المنتجات مباشرة (`items`) لتطبيقات الموبايل.
  - يدعم التوكن الفريد لمنع تكرار الطلب عن طريق الخطأ (`checkout_token` Idempotency).
  - خصم ذري فوري للكميات من المخزون لمنع تضارب الطلبات المتزامنة (Concurrency protection).
  - إطلاق إشعارات الطلب تلقائياً عبر البريد الإلكتروني.
- **نموذج الطلب**:
```json
{
  "customer_name": "أحمد إبراهيم",
  "phone": "01012345678",
  "second_phone": "01187654321",
  "email": "ahmed@example.com",
  "governorate": "Cairo",
  "city": "مدينة نصر",
  "address": "شارع النزهة، عمارة 4، الدور 3",
  "notes": "يرجى الاتصال قبل الوصول بنصف ساعة",
  "coupon_code": "SUMMER2026",
  "checkout_token": "a4d7d11e-8e65-4f40-8b17-7a2e2f392ce1",
  "items": [
    {
      "product_id": 3,
      "variant_id": 5,
      "quantity": 1
    }
  ]
}
```
- **الاستجابة (201 Created)**: إرجاع تفاصيل الطلب كاملة ورقم الطلب (`order_number`) ورمز التتبع العام (`public_token`).

### 4. تتبع الطلب بالرقم والهاتف (Order Tracking)
- **المسار**: `POST /api/v1/orders/track/`
- **البيانات المطلوبة**:
```json
{
  "order_number": "RK-261101-A1B2C3D4E5F6",
  "phone": "01012345678"
}
```
- **الاستجابة**: حالة الطلب الحالية (قيد المراجعة، مؤكد، جاري التجهيز، تم الشحن، تم التوصيل).

### 5. إيصال الطلب برمز التوكن العام (Public Order Receipt)
- **المسار**: `GET /api/v1/orders/receipt/{public_token}/`
- يتيح للعميل استعراض فاتورة وإيصال طلبه بأمان دون الحاجة لتسجيل دخول.

### 6. سجل طلبات العميل المسجل (Customer Order History)
- **المسار**: `GET /api/v1/orders/my-orders/` و `GET /api/v1/orders/my-orders/{order_number}/`
- **الترويسة**: `Authorization: Bearer <access_token>`

---

## 7. التسويق والنشرة البريدية (Marketing)

المسار الأساسي: `/api/v1/marketing/`

- **البنرات الإعلانية**: `GET /api/v1/marketing/banners/?location=hero|offer|promo`
  - ترجع البنرات النشطة والصالحة زمنياً مع نصوص الأزرار والروابط والصور للشاشات العادية والجوال.
- **الاشتراك في النشرة البريدية**: `POST /api/v1/marketing/newsletter/`
  - `{"email": "client@example.com"}`

---

## 8. إعدادات المتجر والتواصل (Core & Contact)

المسار الأساسي: `/api/v1/core/`

- **إعدادات المتجر وبيانات التواصل**: `GET /api/v1/core/settings/`
  - يرجع اسم الشركة، أرقام الهاتف وواتساب، روابط السوشيال ميديا، رسالة الشحن، والعملة (`EGP`).
- **إرسال استفسار أو رسالة تواصل**: `POST /api/v1/core/contact/`
  - بيانات الإرسال: `{"name": "...", "phone": "...", "email": "...", "subject": "...", "message": "..."}`
  - محمي بمحدد المعدل (1 رسالة كل دقيقة لكل IP).

---

## 9. إدارة المتجر ولوحة التحكم للمشرفين (Staff & Admin Management)

المسار الأساسي: `/api/v1/admin/` (يتطلب مستخدم برتبة `is_staff=True`)

### 1. مؤشرات الأداء الحية (Dashboard Metrics KPI)
- **المسار**: `GET /api/v1/admin/metrics/`
- **الاستجابة**:
  - إجمالي الطلبات موزعة حسب الحالة (جديد، مؤكد، جاري التجهيز، مشحون، مكتمل، ملغي).
  - إجمالي الإيرادات وإيرادات الشهر الجاري.
  - تنبيهات المخزون (المنتجات النافذة، والمنتجات منخفضة المخزون `<= 5`).
  - عدد رسائل التواصل غير المقروءة، وإجمالي العملاء.

### 2. إدارة طلبات العملاء (Orders Management)
- **المسار**: `GET /api/v1/admin/orders/?status=pending&search=010...`
- **تحديث حالة الطلب**: `PATCH /api/v1/admin/orders/{id}/update-status/`
  - `{"status": "delivered", "payment_status": "paid"}`
  - **ميزة حماية المخزون الذكية**: عند تحويل الطلب إلى `cancelled`، يقوم النظام تلقائياً باستدعاء `restore_order_stock` وإعادة كميات المنتجات إلى المخزون وإرجاع عداد استخدام الكوبون، مع منع إعادة فتح الطلب الملغي لحماية العمليات المحاسبية.

### 3. إدارة رسائل واستفسارات العملاء (Contact Messages)
- **المسار**: `GET /api/v1/admin/contact-messages/?is_read=false`
- **تحديد كمقروء**: `PATCH /api/v1/admin/contact-messages/{id}/set-read/` مع `{"is_read": true}`

---

## 10. إرشادات التكامل لتطبيقات الموبايل (Mobile App Integration Guide)

1. **الترويسات الموصى بها (Headers)**:
```http
Content-Type: application/json
Accept: application/json
Accept-Language: ar
Authorization: Bearer <access_token>
```
2. **التعامل مع الصور**:
كافة مسارات الصور في الـ API ترجع روابط كاملة مطلقة جاهزة للعرض الفوري في أدوات العرض مثل `CachedNetworkImage` في Flutter أو `FastImage` في React Native.
3. **التعامل مع السلة بدون تسجيل دخول (Guest Cart)**:
يمكن لتطبيق الموبايل الاحتفاظ بسلته محلياً (Local Storage / SQLite) وإرسال العناصر مباشرة إلى نقطة الدفع `/api/v1/orders/checkout/` عبر حقل `items` دون الحاجة لإنشاء جلسة ويب.

