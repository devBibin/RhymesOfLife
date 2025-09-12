from wagtail import hooks


@hooks.register('register_rich_text_features')
def enable_all_features(features):
    features.default_features.extend([
        'bold', 'italic', 'link', 'ol', 'ul', 'h2', 'h3', 'hr', 'blockquote', 'image'
    ])
