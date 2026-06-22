import hashlib
import io

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.files.base import ContentFile

from PIL import Image, ImageDraw, ImageFont

from .models import User


PALETTE = [
    (88, 101, 242),
    (72, 199, 139),
    (255, 99, 71),
    (255, 179, 71),
    (153, 102, 255),
    (60, 179, 113),
    (70, 130, 180),
    (199, 0, 57),
]

AVATAR_SIZE = 256
FONT_COLOR_LIGHT = (255, 255, 255)
FONT_COLOR_DARK = (34, 34, 34)


def _pick_color(key: str):
    if not key:
        return PALETTE[0]
    h = hashlib.sha256(key.encode("utf-8")).digest()
    idx = h[0] % len(PALETTE)
    return PALETTE[idx]


def _contrast_color(bg_color):
    # luminance
    r, g, b = bg_color
    lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return FONT_COLOR_DARK if lum > 0.5 else FONT_COLOR_LIGHT


@receiver(post_save, sender=User)
def generate_avatar_on_create(sender, instance: User, created, **kwargs):
    if not created:
        return

    if instance.avatar:
        return

    # determine letter
    name_source = (instance.name or instance.surname or instance.email or "?").strip()
    letter = name_source[0].upper() if name_source else "?"

    bg = _pick_color(instance.email or instance.username)
    fg = _contrast_color(bg)

    img = Image.new("RGB", (AVATAR_SIZE, AVATAR_SIZE), color=bg)
    draw = ImageDraw.Draw(img)

    try:
        # try to use a truetype font if available
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 120)
    except Exception:
        font = ImageFont.load_default()

    w, h = draw.textsize(letter, font=font)
    draw.text(((AVATAR_SIZE - w) / 2, (AVATAR_SIZE - h) / 2), letter, font=font, fill=fg)

    bio = io.BytesIO()
    img.save(bio, format="PNG")
    bio.seek(0)

    filename = f"users/avatars/{instance.username}_avatar.png"

    # save using default storage
    instance.avatar.save(filename, ContentFile(bio.read()), save=False)
    instance.save()
