from .models import Category
from django.db.models import Count, Q

def get_categories(request):
    categories = list(
        Category.objects.annotate(
            posts_count=Count('posts', filter=Q(posts__status='published'))
        ).order_by('id') 
    )
    main_categories = categories[:5]    
    dropdown_categories = categories[5:] 

    all_categories = main_categories + dropdown_categories

    return {
        'main_categories': main_categories,
        'dropdown_categories': dropdown_categories,
        'all_categories': all_categories,
    }
