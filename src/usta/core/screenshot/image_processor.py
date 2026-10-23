from PIL import Image, ImageOps

class ImageProcessor:
    @staticmethod
    def preprocess_for_tesseract(image_path: str, output_path: str):
        with Image.open(image_path) as img:
            img = img.resize((img.width * 4, img.height * 4), Image.Resampling.NEAREST)
            img = ImageOps.grayscale(img)
            img = ImageOps.autocontrast(img)
            img = img.point(lambda x: 0 if x < 128 else 255, '1')
            img = ImageOps.invert(img.convert('L'))
            img = ImageOps.expand(img, border=10, fill='white')
            img.save(output_path)
