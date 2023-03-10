from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    """Custom pagination class with reassigned page_size_query_param."""
    page_size_query_param = 'limit'
