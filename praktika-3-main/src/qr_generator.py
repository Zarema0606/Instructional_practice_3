import qrcode

FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSdhZcExx6LSIXxk0ub55mSu-WIh23WYdGG9HY5EZhLDo7P8eA/viewform"

def generate_qr(path="quality_qr.png"):
    img = qrcode.make(FORM_URL)
    img.save(path)
