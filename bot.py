import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from database import (
    create_tables,
    save_order,
    get_orders,
    get_order,
    update_order_status,
    delete_order,
)


# =========================
# تنظیمات
# =========================

TOKEN = "8831948563:AAG9DR7N6LI3fSBRQngP5ppvf7aJWgEN3p0"
ADMIN_CHAT_ID = 287587804

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# =========================
# مراحل ثبت سفارش
# =========================

GET_NAME = 1
GET_PHONE = 2
GET_ADDRESS = 3
CONFIRM_ORDER = 4


# =========================
# محصولات
# =========================

products = {
    "bag1": {
        "name": "👜 کیف زنانه",
        "category": "bag",
        "price": 1200000,
        "description": "کیف زنانه شیک و مناسب استفاده روزمره.",
        "image": "images/bag1.jpg",
    },
    "bag2": {
        "name": "👜 کیف دوشی",
        "category": "bag",
        "price": 950000,
        "description": "کیف دوشی سبک و مناسب استفاده روزانه.",
        "image": "images/bag2.jpg",
    },
    "shoe1": {
        "name": "👟 کتانی مردانه",
        "category": "shoe",
        "price": 2300000,
        "description": "کتانی راحت و مناسب استفاده روزمره.",
        "image": "images/shoe1.jpg",
    },
    "shoe2": {
        "name": "👟 کتانی زنانه",
        "category": "shoe",
        "price": 1900000,
        "description": "کتانی اسپرت و راحت.",
        "image": "images/shoe2.jpg",
    },
}


# =========================
# توابع کمکی
# =========================

def format_price(price):
    return f"{price:,}"


def get_cart(context):
    return context.user_data.setdefault("cart", {})


def get_cart_total(context):
    cart = get_cart(context)

    return sum(
        products[product_id]["price"] * quantity
        for product_id, quantity in cart.items()
        if product_id in products
    )


def main_menu():
    keyboard = [
        [InlineKeyboardButton("🛍 محصولات", callback_data="products")],
        [InlineKeyboardButton("🛒 سبد خرید", callback_data="cart")],
        [InlineKeyboardButton("📦 ثبت سفارش", callback_data="start_order")],
        [InlineKeyboardButton("📞 پشتیبانی", callback_data="support")],
    ]

    return InlineKeyboardMarkup(keyboard)


def admin_menu():
    keyboard = [
        [
            InlineKeyboardButton(
                "🆕 سفارش‌های جدید",
                callback_data="admin_new_orders",
            )
        ],
        [
            InlineKeyboardButton(
                "📦 همه سفارش‌ها",
                callback_data="admin_all_orders",
            )
        ],
        [
            InlineKeyboardButton(
                "📊 آمار فروش",
                callback_data="admin_stats",
            )
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


def back_button(callback_data):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 بازگشت", callback_data=callback_data)]
    ])


def cart_text(context):
    cart = get_cart(context)

    if not cart:
        return "🛒 سبد خرید شما خالی است."

    text = "🛒 سبد خرید شما:\n\n"

    for product_id, quantity in cart.items():
        product = products.get(product_id)

        if not product:
            continue

        line_total = product["price"] * quantity

        text += (
            f"{product['name']}\n"
            f"تعداد: {quantity}\n"
            f"قیمت واحد: {format_price(product['price'])} تومان\n"
            f"قیمت کل: {format_price(line_total)} تومان\n\n"
        )

    text += (
        "━━━━━━━━━━━━━━\n"
        f"💰 مبلغ کل: {format_price(get_cart_total(context))} تومان"
    )

    return text


def order_products_text(context, short=False):
    cart = get_cart(context)
    text = ""

    for product_id, quantity in cart.items():
        product = products.get(product_id)

        if not product:
            continue

        line_total = product["price"] * quantity

        if short:
            text += (
                f"{product['name']} × {quantity} "
                f"= {format_price(line_total)} تومان\n"
            )
        else:
            text += (
                f"• {product['name']}\n"
                f"  تعداد: {quantity}\n"
                f"  مبلغ: {format_price(line_total)} تومان\n\n"
            )

    return text


def is_admin(user_id):
    return user_id == ADMIN_CHAT_ID


# =========================
# /start
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام 👋\n\n"
        "به فروشگاه کیف و کفش خوش آمدید.\n"
        "از منوی زیر استفاده کنید:",
        reply_markup=main_menu(),
    )


# =========================
# محصولات
# =========================

async def show_products(update, context):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [
            InlineKeyboardButton(
                "👜 کیف‌ها",
                callback_data="category_bag",
            )
        ],
        [
            InlineKeyboardButton(
                "👟 کفش‌ها",
                callback_data="category_shoe",
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 بازگشت",
                callback_data="back_main",
            )
        ],
    ]

    await query.message.edit_text(
        "🛍 دسته‌بندی محصولات:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def show_category(update, context, category):
    query = update.callback_query
    await query.answer()

    keyboard = []

    for product_id, product in products.items():
        if product["category"] == category:
            keyboard.append([
                InlineKeyboardButton(
                    product["name"],
                    callback_data=f"product_{product_id}",
                )
            ])

    keyboard.append([
        InlineKeyboardButton(
            "🔙 بازگشت",
            callback_data="products",
        )
    ])

    await query.message.edit_text(
        "محصول موردنظر را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def show_product(update, context, product_id):
    query = update.callback_query
    await query.answer()

    product = products.get(product_id)

    if not product:
        await query.message.reply_text("❌ محصول پیدا نشد.")
        return

    text = (
        f"{product['name']}\n\n"
        f"📝 {product['description']}\n\n"
        f"💰 قیمت: {format_price(product['price'])} تومان"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "➕ افزودن به سبد",
                callback_data=f"add_{product_id}",
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 بازگشت",
                callback_data=f"category_{product['category']}",
            )
        ],
    ]

    image_path = os.path.join(BASE_DIR, product["image"])

    await query.message.delete()

    if os.path.exists(image_path):
        with open(image_path, "rb") as photo:
            await query.message.chat.send_photo(
                photo=photo,
                caption=text,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
    else:
        await query.message.chat.send_message(
            "⚠️ تصویر محصول پیدا نشد.\n\n" + text,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


async def add_to_cart(update, context, product_id):
    query = update.callback_query

    if product_id not in products:
        await query.answer("❌ محصول پیدا نشد.")
        return

    cart = get_cart(context)
    cart[product_id] = cart.get(product_id, 0) + 1

    await query.answer("✅ محصول به سبد خرید اضافه شد!")


# =========================
# سبد خرید
# =========================

async def show_cart(update, context):
    query = update.callback_query
    await query.answer()

    cart = get_cart(context)

    if not cart:
        keyboard = [
            [
                InlineKeyboardButton(
                    "🛍 مشاهده محصولات",
                    callback_data="products",
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 بازگشت",
                    callback_data="back_main",
                )
            ],
        ]

        await query.message.edit_text(
            "🛒 سبد خرید شما خالی است.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    keyboard = []

    for product_id, quantity in cart.items():
        product = products.get(product_id)

        if not product:
            continue

        keyboard.append([
            InlineKeyboardButton(
                "➖",
                callback_data=f"decrease_{product_id}",
            ),
            InlineKeyboardButton(
                f"{product['name']} × {quantity}",
                callback_data="nothing",
            ),
            InlineKeyboardButton(
                "➕",
                callback_data=f"increase_{product_id}",
            ),
        ])

        keyboard.append([
            InlineKeyboardButton(
                "🗑 حذف",
                callback_data=f"remove_{product_id}",
            )
        ])

    keyboard.extend([
        [
            InlineKeyboardButton(
                "📦 ثبت سفارش",
                callback_data="start_order",
            )
        ],
        [
            InlineKeyboardButton(
                "🗑 پاک کردن سبد",
                callback_data="clear_cart",
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 بازگشت",
                callback_data="back_main",
            )
        ],
    ])

    await query.message.edit_text(
        cart_text(context),
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def increase_product(update, context, product_id):
    query = update.callback_query
    cart = get_cart(context)

    if product_id in cart:
        cart[product_id] += 1

    await query.answer()
    await show_cart(update, context)


async def decrease_product(update, context, product_id):
    query = update.callback_query
    cart = get_cart(context)

    if product_id in cart:
        cart[product_id] -= 1

        if cart[product_id] <= 0:
            del cart[product_id]

    await query.answer()
    await show_cart(update, context)


async def remove_product(update, context, product_id):
    query = update.callback_query
    cart = get_cart(context)

    cart.pop(product_id, None)

    await query.answer()
    await show_cart(update, context)


async def clear_cart(update, context):
    query = update.callback_query
    await query.answer()

    context.user_data["cart"] = {}

    await query.message.edit_text(
        "🗑 سبد خرید با موفقیت پاک شد.",
        reply_markup=main_menu(),
    )


# =========================
# ثبت سفارش
# =========================

async def start_order(update, context):
    query = update.callback_query
    await query.answer()

    if not get_cart(context):
        await query.message.edit_text(
            "🛒 سبد خرید شما خالی است.\n\n"
            "ابتدا یک محصول به سبد خرید اضافه کنید.",
            reply_markup=main_menu(),
        )
        return ConversationHandler.END

    await query.message.edit_text(
        "👤 لطفاً نام و نام خانوادگی خود را وارد کنید:"
    )

    return GET_NAME


async def get_name(update, context):
    context.user_data["name"] = update.message.text.strip()

    await update.message.reply_text(
        "📞 لطفاً شماره تلفن خود را وارد کنید:"
    )

    return GET_PHONE


async def get_phone(update, context):
    context.user_data["phone"] = update.message.text.strip()

    await update.message.reply_text(
        "📍 لطفاً آدرس کامل خود را وارد کنید:"
    )

    return GET_ADDRESS


async def get_address(update, context):
    context.user_data["address"] = update.message.text.strip()

    if not get_cart(context):
        await update.message.reply_text(
            "🛒 سبد خرید شما خالی است."
        )
        return ConversationHandler.END

    name = context.user_data["name"]
    phone = context.user_data["phone"]
    address = context.user_data["address"]
    total = get_cart_total(context)

    text = (
        "📋 لطفاً اطلاعات سفارش را بررسی کنید:\n\n"
        f"👤 نام: {name}\n"
        f"📞 تلفن: {phone}\n"
        f"📍 آدرس: {address}\n\n"
        "🛍 محصولات:\n"
        f"{order_products_text(context)}"
        f"💰 مبلغ کل: {format_price(total)} تومان\n\n"
        "آیا اطلاعات صحیح است؟"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "➡️ ادامه و انتخاب پرداخت",
                callback_data="choose_payment",
            )
        ],
        [
            InlineKeyboardButton(
                "❌ لغو سفارش",
                callback_data="cancel_order",
            )
        ],
    ]

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return CONFIRM_ORDER


async def choose_payment(update, context):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [
            InlineKeyboardButton(
                "💵 پرداخت در محل",
                callback_data="payment_cash",
            )
        ],
        [
            InlineKeyboardButton(
                "💳 پرداخت آنلاین",
                callback_data="payment_online",
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 بازگشت",
                callback_data="back_to_cart",
            )
        ],
    ]

    await query.message.edit_text(
        "💳 روش پرداخت را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return CONFIRM_ORDER


async def payment_online(update, context):
    query = update.callback_query
    await query.answer()

    total = get_cart_total(context)

    keyboard = [
        [
            InlineKeyboardButton(
                "🔙 بازگشت به پرداخت",
                callback_data="choose_payment",
            )
        ]
    ]

    await query.message.edit_text(
        "💳 پرداخت آنلاین\n\n"
        f"💰 مبلغ سفارش: {format_price(total)} تومان\n\n"
        "🔗 درگاه پرداخت در مرحله بعد به ربات متصل می‌شود.",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return CONFIRM_ORDER


async def register_cash_order(update, context):
    query = update.callback_query
    await query.answer()

    cart = get_cart(context)

    if not cart:
        await query.message.edit_text(
            "🛒 سبد خرید شما خالی است.",
            reply_markup=main_menu(),
        )
        return ConversationHandler.END

    name = context.user_data.get("name", "")
    phone = context.user_data.get("phone", "")
    address = context.user_data.get("address", "")
    total = get_cart_total(context)
    products_text = order_products_text(context, short=True)

    order_id = save_order(
        name,
        phone,
        address,
        products_text,
        total,
    )

    admin_text = (
        f"🆕 سفارش جدید #{order_id}\n\n"
        f"👤 نام: {name}\n"
        f"📞 تلفن: {phone}\n"
        f"📍 آدرس: {address}\n\n"
        f"🛍 محصولات:\n{products_text}\n"
        f"💰 مبلغ کل: {format_price(total)} تومان\n"
        "💵 روش پرداخت: پرداخت در محل"
    )

    try:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=admin_text,
        )
    except Exception:
        pass

    context.user_data.clear()

    await query.message.edit_text(
        f"✅ سفارش شما با موفقیت ثبت شد!\n\n"
        f"🧾 شماره سفارش: #{order_id}\n"
        f"💰 مبلغ: {format_price(total)} تومان\n"
        "💵 روش پرداخت: پرداخت در محل\n\n"
        "📦 سفارش شما در حال بررسی است.",
        reply_markup=main_menu(),
    )

    return ConversationHandler.END


async def cancel_order(update, context):
    query = update.callback_query
    await query.answer()

    context.user_data.clear()

    await query.message.edit_text(
        "❌ سفارش لغو شد.",
        reply_markup=main_menu(),
    )

    return ConversationHandler.END


async def back_to_cart(update, context):
    await show_cart(update, context)
    return ConversationHandler.END


# =========================
# پشتیبانی
# =========================

async def support(update, context):
    query = update.callback_query
    await query.answer()

    await query.message.edit_text(
        "📞 پشتیبانی\n\n"
        "برای ارتباط با پشتیبانی با ادمین فروشگاه تماس بگیرید.",
        reply_markup=back_button("back_main"),
    )


# =========================
# پنل ادمین
# =========================

async def admin(update, context):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ دسترسی غیرمجاز.")
        return

    await update.message.reply_text(
        "🔐 پنل مدیریت فروشگاه",
        reply_markup=admin_menu(),
    )


async def admin_new_orders(update, context):
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.message.edit_text("⛔ دسترسی غیرمجاز.")
        return

    orders = [
        order
        for order in get_orders()
        if order[6] == "جدید"
    ]

    if not orders:
        await query.message.edit_text(
            "📭 در حال حاضر سفارش جدیدی وجود ندارد.",
            reply_markup=back_button("admin_back"),
        )
        return

    keyboard = []

    for order in orders:
        keyboard.append([
            InlineKeyboardButton(
                f"🧾 #{order[0]} | {order[1]} | "
                f"{format_price(order[5])} تومان",
                callback_data=f"admin_order_{order[0]}",
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "🔙 بازگشت",
            callback_data="admin_back",
        )
    ])

    await query.message.edit_text(
        "🆕 سفارش‌های جدید:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def admin_all_orders(update, context):
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.message.edit_text("⛔ دسترسی غیرمجاز.")
        return

    orders = get_orders()

    if not orders:
        await query.message.edit_text(
            "📭 هنوز سفارشی ثبت نشده است.",
            reply_markup=back_button("admin_back"),
        )
        return

    keyboard = []

    for order in orders:
        keyboard.append([
            InlineKeyboardButton(
                f"#{order[0]} | {order[1]} | {order[6]}",
                callback_data=f"admin_order_{order[0]}",
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "🔙 بازگشت",
            callback_data="admin_back",
        )
    ])

    await query.message.edit_text(
        "📦 همه سفارش‌ها:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def admin_order_details(update, context, order_id):
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.message.edit_text("⛔ دسترسی غیرمجاز.")
        return

    order = get_order(order_id)

    if not order:
        await query.message.edit_text("❌ سفارش پیدا نشد.")
        return

    (
        order_id,
        name,
        phone,
        address,
        order_products,
        total,
        status,
        created_at,
    ) = order

    text = (
        f"🧾 سفارش #{order_id}\n\n"
        f"👤 نام: {name}\n"
        f"📞 تلفن: {phone}\n"
        f"📍 آدرس: {address}\n\n"
        f"🛍 محصولات:\n{order_products}\n"
        f"💰 مبلغ: {format_price(total)} تومان\n"
        f"📌 وضعیت: {status}\n"
        f"🕐 تاریخ: {created_at}"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "✅ تأیید سفارش",
                callback_data=f"approve_order_{order_id}",
            ),
            InlineKeyboardButton(
                "❌ رد سفارش",
                callback_data=f"reject_order_{order_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                "🗑 حذف سفارش",
                callback_data=f"delete_order_{order_id}",
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 بازگشت",
                callback_data="admin_new_orders",
            )
        ],
    ]

    await query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def admin_stats(update, context):
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.message.edit_text("⛔ دسترسی غیرمجاز.")
        return

    orders = get_orders()

    approved_orders = [
        order
        for order in orders
        if order[6] == "تأیید شده"
    ]

    total_sales = sum(
        order[5]
        for order in approved_orders
    )

    text = (
        "📊 آمار فروشگاه\n\n"
        f"📦 تعداد کل سفارش‌ها: {len(orders)}\n"
        f"✅ سفارش‌های تأییدشده: {len(approved_orders)}\n"
        f"💰 مجموع فروش: {format_price(total_sales)} تومان"
    )

    await query.message.edit_text(
        text,
        reply_markup=back_button("admin_back"),
    )


# =========================
# Chat ID
# =========================

async def my_id(update, context):
    await update.message.reply_text(
        f"🆔 Chat ID شما:\n\n{update.effective_user.id}"
    )


# =========================
# مدیریت دکمه‌ها
# =========================

async def button_handler(update, context):
    query = update.callback_query
    data = query.data

    if data == "products":
        await show_products(update, context)

    elif data == "category_bag":
        await show_category(update, context, "bag")

    elif data == "category_shoe":
        await show_category(update, context, "shoe")

    elif data.startswith("product_"):
        await show_product(
            update,
            context,
            data.replace("product_", "", 1),
        )

    elif data.startswith("add_"):
        await add_to_cart(
            update,
            context,
            data.replace("add_", "", 1),
        )

    elif data == "cart":
        await show_cart(update, context)

    elif data.startswith("increase_"):
        await increase_product(
            update,
            context,
            data.replace("increase_", "", 1),
        )

    elif data.startswith("decrease_"):
        await decrease_product(
            update,
            context,
            data.replace("decrease_", "", 1),
        )

    elif data.startswith("remove_"):
        await remove_product(
            update,
            context,
            data.replace("remove_", "", 1),
        )

    elif data == "clear_cart":
        await clear_cart(update, context)

    elif data == "support":
        await support(update, context)

    elif data == "back_main":
        await query.answer()
        await query.message.edit_text(
            "🏠 منوی اصلی:",
            reply_markup=main_menu(),
        )

    elif data == "admin_new_orders":
        await admin_new_orders(update, context)

    elif data == "admin_all_orders":
        await admin_all_orders(update, context)

    elif data == "admin_stats":
        await admin_stats(update, context)

    elif data == "admin_back":
        await query.answer()
        await query.message.edit_text(
            "🔐 پنل مدیریت فروشگاه",
            reply_markup=admin_menu(),
        )

    elif data.startswith("admin_order_"):
        order_id = int(
            data.replace("admin_order_", "", 1)
        )

        await admin_order_details(
            update,
            context,
            order_id,
        )

    elif data.startswith("approve_order_"):
        await query.answer()

        if not is_admin(query.from_user.id):
            await query.message.edit_text("⛔ دسترسی غیرمجاز.")
            return

        order_id = int(
            data.replace("approve_order_", "", 1)
        )

        update_order_status(
            order_id,
            "تأیید شده",
        )

        await query.message.edit_text(
            f"✅ سفارش #{order_id} تأیید شد.",
            reply_markup=admin_menu(),
        )

    elif data.startswith("reject_order_"):
        await query.answer()

        if not is_admin(query.from_user.id):
            await query.message.edit_text("⛔ دسترسی غیرمجاز.")
            return

        order_id = int(
            data.replace("reject_order_", "", 1)
        )

        update_order_status(
            order_id,
            "رد شده",
        )

        await query.message.edit_text(
            f"❌ سفارش #{order_id} رد شد.",
            reply_markup=admin_menu(),
        )

    elif data.startswith("delete_order_"):
        await query.answer()

        if not is_admin(query.from_user.id):
            await query.message.edit_text("⛔ دسترسی غیرمجاز.")
            return

        order_id = int(
            data.replace("delete_order_", "", 1)
        )

        delete_order(order_id)

        await query.message.edit_text(
            f"🗑 سفارش #{order_id} حذف شد.",
            reply_markup=admin_menu(),
        )

    elif data == "nothing":
        await query.answer()


# =========================
# اجرای ربات
# =========================

def main():
    create_tables()

    app = Application.builder().token(TOKEN).build()

    order_conversation = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                start_order,
                pattern="^start_order$",
            )
        ],
        states={
            GET_NAME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_name,
                )
            ],
            GET_PHONE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_phone,
                )
            ],
            GET_ADDRESS: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_address,
                )
            ],
            CONFIRM_ORDER: [
                CallbackQueryHandler(
                    choose_payment,
                    pattern="^choose_payment$",
                ),
                CallbackQueryHandler(
                    register_cash_order,
                    pattern="^payment_cash$",
                ),
                CallbackQueryHandler(
                    payment_online,
                    pattern="^payment_online$",
                ),
                CallbackQueryHandler(
                    cancel_order,
                    pattern="^cancel_order$",
                ),
                CallbackQueryHandler(
                    back_to_cart,
                    pattern="^back_to_cart$",
                ),
            ],
        },
        fallbacks=[
            CommandHandler("start", start),
        ],
        per_message=False,
    )

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("myid", my_id)
    )

    app.add_handler(
        CommandHandler("admin", admin)
    )

    app.add_handler(order_conversation)

    app.add_handler(
        CallbackQueryHandler(button_handler)
    )

    print("ربات آماده است...")
    app.run_polling()


if __name__ == "__main__":
    main()