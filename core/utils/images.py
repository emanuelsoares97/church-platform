from io import BytesIO

from PIL import Image, ImageOps
from django.core.files.uploadedfile import InMemoryUploadedFile


MAX_WIDTH = 2000
JPEG_QUALITY = 85
MAX_FILE_SIZE_MB = 10


def optimize_uploaded_image(uploaded_file):
    """
    Otimiza imagens enviadas pelos utilizadores.

    Faz:
    - correção de rotação com base no EXIF
    - conversão para RGB
    - redimensionamento proporcional
    - compressão em JPEG

    Retorna um novo ficheiro em memória, pronto para guardar.
    """
    image = Image.open(uploaded_file)

    # Corrige rotação automática de imagens vindas do telemóvel
    image = ImageOps.exif_transpose(image)

    # Converte para RGB se necessário
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    elif image.mode != "RGB":
        image = image.convert("RGB")

    # Redimensiona se exceder a largura máxima
    if image.width > MAX_WIDTH:
        ratio = MAX_WIDTH / float(image.width)
        height = int(image.height * ratio)
        image = image.resize((MAX_WIDTH, height), Image.LANCZOS)

    output = BytesIO()

    image.save(
        output,
        format="JPEG",
        quality=JPEG_QUALITY,
        optimize=True,
    )

    output.seek(0)

    size_mb = output.getbuffer().nbytes / (1024 * 1024)

    if size_mb > MAX_FILE_SIZE_MB:
        raise ValueError("Imagem demasiado grande após otimização.")

    # Força extensão jpg para coerência
    original_name = uploaded_file.name.rsplit(".", 1)[0]
    new_name = f"{original_name}.jpg"

    return InMemoryUploadedFile(
        output,
        "ImageField",
        new_name,
        "image/jpeg",
        output.getbuffer().nbytes,
        None,
    )