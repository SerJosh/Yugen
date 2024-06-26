from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from .models import Product, Category, Review
from django.db.models.functions import Lower
from .forms import ProductForm
from django.contrib.auth.decorators import login_required
from .forms import NewReviewForm
from django.http import HttpResponseRedirect

# Create your views here.


def all_products(request):
    """view to show all products, including sorting and search queries"""

    products = Product.objects.all()
    query = None
    categories = None
    sort = None
    direction = None

    if request.GET:
        if 'sort' in request.GET:
            sortkey = request.GET['sort']
            sort = sortkey
            if sortkey == 'name':
                sortkey = 'lower_name'
                products = products.annotate(lower_name=Lower('name'))
            if sortkey == 'category':
                sortkey = 'category__name'
            if 'direction' in request.GET:
                direction = request.GET['direction']
                if direction == 'desc':
                    sortkey = f'-{sortkey}'
            products = products.order_by(sortkey)

        if 'category' in request.GET:
            categories = request.GET['category'].split(',')
            products = products.filter(category__name__in=categories)
            categories = Category.objects.filter(name__in=categories)

    if request.GET:
        if 'q' in request.GET:
            query = request.GET['q']
            if not query:
                messages.error(request, "You didn't enter any criteria!")
                return redirect(reverse('products'))

            queries = Q(name__icontains=query
                        ) | Q(description__icontains=query)
            products = products.filter(queries)

    current_sorting = f'{sort}_{direction}'

    context = {
        'products': products,
        'search_term': query,
        'current_categories': categories,
        'current_sorting': current_sorting,
    }

    return render(request, 'pictures/pictures.html', context)


def product_detail(request, product_id):
    """ A view to show individual product details and reviews """

    product = get_object_or_404(Product, pk=product_id)
    fav = bool

    queryset = Product.objects
    product = get_object_or_404(queryset, pk=product_id)
    reviews = product.reviews.all()
    review_count = product.reviews.count()

    if product.favourites.filter(id=request.user.id).exists():
        fav = True

    if request.method == "POST":
        review_form = NewReviewForm(data=request.POST)
        if review_form.is_valid():
            review = review_form.save(commit=False)
            review.name = request.user
            review.product = product
            review.save()
            messages.add_message(
                request, messages.SUCCESS,
                'Review submitted!'
            )

    review_form = NewReviewForm()

    context = {
        'product': product,
        'fav': fav,
        "product": product,
        "reviews": reviews,
        "review_count": review_count,
        "review_form": review_form,
    }

    return render(request, 'pictures/pictures_detail.html', context)


def delete_review(request, review_id):
    """ A view to delete reviews """
    review_delete = Review.objects.get(pk=review_id)
    review_delete.delete()
    return HttpResponseRedirect(request.META['HTTP_REFERER'])


@login_required
def add_product(request):
    """ Add a product to the store """
    if not request.user.is_superuser:
        messages.error(request, 'Sorry, only store owners can do that.')
        return redirect(reverse('home'))

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            messages.success(request, 'Successfully added product!')
            return redirect(reverse('product_detail', args=[product.id]))
        else:
            messages.error(request, 'Failed. Please ensure the form is valid.')
    else:
        form = ProductForm()

    template = 'pictures/add_pictures.html'
    context = {
        'form': form,
    }

    return render(request, template, context)


@login_required
def edit_product(request, product_id):
    """ Edit a product in the store """
    if not request.user.is_superuser:
        messages.error(request, 'Sorry, only store owners can do that.')
        return redirect(reverse('home'))

    product = get_object_or_404(Product, pk=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Successfully updated product!')
            return redirect(reverse('product_detail', args=[product.id]))
        else:
            messages.error(request, 'Failed. Please ensure the form is valid.')
    else:
        form = ProductForm(instance=product)
        messages.info(request, f'You are editing {product.name}')

    template = 'pictures/edit_pictures.html'
    context = {
        'form': form,
        'product': product,
    }

    return render(request, template, context)


@login_required
def delete_product(request, product_id):
    """ Delete a product from the store """
    if not request.user.is_superuser:
        messages.error(request, 'Sorry, only store owners can do that.')
        return redirect(reverse('home'))
    product = get_object_or_404(Product, pk=product_id)
    product.delete()
    messages.success(request, 'Product deleted!')
    return redirect(reverse('products'))


def review_detail(request, product_id):

    queryset = Product.objects
    product = get_object_or_404(queryset, pk=product_id)
    reviews = product.reviews.all()
    review_count = product.reviews.count()
    if request.method == "POST":
        review_form = NewReviewForm(data=request.POST)
        if review_form.is_valid():
            review = review_form.save(commit=False)
            review.name = request.user
            review.product = product
            review.save()
            messages.add_message(
                request, messages.SUCCESS,
                'Comment submitted and awaiting approval'
            )

    review_form = NewReviewForm()

    context = {
            "product": product,
            "reviews": reviews,
            "review_count": review_count,
            "review_form": review_form
    }

    return render(
        request,
        "pictures/pictures_detail.html", context)
