from django.http import HttpResponseNotAllowed

def post_only(func):# pragma: no cover
    def decorated(request, *args, **kwargs):
        if request.method != 'POST':
            return HttpResponseNotAllowed(['GET'])
        return func(request, *args, **kwargs)
    return decorated

def get_only(func):# pragma: no cover
    def decorated(request, *args, **kwargs):
        if request.method != 'GET':
            return HttpResponseNotAllowed(['POST'])
        return func(request, *args, **kwargs)
    return decorated
