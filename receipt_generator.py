"""
receipt_generator.py
Generates a printable Customer KYC Card (PNG) for
Jalgaon People's Co-operative Bank.
"""

import os
import io
import datetime
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─── Colors ───
COLOR_BG         = (245, 247, 252)
COLOR_HEADER_BG  = (10, 36, 99)
COLOR_HEADER_FG  = (255, 255, 255)
COLOR_ACCENT     = (0, 102, 204)
COLOR_LABEL      = (80, 80, 120)
COLOR_TEXT       = (20, 20, 40)
COLOR_LINE       = (180, 200, 230)
COLOR_GREEN      = (0, 128, 0)

W = 900
H = 520


def load_font(size, bold=False):
    font_names = ["arialbd.ttf", "arial.ttf", "DejaVuSans-Bold.ttf",
                  "DejaVuSans.ttf", "FreeSansBold.ttf", "FreeSans.ttf"]
    bold_names = ["arialbd.ttf", "DejaVuSans-Bold.ttf", "FreeSansBold.ttf"]
    search = bold_names if bold else font_names
    dirs = [
        r"C:\Windows\Fonts",
        "/usr/share/fonts/truetype/dejavu",
        "/usr/share/fonts",
        os.path.dirname(__file__),
    ]
    for fname in search:
        for d in dirs:
            path = os.path.join(d, fname)
            if os.path.exists(path):
                try:
                    return ImageFont.truetype(path, size)
                except Exception:
                    pass
    return ImageFont.load_default()


def generate_kyc_card(customer_data: dict, photo_bytes: bytes,
                      fingerprint_bytes: bytes) -> str:
    """
    Generate KYC card PNG and save to outputs/.
    customer_data keys: full_name, mobile, loan_type,
                        loan_amount, account_number, customer_id
    Returns saved file path.
    """
    img  = Image.new("RGB", (W, H), COLOR_BG)
    draw = ImageDraw.Draw(img)

    # ── Header ──
    draw.rectangle([0, 0, W, 90], fill=COLOR_HEADER_BG)
    f_title  = load_font(22, bold=True)
    f_sub    = load_font(13)
    f_label  = load_font(12)
    f_value  = load_font(15, bold=True)
    f_small  = load_font(11)
    f_stamp  = load_font(14, bold=True)

    draw.text((W // 2, 22), "JALGAON PEOPLE'S CO-OPERATIVE BANK LTD.",
              font=f_title, fill=COLOR_HEADER_FG, anchor="mm")
    draw.text((W // 2, 58), "LOAN CUSTOMER KYC CARD",
              font=f_sub, fill=(180, 210, 255), anchor="mm")
    draw.text((W // 2, 76), "Biometric Verified",
              font=f_small, fill=(140, 180, 220), anchor="mm")

    # ── Photo ──
    photo_x, photo_y = 30, 110
    photo_w, photo_h = 160, 190

    if photo_bytes:
        try:
            photo = Image.open(io.BytesIO(photo_bytes)).convert("RGB")
            photo = photo.resize((photo_w, photo_h))
            img.paste(photo, (photo_x, photo_y))
            draw.rectangle(
                [photo_x - 2, photo_y - 2,
                 photo_x + photo_w + 2, photo_y + photo_h + 2],
                outline=COLOR_ACCENT, width=2
            )
        except Exception:
            draw.rectangle([photo_x, photo_y, photo_x + photo_w,
                            photo_y + photo_h], fill=(220, 220, 220))
            draw.text((photo_x + photo_w // 2, photo_y + photo_h // 2),
                      "No Photo", font=f_label,
                      fill=COLOR_LABEL, anchor="mm")

    # ── Customer Details ──
    details_x = 220
    details_y = 110
    line_gap  = 36

    def draw_field(label, value, y):
        draw.text((details_x, y), label + ":",
                  font=f_label, fill=COLOR_LABEL)
        draw.text((details_x, y + 16), str(value),
                  font=f_value, fill=COLOR_TEXT)
        draw.line([details_x, y + 34, details_x + 440, y + 34],
                  fill=COLOR_LINE, width=1)

    draw_field("Customer ID",
               f"JPCB-{str(customer_data.get('customer_id', '')).zfill(5)}",
               details_y)
    draw_field("Full Name",
               customer_data.get("full_name", ""),
               details_y + line_gap)
    draw_field("Mobile",
               customer_data.get("mobile", ""),
               details_y + line_gap * 2)
    draw_field("Loan Type",
               customer_data.get("loan_type", ""),
               details_y + line_gap * 3)
    draw_field("Loan Amount",
               f"Rs. {customer_data.get('loan_amount', '')}",
               details_y + line_gap * 4)

    # ── Account Number ──
    acno_x = details_x
    acno_y = details_y + line_gap * 5
    draw.text((acno_x, acno_y), "Account Number:",
              font=f_label, fill=COLOR_LABEL)
    draw.text((acno_x, acno_y + 16),
              customer_data.get("account_number", ""),
              font=f_value, fill=COLOR_TEXT)

    # ── Fingerprint ──
    fp_x, fp_y = 690, 110
    fp_w, fp_h = 160, 190

    draw.text((fp_x + fp_w // 2, fp_y - 14), "Fingerprint",
              font=f_label, fill=COLOR_LABEL, anchor="mm")

    if fingerprint_bytes:
        try:
            fp_img = Image.open(
                io.BytesIO(fingerprint_bytes)).convert("RGB")
            fp_img = fp_img.resize((fp_w, fp_h))
            img.paste(fp_img, (fp_x, fp_y))
            draw.rectangle(
                [fp_x - 2, fp_y - 2,
                 fp_x + fp_w + 2, fp_y + fp_h + 2],
                outline=COLOR_ACCENT, width=2
            )
        except Exception:
            draw.rectangle([fp_x, fp_y, fp_x + fp_w, fp_y + fp_h],
                           fill=(220, 220, 220))

    # ── Footer ──
    draw.rectangle([0, H - 70, W, H], fill=COLOR_HEADER_BG)

    enrolled = customer_data.get("enrolled_date", "")
    draw.text((30, H - 50),
              f"Enrolled: {enrolled}",
              font=f_small, fill=(180, 210, 255))

    draw.text((W // 2, H - 45),
              "BIOMETRIC KYC VERIFIED  ✓",
              font=f_stamp, fill=(100, 255, 150), anchor="mm")

    draw.text((W - 30, H - 50),
              "Authorised Signatory",
              font=f_small, fill=(180, 210, 255), anchor="ra")

    # ── Save ──
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    cid       = str(customer_data.get("customer_id", "0")).zfill(5)
    filename  = f"KYC_Card_{cid}_{timestamp}.png"
    out_path  = os.path.join(OUTPUT_DIR, filename)
    img.save(out_path, "PNG")
    print(f"[KYC Card] Saved: {out_path}")
    return out_path


# ─── Quick test ───
if __name__ == "__main__":
    test_data = {
        "customer_id"   : 1,
        "full_name"     : "Ramesh Bhimrao Patil",
        "mobile"        : "9876543210",
        "loan_type"     : "Gold Loan",
        "loan_amount"   : 150000,
        "account_number": "JPCB-2025-00042",
        "enrolled_date" : "2025-04-18",
    }
    path = generate_kyc_card(test_data, None, None)
    print("Card saved at:", path)