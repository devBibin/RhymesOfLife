from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock


class ImageWithCaptionBlock(blocks.StructBlock):
    image = ImageChooserBlock()
    caption = blocks.CharBlock(required=False, max_length=250, label="Подпись к изображению")

    class Meta:
        icon = "image"
        label = "Изображение с подписью"
        template = "blog/blocks/image_with_caption.html"
